from typing import Optional, Union, Any, Dict
import requests
import os
import json
import logging

logger = logging.getLogger('feishu-ctf')


class FeishuException(Exception):
    pass


class FeishuClient:
    APP_VERIFICATION_TOKEN = os.environ['FEISHU_VERIFICATION_TOKEN']
    APP_SECRET = os.environ['FEISHU_SECRET']
    APP_ID = os.environ['APP_ID']

    MESSAGE_URL = '	https://open.feishu.cn/open-apis/im/v1/messages'
    GET_APP_ACCESS_TOKEN_URL = 'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/'
    BOT_INFO_URL = 'https://open.feishu.cn/open-apis/bot/v3/info'
    CREATE_CHAT_URL = 'https://open.feishu.cn/open-apis/im/v1/chats'
    CHAT_INFO_URL = 'https://open.feishu.cn/open-apis/im/v1/chats/{}'
    LIST_CHAT_URL = 'https://open.feishu.cn/open-apis/im/v1/chats'

    bot_info: Dict[str, Any]

    def __init__(self) -> None:
        self.access_token = FeishuClient.get_access_token()
        self.bot_info = FeishuClient.get_bot_info(self.access_token)

    @staticmethod
    def request(url: str,
        method: str,
        data: Dict[str, Any] = None,
        headers: Optional[Dict[str, str]] = None) -> Dict[Any, Any]:

        logger.info('{} request {} with data {} headers {}'.format(
            method,
            url,
            data,
            headers
        ))

        res = requests.request(method, url, json=data, headers=headers)
        res = res.json()
        code = res.get('code', -1)
        if code != 0:
                raise FeishuException('Feishu API error with {}'.format(res.get('msg', '(no msg)')))
        else:
            return res

    @staticmethod
    def post(url: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None):
        return FeishuClient.request(url, 'post', data, headers)
    
    @staticmethod
    def get(url: str,
        data: Dict[str, Any] = None,
        headers: Optional[Dict[str, str]] = None):
        return FeishuClient.request(url, 'get', data, headers)

    def authorized_post(self,
        url: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if headers is None:
            headers = {}
        headers['Authorization'] = 'Bearer ' + self.access_token

        return self.post(url, data, headers)

    def authorized_get(self,
        url: str,
        data: Dict[str, Any] = None,
        headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if headers is None:
            headers = {}
        headers['Authorization'] = 'Bearer ' + self.access_token
        return self.get(url, data, headers)

    @staticmethod
    def get_access_token() -> str:
        url = FeishuClient.GET_APP_ACCESS_TOKEN_URL
        data = {
            "app_id": FeishuClient.APP_ID,
            "app_secret": FeishuClient.APP_SECRET
        }
        return FeishuClient.post(url, data).get('tenant_access_token', '')

    @staticmethod
    def get_bot_info(access_token: str) -> Dict[str, Any]:
        headers = {
            'Authorization': 'Bearer ' + access_token
        }
        return FeishuClient.post(FeishuClient.BOT_INFO_URL, data={}, headers=headers)['bot']

    def create_chat_group(self, name, description=None) -> Dict[str, Any]:
        url = FeishuClient.CREATE_CHAT_URL
        data = {
            'name': name,
            'chat_type': 'public'
        }
        if description:
            data['description'] = description
        return self.authorized_post(url, data)['data']

    def get_chat_info(self, chat_id: Union[int, str]) -> Dict[str, Any]:
        url = FeishuClient.CHAT_INFO_URL.format(chat_id)
        return self.authorized_get(url)['data']

    def list_chats(self) -> Dict[str, Any]:
        url = FeishuClient.LIST_CHAT_URL
        return self.authorized_get(url)['data']


    def send_message(self,
        chat_id: str,
        content: Dict[str, Any], msg_type: str = 'text') -> Dict[str, Any]:
        url = self.MESSAGE_URL + '?receive_id_type=chat_id'
        data = {
            'receive_id': chat_id,
            'content': json.dumps(content),
            'msg_type': msg_type
        }
        return self.authorized_post(url, data)

API = FeishuClient()