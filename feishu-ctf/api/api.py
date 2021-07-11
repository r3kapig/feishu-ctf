from typing import Any
import requests
import os

APP_VERIFICATION_TOKEN = os.environ['FEISHU_VERIFICATION_TOKEN']
APP_SECRET = os.environ['FEISHU_SECRET']
APP_ID = os.environ['APP_ID']


def send_message(token: str, open_id: str, text: str):
    url = "https://open.feishu.cn/open-apis/message/v4/send/"

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
        }
    req_body: dict[str, Any] = {
         "open_id": open_id,
          "msg_type": "text",
         "content": {
                "text": text
            }
         }

    req = requests.post(url, data=req_body, headers=headers)
    rsp_dict = req.json()
    code = rsp_dict.get("code", -1)
    if code != 0:
        raise Exception("send message error, code = " + code + ", msg =", rsp_dict.get("msg", ""))

    
def get_tenant_access_token() -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
    req_body = {
         "app_id": APP_ID,
         "app_secret": APP_SECRET
    }

    rsp_dict = requests.post(url, json=req_body)
    code = rsp_dict.get("code", -1)
    if code != 0:
        raise Exception("get tenant_access_token error, code =" + code)
    return rsp_dict.get("tenant_access_token", "")
