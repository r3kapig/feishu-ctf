from typing import Optional, Union, Any, Dict
import requests
import os


class FeishuException(Exception):
    pass


class FeishuClient:
    APP_VERIFICATION_TOKEN = os.environ['FEISHU_VERIFICATION_TOKEN']
    APP_SECRET = os.environ['FEISHU_SECRET']
    APP_ID = os.environ['APP_ID']

    SEND_MESSAGE_URL = 'https://open.feishu.cn/open-apis/message/v4/send/'
    GET_TENANT_ACCESS_TOKEN_URL = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/'

    def __init__(self) -> None:
        self.access_token = FeishuClient.get_tenant_access_token()

    @staticmethod
    def post(url: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        error_msg: Optional[str] = None) -> Dict[Any, Any]:
        res = requests.post(url, json=data, headers=headers).json()
        code = res.get('code', -1)
        if code != 0:
            if error_msg:
                raise FeishuException('{}: {}'.format(error_msg, res))
            else:
                raise FeishuException('Feishu API error with {}'.format(res))
        else:
            return res

    @staticmethod
    def get_tenant_access_token() -> str:
        url = FeishuClient.GET_TENANT_ACCESS_TOKEN_URL
        data = {
            "app_id": FeishuClient.APP_ID,
            "app_secret": FeishuClient.APP_SECRET
        }
        return FeishuClient.post(url, data).get('tenant_access_token', '')


    def send_message(self, text: str) -> None:
        url = self.SEND_MESSAGE_URL
        headers: Dict[str, str] = {
            "Authorization": "Bearer " + self.access_token 
        }
        data: Dict[str, Union[str, Dict[str, str]]] = {
            "open_id": self.APP_ID,
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        FeishuClient.post(url, data, headers=headers)