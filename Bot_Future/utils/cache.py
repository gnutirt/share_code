import time

class Cache:
    def __init__(self, expiry=5):
        self.data = {}
        self.expiry = expiry

    def set(self, key, value):
        self.data[key] = (value, time.time())

    def get(self, key):
        if key in self.data:
            value, timestamp = self.data[key]
            if time.time() - timestamp < self.expiry:
                return value
        return None
