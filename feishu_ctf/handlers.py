from typing import Any, Dict, List, Optional
from flask.json import jsonify
import json
import traceback
from flask import Request, Response
from feishu_ctf.api import API

class FeishuHandlerException(Exception):
    pass


class FeishuHandler:
    def handle(self, info: Dict[str, Any]) -> Response:
        raise NotImplementedError()


class FeishuEventHandler:
    def handle(self, event: Dict[str, Any]) -> Response:
        raise NotImplementedError()

class CommandArg:
    def __init__(self, name, optional = False):
        self.name = name
        self.optional = optional

    def __str__(self) -> str:
        if not self.optional:
            return self.name
        else:
            return '[' + self.name + ']'

class CommandHandler:

    @staticmethod
    def help() -> str:
        """returns help message
        """
        raise NotImplementedError()

    @staticmethod
    def args() -> List[CommandArg]:
        """returns args definition"""
        raise NotImplementedError()

    def usage(self, name):
        args_help = ' '.join(map(str, self.args()))
        return '{}: {} - {} {}'.format(
            name, self.help(), name, args_help
        )

    def handle(self, event: Dict[str, Any]) -> Response:
        content: str = json.loads(event['message']['content'])['text'].split(maxsplit=1)[1]
        cmd = content.split(maxsplit=len(self.args()))
        name = cmd[0]
        cmd = cmd[1:]
        arg_len = len(list(filter(lambda x: not x.optional, self.args())))
        if len(cmd) < arg_len:
            raise FeishuHandlerException('expected {} args got {}: {}'.format(arg_len, len(cmd)), self.usage(name))
        return self.handle_command(cmd, event)

    def handle_command(self, cmd: List[str], event: Dict[str, Any]) -> Response:
        raise NotImplementedError()


class VerificationHandler(FeishuHandler):
    def handle(self, info: Dict[str, Any]) -> Response:
        token = info.get('token', None)
        if token is None:
            raise FeishuHandlerException('missing token')

        if token != API.APP_VERIFICATION_TOKEN:
            raise FeishuHandlerException('invalid token')
        challenge = info.get('challenge', None)
        if challenge is None:
            raise FeishuHandlerException('challenge not provided')
        return jsonify({'challenge': challenge})


class NewChallCommand(CommandHandler):
    @staticmethod
    def help():
        return 'add a new chall to this event'

    @staticmethod
    def args():
        return [CommandArg('category'), CommandArg('name')]

    def handle_command(self, cmd: List[str], event: Dict[str, Any]) -> Response:
        chall_category = cmd[0]
        chall_name = cmd[1]

        chat_id = event['message']['chat_id']
        cur_chat_info = API.get_chat_info(chat_id)
        cur_chat_name = cur_chat_info['name']

        name = '{} - {}'.format(cur_chat_name, chall_name)
        description = '{}: {}'.format(name, chall_category)

        new_chat_info = API.create_chat_group(name, description)
        content = {
            'chat_id': new_chat_info['chat_id']
        }
        API.send_message(chat_id, content, msg_type='share_chat')
        return Response()


class MessageReceiveEventHandler(FeishuEventHandler):

    HANDLERS = {
        'new-chall': NewChallCommand(),
        'nc': NewChallCommand(),
        '新题': NewChallCommand(),
    }

    def handle(self, event: Dict[str, Any]) -> Response:
        def open_id_equals(mention):
            return mention['id']['open_id']

        if event['message'].get('mentions') is None or \
            not all(map(
            open_id_equals,
            event['message']['mentions'])):
            return Response('Bot: not my message')

        chat_id = event['message']['chat_id']
        
        try:
            content = json.loads(event['message']['content'])['text']
            splits = content.split(maxsplit=1)
            if len(splits) > 1:
                cmd = splits[1]
                for handler_cmd in self.HANDLERS.keys():
                    if cmd.startswith(handler_cmd):
                        return self.HANDLERS[handler_cmd].handle(event)
            else:
                cmd = '<empty>'

            content = {
                'text': 'No such command: {}'.format(cmd)
            }
            API.send_message(chat_id, content)
            return Response('liangjs said: Command is not valid!', status=200)
        except Exception as e:
            err_text = traceback.format_exc()
            content = {
                'text': 'Exception happened in bot: ' + str(e) + ' ' + err_text
            }
            API.send_message(chat_id, content)

            return Response('liangjs said: Exception happened! No!', 200)


class EventCallbackHandler(FeishuHandler):

    HANDLERS = {
        'im.message.receive_v1': MessageReceiveEventHandler()
    }

    def handle(self, info: Dict[str, Any]) -> Response:
        typ = info['header']['event_type']
        if typ not in self.HANDLERS:
            raise FeishuHandlerException('unsupported event {}'.format(typ))
        event = info['event']
        return self.HANDLERS[typ].handle(event)


class FeishuMessageHandler:

    HANDLERS = {
        'url_verification':  VerificationHandler(),
        'event_callback': EventCallbackHandler(),
    }

    def __init__(self, req: Request):
        self.req = req

    def handle_message(self) -> Response:
        req: Dict[str, Any] = self.req.json

        typ: str = req.get('type', None) 
        if typ not in self.HANDLERS:
            # 2.0 won't use event_callback as the type.
            # see: https://open.feishu.cn/document/ukTMukTMukTM/uUTNz4SN1MjL1UzM#8f960a4b
            typ = 'event_callback'

        return self.HANDLERS[typ].handle(req) 