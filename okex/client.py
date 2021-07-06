import requests
import json
from . import consts as c, utils, exceptions


class Client(object):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, flag='1', proxy=None):
        self.proxy = proxy
        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.PASSPHRASE = passphrase
        self.use_server_time = use_server_time
        self.flag = flag

    def _request(self, method, request_path, params):

        if method == c.GET:
            request_path = request_path + utils.parse_params_to_str(params)
        # url
        url = c.API_URL + request_path

        timestamp = utils.get_timestamp()

        # sign & header
        if self.use_server_time:
            timestamp = self._get_timestamp()

        body = json.dumps(params) if method == c.POST else ""

        sign = utils.sign(utils.pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
        header = utils.get_header(self.API_KEY, sign, timestamp, self.PASSPHRASE, self.flag)

        # send request
        response = None

        # print("url:", url)
        # print("headers:", header)
        # print("body:", body)
        # proxy = "113.204.194.92:10089"
        proxies = None
        if self.proxy is not  None:
            proxy = "127.0.0.1:10808"
            proxies = {
                'http': 'socks5://' + proxy,
                'https': 'socks5://' + proxy
            }

        requests.packages.urllib3.disable_warnings()
        if method == c.GET:
            response = requests.get(url, headers=header, proxies=proxies, verify=False)
        elif method == c.POST:
            response = requests.post(url, data=body, headers=header, proxies=proxies, verify=False)

        # exception handle
        # print(response.headers)

        if not str(response.status_code).startswith('2'):
            raise exceptions.OkexAPIException(response)

        return response.json()

    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})

    def _request_with_params(self, method, request_path, params):
        return self._request(method, request_path, params)

    def _get_timestamp(self):
        url = c.API_URL + c.SERVER_TIMESTAMP_URL
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['ts']
        else:
            return ""
