from flask import Flask, jsonify, request
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


app = Flask(__name__)

def handle_message(event):
    # 此处只处理 text 类型消息，其他类型消息忽略
    msg_type = event.get("msg_type", "")
    if msg_type != "text":
        print("unknown msg_type =" + msg_type)
        return

    # 调用发消息 API 之前，先要获取 API 调用凭证：tenant_access_token
    access_token = get_tenant_access_token()
    if access_token == "":
        return

    # 机器人 echo 收到的消息
    send_message(access_token, event.get("open_id"), event.get("text"))
    return


@app.route('/callback')
def callback():
    """feishu callback procedure
    """
    content = request.json     

    token = content['token']
    if token != APP_VERIFICATION_TOKEN:
        return

    typ = content.get('type', '')
    if typ == 'url_verification':
        challenge = content.get('challenge')
        return jsonify({'challenge': challenge})
    elif typ == 'event_callback':
        event = content.get('event')
        if event.get('type', '') == 'message':
            return handle_error(event)


@app.route("/")
def index():
    return "2019 so nb"


if __name__ == '__main__':
    app.run()