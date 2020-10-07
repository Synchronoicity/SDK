from . import requests, indexing, conversion, retry


class ProductDoesntExistOnTargetPlatform(Exception):
    pass

class MultipleInstancesOfProductOnTargetPlatform(Exception):
    pass