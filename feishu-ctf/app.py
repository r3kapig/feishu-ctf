from flask import Flask, jsonify, request
import os

from api import send_message, get_tenant_access_token

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