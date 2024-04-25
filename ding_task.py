import redis

database_redis = {
    'host': '103.242.3.43',  # 公网
    'port': 6379,
    'user': 'root',
    'password': 'jhkdjhkjdhsIUTYURTU_Bdn7Sw',
    'db': '2'
}

Pool = redis.ConnectionPool(host=database_redis['host'],
                            port=database_redis['port'],
                            password=database_redis['password'],
                            decode_responses=True,
                            db=database_redis['db'])


class RedisDB:

    def __init__(self, key):  # key为表名

        self.conn = redis.Redis(connection_pool=Pool, decode_responses=True)
        self.key = key

    # 设置过期时间
    def set_ExpiredTime(self, time):
        self.conn.expire(self.key, time)


class RedisList(RedisDB):

    def __init__(self, key):  # key为表名
        super(RedisList, self).__init__(key)

    def InsertData(self, *value, lpush=False):
        return self.conn.lpush(self.key, *value) if lpush else self.conn.rpush(self.key, *value)

    def llen(self):
        return self.conn.llen(self.key)

    def DeletePop(self, lpop=False):
        return self.conn.lpop(self.key) if lpop else self.conn.rpop(self.key)

    def expire(self, key, time):
        return self.conn.expire(key, time)

    def s_add(self, value):
        return self.conn.sadd(self.key, value)

    def delete_all(self, key):
        return self.conn.lrange(key, 0, -1)

    def ltrim(self):
        return self.conn.ltrim(self.key, 0, 100)  # 限制101为长度


if __name__ == '__main__':
    RedisList('video').ltrim()  # 限制list中的长度
