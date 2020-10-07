from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from .dbModels import ProductPlatformLink, PlatformRegistration, User, ProductRegistration
from .exceptions.conversion import FailedToConvert, UserDoesntExist, IgnoreChange
from .datetimeProvider import to_rfc3339_string, from_rfc3339_string
import simplejson


@dataclass
class SentPlatformStockChange:
    target: ProductPlatformLink
    action: str  # set, change
    value: Decimal
    timeInitiated: datetime


@dataclass
class ReceivedPlatformStockChange:
    source: ProductPlatformLink
    action: str  # set, change
    value: Decimal
    timeInitiated: datetime
    sourceChangeID: str

    # Quite the expensive conversion!
    @classmethod
    def from_dict(cls, changeDict):
        sourcePlatformIdentifier = changeDict.get("sourcePlatformIdentifier")
        sourcePlatformRegistration = PlatformRegistration.objects(platformIdentifier=sourcePlatformIdentifier).first()
        if sourcePlatformRegistration is None:
            raise FailedToConvert("Change sourcePlatformIdentifier didn't match any databased sources!")

        productOwnerID = changeDict.get("productOwnerID")
        productOwner = User.objects(id=productOwnerID).first()
        if productOwner is None:
            raise UserDoesntExist("Change productOwnerID didn't match any databased users! Maybe the user was deleted??")

        productSKU = changeDict.get("productSKU")
        productRegistration = ProductRegistration.objects(user=productOwner, productSKU=productSKU).first()
        if not productRegistration.syncEnabled:
            raise IgnoreChange
        if productRegistration is None:
            productRegistration = ProductRegistration(
                user=productOwner,
                productSKU=productSKU
            )
            productRegistration.save()

        productPlatformLink = ProductPlatformLink.objects(
            user=productOwner,
            platformReg=sourcePlatformRegistration,
            productReg=productRegistration,
            stillExists=True
        ).first()
        if not productPlatformLink.syncEnabled:
            raise IgnoreChange

        if productPlatformLink is None:
            productPlatformLink = ProductPlatformLink(
                user=productOwner,
                platformReg=sourcePlatformRegistration,
                productReg=productRegistration,
                stillExists=True
            )
            productPlatformLink.save()

        timeInitiated = from_rfc3339_string(changeDict.get("timeInitiated"))

        return cls(
            source=productPlatformLink,
            action=changeDict.get("action"),
            value=changeDict.get("value"),
            timeInitiated=timeInitiated,
            sourceChangeID=changeDict.get("sourceChangeID")
        )


@dataclass
class StockCount:
    source: ProductPlatformLink
    value: Decimal
