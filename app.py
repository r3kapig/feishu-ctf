from flask import Flask, request

from feishu_ctf.api import *
from feishu_ctf.handlers import *

from time import strftime

app = Flask(__name__)

@app.route('/callback', methods=['POST'])
def callback():
    """feishu callback procedure
    """
    handler = FeishuMessageHandler(request)
    try:
        return handler.handle_message()
    except Exception as e:
        logger.error('exception happened: ' + str(e) + ' ' + traceback.format_exc())
        traceback.print_exc()
        return str(e), 200


@app.route("/", methods=['GET'])
def index():
    return "2019 so nb"


if __name__ == '__main__':
    app.run()