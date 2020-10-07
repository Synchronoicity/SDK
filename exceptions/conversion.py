class FailedToConvert(Exception):
    def __init__(self, reason):
        self.reason = reason


class UserDoesntExist(FailedToConvert):
    pass


class IgnoreChange(Exception):
    pass