import os

import lambdaskill.utils as utils
from lambdaskill import *
from tivotalk.server.pubcom import Communicator

PUBKEY = os.environ['TT_PUBKEY']
SUBKEY = os.environ['TT_SUBKEY']
CLIENT_ID = os.environ['TT_CLIENT_ID']
SKILL_ID = os.environ['TT_SKILL_ID']


class CommandError(Exception):
    pass


class TiVoTalk(Skill):

    def __init__(self):
        Skill.__init__(self)
        self._app_id = SKILL_ID
        self.com = Communicator(pub_key=PUBKEY, sub_key=SUBKEY, client_id=CLIENT_ID)

    def on_launch_request(self, request):
        logger.info('Received Launch Request.')
        return Response.respond(output="Welcome to TiVo Talk. "
                                       "Please tell me what you'd like to know, by saying, "
                                       "what's on, or when is Game of Thrones on?")\
            .add_reprompt().add_card(title='Welcome!')

    def handler(self, event, context):
        try:
            return Skill.handler(self, event=event, context=context)
        except CommandError:
            req = Request.wrap(event)
            resp = Response.respond("An error occurred processing your request.  "
                                    "Please state your request again.").add_reprompt()
            return resp.prepare(session_attributes=req.session_attributes)
        except ConnectionError:
            req = Request.wrap(event)
            resp = Response.finish("Failed to connect to TiVo Proxy.  Try again in a few moments.")
            return resp.prepare(session_attributes=req.session_attributes)


    def exec_list_cmd(self, message, list_key):
        com = self.com
        com.connect()
        if com.connected.wait(timeout=1.0):
            com.publish(message=message)
            resp = com.wait_for_message(timeout=3.0).message
            if resp['cmd'] == message['cmd'] and resp['status'] == 'SUCCESS':
                count = resp['total_count']
                items = []
                while True:
                    items.extend(resp[list_key])
                    if len(items) >= count:
                        break
                    resp = com.wait_for_message(timeout=3.0).message
                return items
            raise CommandError('An error occured while executing the command.')
        raise ConnectionError('Failed to connect to remote server.')

    def exec_cmd_check(self, message):
        com = self.com
        com.connect()
        if com.connected.wait(timeout=1.0):
            com.publish(message=message)
            resp = com.wait_for_message(timeout=3.0).message
            if resp['cmd'] == message['cmd'] and resp['status'] == 'SUCCESS':
                return
            raise CommandError('An error occured while executing the command.')
        raise ConnectionError('Failed to connect to remote server.')

    def exec_cmd(self, message):
        com = self.com
        com.connect()
        if com.connected.wait(timeout=1.0):
            com.publish(message=message)
            return
        raise ConnectionError('Failed to connect to remote server.')

    def do_whatsonintent(self, request):
        """Queries the TiVo to find out what its going to record.
        """

        slots = request.get_slots()

        recording_time = slots.get('RECORDING_DATE', 'PRESENT_REF')
        recording_time = recording_time if recording_time != "" else 'PRESENT_REF'

        recordings = self.exec_list_cmd(message={'cmd': 'WHATSON',
                                                 'rec_time': recording_time},
                                        list_key='recordings')
        output = "I'm recording the following items: {}".format(utils.sequence_to_oxford_string(recordings))
        return Response.respond(output=output).add_card(title='ToDo:')

    def do_pauseintent(self, request):
        self.exec_cmd_check(message={'cmd': 'PAUSE'})
        return Response.finish(output="Paused")

    def do_resumeintent(self, request):
        self.exec_cmd_check(message={'cmd': 'RESUME'})
        return Response.finish(output=None)

    def do_advanceintent(self, request):
        self.exec_cmd_check(message={'cmd': 'ADVANCE'})
        return Response.finish(output=None)


handler = TiVoTalk.get_handler()
