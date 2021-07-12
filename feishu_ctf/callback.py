from typing import Any, Dict, Optional
from flask.json import jsonify
import requests
from flask import Request, Response
import os

class FeishuHandlerException(Exception):
    pass


class FeishuHandler:
    def handle(self, info: Dict[str, Any]) -> Response:
        raise NotImplementedError()


class VerificationHandler(FeishuHandler):
    def handle(self, info: Dict[str, Any]) -> Response:
        challenge = info.get('challenge', None)
        if challenge is None:
            raise FeishuHandlerException('challenge not provided')
        return jsonify({'challenge': challenge})


class FeishuMessageHandler:

    APP_VERIFICATION_TOKEN = os.environ['FEISHU_VERIFICATION_TOKEN']
    HANDLERS = {
        'url_verification':  VerificationHandler()
    }

    def __init__(self, req: Request):
        self.req = req

    def handle_message(self):
        req: Dict[str, Any] = self.req.json
        token = req.get('token', None)
        if token is None:
            raise FeishuHandlerException('missing token')

        if token != self.APP_VERIFICATION_TOKEN:
            raise FeishuHandlerException('invalid token')

        typ: str = req.get('type', '') 
        if typ not in self.HANDLERS:
            raise FeishuHandlerException('unsupported message type')

        self.HANDLERS[typ].handle(req) 