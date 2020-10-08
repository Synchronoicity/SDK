import mongoengine
import requests
from werkzeug.security import check_password_hash, generate_password_hash

import sdk
from . import datetimeProvider


class User(mongoengine.Document):
    email = mongoengine.EmailField(required=True)
    passwordHash = mongoengine.StringField()

    nextPoll = mongoengine.DateTimeField(required=True, default=datetimeProvider.get_current_time)
    pollingFrequency = mongoengine.IntField(required=True, default=20)

    syncEnabled = mongoengine.BooleanField(required=True, default=True)

    @property
    def platformRegistrations(self):
        return UserPlatformRegistration.objects(user=self, active=True).all()

    def setPassword(self, password) -> None:
        self.passwordHash = generate_password_hash(password)

    def checkPassword(self, password) -> bool:
        return check_password_hash(self.passwordHash, password)

    @classmethod
    def new(cls, email, password):
        newUser = cls(
            email=email,
        )
        newUser.setPassword(password)
        newUser.save()
        PollingSliceUserAssignment(
            user=newUser,
            slice=None
        ).save()
        return newUser


class UserSession(mongoengine.Document):
    user = mongoengine.ReferenceField(User, required=True)
    timeStarted = mongoengine.DateTimeField(required=True, default=datetimeProvider.get_current_time)
    expiryTime = mongoengine.DateTimeField(required=True, default=datetimeProvider.hours_in_future(2))

# Platform & Product Stores


class PlatformRegistration(mongoengine.Document):
    platformIdentifier = mongoengine.StringField(required=True, unique=True)
    active = mongoengine.BooleanField(required=True, default=True)


class ProductRegistration(mongoengine.Document):
    user = mongoengine.ReferenceField(User, required=True)
    productSKU = mongoengine.StringField(required=True)
    syncEnabled = mongoengine.BooleanField(required=True, default=True)


class UserPlatformRegistration(mongoengine.Document):
    user = mongoengine.ReferenceField(User, required=True)
    platform = mongoengine.ReferenceField(PlatformRegistration, required=True)

    active = mongoengine.BooleanField(required=True, default=True)

    credentials = mongoengine.DictField(required=True, default=dict)


class ProductPlatformLink(mongoengine.Document):
    user = mongoengine.ReferenceField(User, required=True)
    platformReg = mongoengine.ReferenceField(PlatformRegistration, required=True)
    productReg = mongoengine.ReferenceField(ProductRegistration, required=True)

    syncEnabled = mongoengine.BooleanField(required=True, default=True)
    stillExists = mongoengine.BooleanField(required=True, default=True)


class PlatformIDSKUIndexRecord(mongoengine.Document):
    user = mongoengine.ReferenceField(User, required=True)
    productSKU = mongoengine.StringField(required=True)
    indexData = mongoengine.DictField(required=True, default=dict)


class PlatformUserPolledChangesRecord(mongoengine.Document):
    timePolled = mongoengine.DateTimeField(required=True, default=datetimeProvider.get_current_time)
    target = mongoengine.ReferenceField(UserPlatformRegistration, required=True)


# Stock Management Models
class ProductStockRecord(mongoengine.Document):
    product = mongoengine.ReferenceField(ProductRegistration, required=True)
    value = mongoengine.DecimalField(required=True)


class StockTransaction(mongoengine.Document):
    origin = mongoengine.ReferenceField(ProductPlatformLink, required=True)
    originChangeID = mongoengine.StringField(required=True)
    locked = mongoengine.BooleanField(required=True, default=False)
    state = mongoengine.StringField(required=True, default="pending")  # pending, failed, applied, ignored
    timeOccurred = mongoengine.DateTimeField(required=True, default=datetimeProvider.get_current_time)


class StockAction(mongoengine.Document):
    transaction = mongoengine.ReferenceField(StockTransaction, required=True)
    target = mongoengine.ReferenceField(ProductPlatformLink, required=True)
    action = mongoengine.StringField(required=True)  # change, set
    state = mongoengine.StringField(required=True, default="pending")  # pending, failed, applied, nulled (not applied, but not failed, to be ignored)
    value = mongoengine.DecimalField(required=True)

# Consistency Models


class InconsistencyRecord(mongoengine.Document):
    product = mongoengine.ReferenceField(ProductRegistration, required=True)
    timeNoticed = mongoengine.DateTimeField(required=True, default=datetimeProvider.get_current_time)


class InconsistencyStockCount(mongoengine.Document):
    record = mongoengine.ReferenceField(InconsistencyRecord, required=True)
    source = mongoengine.ReferenceField(ProductPlatformLink, required=True)
    value = mongoengine.DecimalField(required=True)


class InconsistencyCase(mongoengine.Document):
    record = mongoengine.ReferenceField(InconsistencyRecord, required=True)
    state = mongoengine.StringField(required=True, default="unresolved") # unresolved, error, resolved


class ChangeProcessor(mongoengine.Document):
    live = mongoengine.BooleanField(default=True)
    lastHeartbeat = mongoengine.DateTimeField(required=True, default=datetimeProvider.get_current_time)
    heartbeatSecret = mongoengine.StringField(required=True)
    connectionString = mongoengine.StringField(required=True)

    def allocate_queues(self, listOfQueueIDs):
        requests.post(f"{self.connectionString}allocate_queues", json=listOfQueueIDs)


class ProcessingSlice(mongoengine.Document):
    processor = mongoengine.ReferenceField(ChangeProcessor)
    usersAllocated = mongoengine.IntField(required=True, default=0)

    def allocate_users(self, listOfUsers):
        user: sdk.dbModels.User
        for user in listOfUsers:
            self.usersAllocated += 1
            self.save()
            ProcessingSliceUserAssignment(
                slice=self,
                user=user
            ).save()
        try:
            self.processor.allocate_queues([str(user.id) for user in listOfUsers])
        except requests.RequestException:
            self.processor.live = False
            self.processor.save()
            # TODO: Write more failover here.
            print("Failed to communicate with processor.")


class ProcessingSliceUserAssignment(mongoengine.Document):
    slice = mongoengine.ReferenceField(ProcessingSlice, required=True)
    user = mongoengine.ReferenceField(User, required=True)


class ChangePoller(mongoengine.Document):
    live = mongoengine.BooleanField(default=True)
    lastHeartbeat = mongoengine.DateTimeField(required=True, default=datetimeProvider.get_current_time)
    heartbeatSecret = mongoengine.StringField(required=True)
    connectionString = mongoengine.StringField(required=True)

    def allocate_users(self, listOfUserPollingJSON):
        print(listOfUserPollingJSON)


class PollingSlice(mongoengine.Document):
    poller = mongoengine.ReferenceField(ChangePoller, required=True)
    usersAllocated = mongoengine.IntField(required=True, default=0)

    def allocateUsers(self, listOfUsers):
        user: sdk.dbModels.User
        for user in listOfUsers:
            self.usersAllocated += 1
            self.save()
            PollingSliceUserAssignment(
                user=user,
                slice=self
            ).save()
        self.poller.allocate_users([generate_user_polling_json(user) for user in listOfUsers])


class PollingSliceUserAssignment(mongoengine.Document):
    user = mongoengine.ReferenceField(User, required=True)
    slice = mongoengine.ReferenceField(PollingSlice)


def generate_user_polling_json(userObject):
    return {
        "id": str(userObject.id),
        "platforms": [
            {
                "identifier": platformReg.platform.platformIdentifier,
                "credentials": platformReg.credentials
            } for platformReg in userObject.platformRegistrations if platformReg.active
        ]
    }