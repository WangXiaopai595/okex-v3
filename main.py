# coding:utf-8
from thread_server.server import exchange
import configparser
import os


def get_config():
    cf = configparser.ConfigParser()
    cf.read(os.path.abspath('.') + "/config.ini", encoding="utf-8")
    section = cf.sections()

    res = {}
    for item in section:
        item_map = {}
        config_item = cf.items(item)
        for kv in range(len(config_item)):
            item_map[config_item[kv][0]] = config_item[kv][1]
        res[item] = item_map
    return res


exchange_config = get_config()

# 创建线程
t = exchange(exchange_config["okex-api"], exchange_config["mysql"], exchange_config["rpc"], exchange_config["proxy"])
# t.setDaemon(True)
t.setDaemon(False)
t.start()
