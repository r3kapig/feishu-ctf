from flask import Flask, request

from feishu_ctf.api import *
from feishu_ctf.callback import *

app = Flask(__name__)
api = FeishuClient()

@app.route('/callback', methods=['POST'])
def callback() -> Optional[requests.Response]:
    """feishu callback procedure
    """
    handler = FeishuMessageHandler(request)
    handler.handle_message()


@app.route("/")
def index():
    return "2019 so nb"


if __name__ == '__main__':
    app.run()
