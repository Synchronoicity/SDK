class FailedToGetLatestChanges(Exception):
    pass


class InvalidCredentials(FailedToGetLatestChanges):
    pass


class RequestFailed(Exception):
    def __init__(self, errors):
        self.errors = errors