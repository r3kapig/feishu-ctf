from typing import Any, Dict, List, Optional
from flask.json import jsonify
import json
import traceback
from flask import Request, Response
from feishu_ctf.api import API
from feishu_ctf.ctf import CTF, ChallState

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
        # if len(cmd) < arg_len:
        #     raise FeishuHandlerException('expected {} args got {}: {}'.format(arg_len, len(cmd)), self.usage(name))
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
        chat_id = event['message']['chat_id']

        # some basic checks
        if len(cmd) != 2:
            API.send_message(chat_id, {'text': "Error: command should be 'nc category challenge_name'"})
            return Response('liangjs said: Error happened! No!', 200)
        event_name = CTF.get_event_from_group(chat_id)
        if event_name is None:
            API.send_message(chat_id, {'text': "Error: command should be used within chat associated with an event"})
            return Response('liangjs said: Error happened! No!', 200)

        # obtain basic information
        chall_category = cmd[0]
        chall_name = cmd[1]
        # cur_chat_name = API.get_chat_info(chat_id)['name']
        # check if already exists
        if not (CTF.get_event(event_name).get_chall(chall_name) is None):
            API.send_message(chat_id, {'text': "Error: challenge already exists"})
            return Response('liangjs said: Error happened! No!', 200)

        # create the group
        name = '{}-{}'.format(event_name, chall_name)
        description = '{}: {}'.format(name, chall_category)
        new_chat_info = API.create_chat_group(name, description)
        content = {'chat_id': new_chat_info['chat_id']}
        API.send_message(chat_id, content, msg_type='share_chat')

        # update manager
        CTF.add_challenge(event_name, chall_name, \
            chall_category, new_chat_info['chat_id'])

        return Response("OK", 200)

class NewEventCommand(CommandHandler):
    @staticmethod
    def help():
        return 'add a new CTF event'

    @staticmethod
    def args():
        return [CommandArg('CTF name')]

    def handle_command(self, cmd: List[str], event: Dict[str, Any]) -> Response:
        chat_id = event['message']['chat_id']
        if len(cmd) != 1:
            API.send_message(chat_id, {'text': "Error: command should be 'newctf event_name'"})
            return Response('liangjs said: Error happened! No!', 200)

        ctf_name = cmd[0]
        if not (CTF.get_event(ctf_name) is None):
            API.send_message(chat_id, {'text': "Error: such CTF event already exists"})
            # TODO: maybe send the group link in this case
            return Response('liangjs said: Error happened! No!', 200)

        # create the chat group
        new_chat_info = API.create_chat_group(ctf_name, ctf_name)
        # add to CTF manager
        CTF.new_event(ctf_name, new_chat_info['chat_id'])
        # send the newly created chat
        API.send_message(chat_id, \
            {'chat_id': new_chat_info['chat_id']}, \
            msg_type='share_chat')

        return Response("OK", 200)


class ShowChatCommand(CommandHandler):
    @staticmethod
    def help():
        return 'show main chat or challenge chat of a CTF'

    @staticmethod
    def args():
        return [CommandArg('chall')]

    def handle_command(self, cmd: List[str], event: Dict[str, Any]) -> Response:
        chat_id = event['message']['chat_id']
        if len(cmd) > 1:
            API.send_message(chat_id, {'text': "Error: command should be 'sc challenge' for showing challenge chat and 'sc' for showing main chat"})
            return Response('liangjs said: Error happened! No!', 200)

        # get current CTF event
        event_name = CTF.get_event_from_group(chat_id)
        if event_name is None:
            API.send_message(chat_id, {'text': "Error: command should be used within chat associated with an event"})
            return Response('liangjs said: Error happened! No!', 200)

        # get and send chat_id_ret
        if len(cmd) == 0:
            chat_id_ret = CTF.get_main_chat(event_name)
        else: # == 1
            chat_id_ret = CTF.get_chall_chat(event_name, cmd[0])
        if chat_id_ret is None:
            API.send_message(chat_id, {'text': "Error: challenge does not exists"})
        else:
            API.send_message(chat_id, {'chat_id':chat_id_ret}, msg_type='share_chat')

        return Response("OK", 200)

class ListCommand(CommandHandler):
    @staticmethod
    def help():
        return 'list challenges status'

    @staticmethod
    def args():
        return []

    def handle_command(self, cmd: List[str], event: Dict[str, Any]) -> Response:
        chat_id = event['message']['chat_id']

        # get current CTF event
        event_name = CTF.get_event_from_group(chat_id)
        if event_name is None:
            API.send_message(chat_id, {'text': "Error: command should be used within chat associated with an event"})
            return Response('liangjs said: Error happened! No!', 200)

        # get the result
        ctf = CTF.get_event(event_name)
        ret = ""
        def show(chall_name, chall):
            nonlocal ret
            ret += "%s(%s)[%s]: %s\n" % (chall_name, \
                " ".join(chall.categories), \
                chall.state.value, \
                ", ".join(chall.workings))
        ctf.iter_chall(show)

        # send
        API.send_message(chat_id, {'text': ret})

        return Response("OK", 200)

class WorkCommand(CommandHandler):
    @staticmethod
    def help():
        return 'mark people working on the challenge'

    @staticmethod
    def args():
        return []

    # TODO: mark other people as working on the challenge
    def handle_command(self, cmd: List[str], event: Dict[str, Any]) -> Response:
        chat_id = event['message']['chat_id']

        # get user who sends this message
        uid = event['sender']['sender_id']['user_id']
        API.send_message(chat_id, {'text': \
            "{} is working on the challenge".format(API.get_user_name(uid))})

        # get current CTF challenge
        chall = CTF.get_chall_from_group(chat_id)
        if chall is None or chall[1] is None:
            API.send_message(chat_id, {'text': "Error: command should be used within chat associated with a challenge"})
            return Response('liangjs said: Error happened! No!', 200)

        CTF.get_event(chall[0]).get_chall(chall[1]).add_person(API.get_user_name(uid))
        # TODO: may change
        return Response("OK", 200)

class MarkCommands(CommandHandler):
    @staticmethod
    def args():
        return []

    def handle_command_helper(self, cmd: List[str], event: Dict[str, Any], state: ChallState) -> Response:
        chat_id = event['message']['chat_id']

        # get current CTF challenge
        chall = CTF.get_chall_from_group(chat_id)
        if chall is None or chall[1] is None:
            API.send_message(chat_id, {'text': "Error: command should be used within chat associated with a challenge"})
            return Response('liangjs said: Error happened! No!', 200)

        CTF.get_event(chall[0]).get_chall(chall[1]).state = state

        return Response("OK", 200)

class SolvedCommand(MarkCommands):
    @staticmethod
    def help():
        return 'mark the challenge as solved'
    def handle_command(self, cmd: List[str], event: Dict[str, Any]) -> Response:
        ret = self.handle_command_helper(cmd, event, ChallState.Solved)
        API.send_message(event['message']['chat_id'], \
            {'text': "Congratulation! The challenge is solved!"})
        return ret
class StuckCommand(MarkCommands):
    @staticmethod
    def help():
        return 'mark the challenge as stuck'
    def handle_command(self, cmd: List[str], event: Dict[str, Any]) -> Response:
        return self.handle_command_helper(cmd, event, ChallState.Stuck)
class ProgressCommand(MarkCommands):
    @staticmethod
    def help():
        return 'mark the challenge as progress'
    def handle_command(self, cmd: List[str], event: Dict[str, Any]) -> Response:
        return self.handle_command_helper(cmd, event, ChallState.Progress)


class MessageReceiveEventHandler(FeishuEventHandler):

    HANDLERS = {
        'new-chall': NewChallCommand(),
        'nc': NewChallCommand(),
        '新题': NewChallCommand(),
        'newctf': NewEventCommand(),
        'showchat': ShowChatCommand(),
        'sc': ShowChatCommand(),
        'ls': ListCommand(),
        'w': WorkCommand(),
        'solved': SolvedCommand(),
        'solve': SolvedCommand(),
        'stuck': StuckCommand(),
        'progress': ProgressCommand(),
        'prog': ProgressCommand()
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
                    if cmd == handler_cmd or cmd.startswith(handler_cmd + ' '):
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