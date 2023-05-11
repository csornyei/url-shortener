import os
import redis

DAY = 24 * 60 * 60

class Cache:
    def __init__(self):
        self.client = redis.Redis(host=os.getenv("REDIS_HOST"),
                                  port=os.getenv("REDIS_PORT"))

    def cache_url(self, shortcode: str, url: str):
        self.client.set(shortcode, url)
        self.client.expire(shortcode, DAY)

    def extend_url(self, shortcode: str):
        self.client.expire(shortcode, DAY)

    def retrieve_url(self, shortcode: str):
        return self.client.get(shortcode)

client = redis.Redis(host=os.getenv("REDIS_HOST"),
                     port=os.getenv("REDIS_PORT"))



