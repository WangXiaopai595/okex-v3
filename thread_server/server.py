import threading
import okex.Account_api as Account
import okex.Market_api as Market
import okex.Trade_api as Trade
import json
from web3 import Web3
import time
import pymysql


class exchange(threading.Thread):
    def __init__(self, ok_conf, mysql_c, rpc_config, proxy):
        super().__init__()
        self.proxy = proxy["proxy_url"]
        self.rpc = rpc_config
        self.mysql_conf = mysql_c
        self.assert_detail = {
            "btc": 0,
            "usdc": 0,
            "eth": 0
        }
        self.my_balance = {
            "btc": 0,
            "usdt": 3000.0
        }
        self.api_key = ok_conf["api_key"]
        self.secret_key = ok_conf["secret_key"]
        self.passphrase = ok_conf["passphrase"]
        self.flag = ok_conf["flag"]
        self.last_rate = 0
        self.create_data = {}

    def run(self):
        while True:
            try:
                self.my_balance["usdt"], self.my_balance["btc"] = self.get_balance()

                self.create_data["btc_balance"] = "%f" % self.my_balance["btc"]
                self.create_data["usdt_balance"] = "%f" % self.my_balance["usdt"]

                btc_price = self.get_ticker()
                rate = self.get_buy_rate(btc_price)
                if rate != self.last_rate:
                    print("当前账户余额：usdt: %f, btc: %f" % (self.my_balance["usdt"], self.my_balance["btc"]))
                    self.last_rate = rate
                    mod, exchange_num = self.get_exchange_num(rate, btc_price)

                    self.create_data["exchange_rate"] = "%f" % rate
                    self.create_data["btc_price"] = "%f" % btc_price

                    exchange_num = round(exchange_num, 2)
                    succ = self.place_order(mod, exchange_num, btc_price)
                    print("-------------------------------------------------------------------------------------------")
                    if succ:
                        self.created_sql()
            except Exception as e:
                print("%s 发送错误：%s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), e))

            time.sleep(60)

    def created_sql(self):
        self.create_data["created_time"] = "%d" % time.time()
        conn = pymysql.connect(
            host=self.mysql_conf["host"],
            port=int(self.mysql_conf["port"]),
            db=self.mysql_conf["db"],
            user=self.mysql_conf["user"],
            password=self.mysql_conf["password"],
            cursorclass=pymysql.cursors.DictCursor
        )

        cursor = conn.cursor()
        keys = ",".join(self.create_data.keys())
        values = ",".join(self.create_data.values())
        sql = "insert into exchange_record (%s) values (%s)" % (keys, values)
        cursor.execute(sql)
        conn.commit()
        # 关闭数据库连接
        cursor.close()
        conn.close()

    def place_order(self, mod, exchange_num, price):
        if exchange_num < 40 and self.flag == "1":
            exchange_num = 40

        # if exchange_num < 5:
        #     print("交易金额小于5USDT，本次不触发交易。")

        btc_num = exchange_num / price

        self.create_data["exchange_usdt"] = "%f" % exchange_num
        self.create_data["exchange_btc"] = "%f" % btc_num
        self.create_data["exchange_mod"] = "\"%s\"" % mod
        # self.create_data["position_rate"] = "%f" % btc_num

        tradeAPI = Trade.TradeAPI(self.api_key, self.secret_key, self.passphrase, False, self.flag, self.proxy)
        if mod == "buy":
            result = tradeAPI.place_order(instId='BTC-USDT', tdMode='cash', side=mod, ordType='market', sz=str(exchange_num))
        else:
            if btc_num > self.my_balance["btc"]:
                btc_num = self.my_balance["btc"]
                exchange_num = btc_num * price
            sz = "%f" % btc_num
            result = tradeAPI.place_order(instId='BTC-USDT', tdMode='cash', side=mod, ordType='market', sz=sz)

        print("本次交易类型：%s， 本次交易USD数量：%f (相当于 %f 个btc)，当前btc价格：%f" % (mod, exchange_num, btc_num, price))
        if result["data"][0]["sCode"] == "0":
            print("本次交易成功：交易usdt数量为：%f，交易类型：%s" % (exchange_num, mod))
        else:
            print("交易失败：%s" % json.dumps(result))
        return result["data"][0]["sCode"] == "0"

    def get_balance(self):
        accountAPI = Account.AccountAPI(self.api_key, self.secret_key, self.passphrase, False, self.flag, self.proxy)
        usd = accountAPI.get_account("USDT")
        btc = accountAPI.get_account("BTC")
        usd_num = 0
        btc_num = 0
        if len(usd["data"][0]["details"]):
            usd_num = float(usd["data"][0]["details"][0]["cashBal"])

        if len(btc["data"][0]["details"]):
            btc_num = float(btc["data"][0]["details"][0]["cashBal"])

        return usd_num, btc_num

    def get_exchange_num(self, rate, price):
        """
        计算本次交易数量及类型
        :param rate: 链上所占比例
        :param price: btc价格
        :return: 交易类型、交易数量
        """
        btc_assert = self.my_balance["btc"] * price
        total = btc_assert + self.my_balance["usdt"]

        self.create_data["total_balance"] = "%f" % total

        now_rate = btc_assert / total

        mod = ""
        exchange_num = 0
        if now_rate > rate:
            mod = "sell"
            exchange_num = total * (now_rate - rate)
        elif now_rate < rate:
            mod = "buy"
            exchange_num = total * (rate - now_rate)
        return mod, exchange_num

    def get_buy_rate(self, price):
        """
        抓取链上资产，并计算本次交易比例
        :param price: 当前btc价格
        :return:
        """
        my_provider = Web3.HTTPProvider(self.rpc["rpc_url"])
        w3 = Web3(my_provider)
        addr = self.rpc["address"]

        abi = self.rpc["abi"]

        contract_instance = w3.eth.contract(address=addr, abi=abi)
        contract_assert = contract_instance.functions.getTotalAssert().call()

        rate = self.last_rate
        if contract_assert[1] / 1e6 != self.assert_detail["usdc"] or contract_assert[2] / 1e8 != self.assert_detail["btc"]:
            print("触发时间：%s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            print("链上原资产：", self.assert_detail)
            self.assert_detail["eth"] = contract_assert[0] / 1e18
            self.assert_detail["usdc"] = contract_assert[1] / 1e6
            self.assert_detail["btc"] = contract_assert[2] / 1e8
            print("链上现有资产：", self.assert_detail)
            btc_assert = self.assert_detail["btc"] * price
            rate = btc_assert / (btc_assert + self.assert_detail["usdc"])

        return rate

    def get_ticker(self, ticker='BTC-USDT'):
        """
        获取某交易对汇率
        :param ticker: 交易对ID
        :return: float
        """
        # market api
        marketAPI = Market.MarketAPI(self.api_key, self.secret_key, self.passphrase, False, self.flag, self.proxy)
        result = marketAPI.get_ticker(ticker)
        return float(result["data"][0]["last"])
