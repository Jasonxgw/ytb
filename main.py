# coding=utf-8
import json
import random
import re
import time
import os
import json
import redis
import platform
from pprint import pprint
from threading import Thread
from TimePinner import Pinner
from DrissionPage import ChromiumPage
from DrissionPage.common import Keys
from DrissionPage._units.actions import Actions
from DrissionPage._configs.chromium_options import ChromiumOptions
SYS_ENV = platform.system()
database_redis = {
    'host': '103.242.3.43',  # 公网
    'port': 1968,
    'user': '',
    'password': '',
    'db': '0'
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


# 封装Hash方法
class RedisHash(RedisDB):

    def __init__(self, key):  # key为表名
        super(RedisHash, self).__init__(key)

    # 添加数据
    def set(self, dic):
        try:
            self.conn.hmset(self.key, dic)
            return True
        except Exception as e:
            self.set(dic)  # 放入失败 重新放入
            return False

    def get_value(self, field):
        return self.conn.hmget(self.key, field)

    def get_values(self, *field):
        data_bytes = self.conn.hmget(self.key, field)
        if data_bytes != [None]:
            data = eval(data_bytes[0]) if len(data_bytes) == 1 else \
                [i != None and eval(i) or i for i in data_bytes]
        else:
            data = {}
        return data

    # 获取全部`field` 和 `value
    def get_all(self):
        all = self.conn.hgetall(self.key)
        all_dict = {k: json.loads(v) for k, v in all.items()}
        return all_dict

    # 删除
    def hdel(self, *field):
        # 如果只传field ，会有解包错误， 而不执行代码的情况
        return self.conn.hdel(self.key, *field)

    # 查看所有的value
    def hvals(self):
        return self.conn.hvals(self.key)

    # 查看所有的field
    def hkeys(self):
        keys = self.conn.hkeys(self.key)
        keys_list = [i for i in keys]
        return keys_list

    # 查看有几个键值对
    def hlen(self):
        keys = self.conn.hlen(self.key)
        keys_list = [i for i in keys]
        return keys_list

    # 判断hash表中指定域是否存在，返回1，若key或field不存在则返回0；
    def hexists(self, field):
        try:
            return self.conn.hexists(self.key, field)
        except Exception as e:
            return False

    def get_pop(self):
        all = self.conn.hgetall(self.key)
        tmp = []
        for k, v in all.items():
            self.hdel(k)
            tmp.append(v)
        return tmp[:10]

    def get_all_dict(self):
        return self.conn.hgetall(self.key)


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


class RedisSet(RedisDB):

    def __init__(self, key):  # key为表名
        super(RedisSet, self).__init__(key)

    def s_add(self, value):
        return self.conn.sadd(self.key, value)

    def smembers(self):
        return self.conn.smembers(self.key)

    def is_exist(self, value):
        return self.conn.sismember(self.key, value)

    def s_pop(self):
        return self.conn.spop(self.key)


def get_user_info(url, page):
    # 跳转到登录页面
    page.listen.start('/youtubei/v1/next')  # 指定监听目标并启动监听
    page.get(url)
    video_list = re.findall(r'url":"\/watch\?v=(.*?)"', str(page.html), re.I)
    if video_list:
        for i in list(set(video_list)):
            if RedisSet("video_id").is_exist(i[:11]):
                continue
            RedisList('video').InsertData(f"https://www.youtube.com/watch?v={i[:11]}")
    time.sleep(1)
    if '评论已关闭' in str(page.html) or '此视频无法再播放' in str(page.html):
        return
    num = 0
    page.scroll.to_bottom()  # 防止没有评论的视频，卡死程序
    # while True:
    print(page.url)
    packet = page.listen.wait()  # 等待数据包
    time.sleep(1)
    page.scroll.to_bottom()
    time.sleep(1)
    if packet.response.body is None:
        return
    handle_response(packet.response.body)  # 打印数据包正文
    return page


def handle_response(response):
    comments = response.get("frameworkUpdates").get("entityBatchUpdate").get("mutations")
    for i in comments:
        try:
            user_name = i["payload"]["commentEntityPayload"]["properties"]["authorButtonA11y"]
            print(user_name)
            RedisSet("ytb").s_add(user_name)
        except Exception as e:
            pass


def get_video(url):
    co = ChromiumOptions()
    co.set_load_mode('eager')
    # 用 d 模式创建页面对象（默认模式）
    page = ChromiumPage()
    user_name = re.findall(r'com/(.*?)/videos', url)[0]
    # 跳转到登录页面
    page.listen.start(f'/{user_name}/videos')  # 指定监听目标并启动监听
    page.listen.start('/youtubei/v1/browse')  # 指定监听目标并启动监听
    page.get(url)
    time.sleep(1)
    num = 0
    while True:
        time.sleep(1)
        page.scroll.to_bottom()
        time.sleep(1)
        packet = page.listen.wait()  # 等待数据包
        video_list = re.findall(r'url":"\/watch\?v=(.*?)"', str(packet.response.body), re.I)
        video_list1 = list(set(re.findall(r"'videoId': '(.*?)'", str(packet.response.body), re.I)))
        if video_list:
            for i in video_list:
                if RedisSet("video_id").is_exist(i[:11]):
                    continue
                RedisList('video').InsertData(f"https://www.youtube.com/watch?v={i[:11]}")
        if video_list1:
            for i in video_list1:
                if RedisSet("video_id").is_exist(i[:11]):
                    continue
                RedisList('video').InsertData(f"https://www.youtube.com/watch?v={i[:11]}")


def handle_video():
    pass


def run(page):
    while True:
        url = RedisList('video').DeletePop()
        if url is None:
            break
        video_id = url.split('=')[1]
        try:
            if RedisSet("video_id").is_exist(video_id):
                continue
            RedisSet("video_id").s_add(video_id)
            get_user_info(url, page)
        except Exception as e:
            continue


if __name__ == '__main__':
    if SYS_ENV == "Windows":
        co = ChromiumOptions().auto_port()
    else:
        path = "/opt/google/chrome/google-chrome"
        co = ChromiumOptions().auto_port().set_browser_path(path)
    co.headless(True)
    # 用 d 模式创建页面对象（默认模式）
    page1 = ChromiumPage(co)
    page2 = ChromiumPage(co)

    Thread(target=run, args=(page1,)).start()
    Thread(target=run, args=(page2,)).start()
