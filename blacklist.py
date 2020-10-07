from redis import Redis


class BlacklistClient:
    def __init__(self, *args, **kwargs):
        self.redisClient = Redis(*args, decode_responses=True, **kwargs)

    def isBlacklisted(self, platformIdentifier, userID, value):
        if value is None:
            return False
        setKey = f"{platformIdentifier}/{userID}/blacklist"
        return self.redisClient.sismember(setKey, value)

    def addToBlacklist(self, platformIdentifier, userID, value):
        setKey = f"{platformIdentifier}/{userID}/blacklist"
        return self.redisClient.sadd(setKey, value)

    def delFromBlacklist(self, platformIdentifier, userID, value):
        setKey = f"{platformIdentifier}/{userID}/blacklist"
        return self.redisClient.srem(setKey, value)
