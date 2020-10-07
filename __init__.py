from . import exceptions, datetimeProvider, dbModels, interfaces, blacklist, numbers, batchHandling, logging, queue
from mongoengine import connect


def connect_db(*args, **kwargs):
    connect(*args, **kwargs)


def registerPlatform(persistentIdentifier):
    platformRecord = dbModels.PlatformRegistration.objects(platformIdentifier=persistentIdentifier).first()
    if platformRecord is None:
        platformRecord = dbModels.PlatformRegistration(platformIdentifier=persistentIdentifier)
        platformRecord.save()
    else:
        platformRecord.active = True
        platformRecord.save()
    return platformRecord
