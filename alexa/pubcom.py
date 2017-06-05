import logging
from queue import Queue
import threading
import uuid

from pubnub.enums import PNOperationType, PNStatusCategory
from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


class Communicator(SubscribeCallback):

    def __init__(self, pub_key, sub_key,
                 publish_channel="C_QUERY", subscribe_channel="C_RESP",
                 client_id=None, debug=False):
        self.messages = Queue()
        self.connected = threading.Event()
        self.stop_key = str(uuid.uuid4())

        self.subscribe_channel = subscribe_channel
        self.publish_channel = publish_channel

        self.pn = None

        self.config = PNConfiguration()
        self.config.publish_key = pub_key
        self.config.subscribe_key = sub_key
        self.config.uuid = client_id

        self.debug = debug

    def message(self, pubnub, message):
        msg = message.message
        print('Message: {}'.format(msg))
        if msg['cmd'] == 'STOP' and msg['key'] == self.stop_key:
            pubnub.unsubscribe().channels(self.subscribe_channel).execute()
            pubnub.remove_listener(self)
            pubnub.stop()
        else:
            self.messages.put(message)

    def presence(self, pubnub, presence):
        pass

    def status(self, pubnub, status):
        if status.operation in (PNOperationType.PNSubscribeOperation,
                                PNOperationType.PNUnsubscribeOperation):
            if status.category == PNStatusCategory.PNConnectedCategory:
                print('Connected.')
                self.connected.set()
            elif status.category == PNStatusCategory.PNDisconnectedCategory:
                print('Disconnected.')
                self.connected.clear()

    def swap_channels(self):
        if not self.connected.is_set():
            tmp = self.publish_channel
            self.publish_channel = self.subscribe_channel
            self.subscribe_channel = tmp

    def connect(self):
        self.pn = PubNub(self.config)
        if self.debug:
            import pubnub
            pubnub.set_stream_logger('pubnub', logging.DEBUG)
        self.pn.add_listener(self)
        self.pn.subscribe().channels(self.subscribe_channel).execute()

    def disconnect(self):
        msg = {'cmd': 'STOP',
               'key': self.stop_key}
        self.pn.publish().channel(self.subscribe_channel).message(msg).sync()

    def wait_for_message(self, timeout=1.0):
        if self.connected.is_set():
            env = self.messages.get(timeout=timeout)
            self.messages.task_done()
            return env
        else:
            raise ConnectionError('Not currently connected.')

    def publish(self, message):
        if self.connected.is_set():
            self.pn.publish().channel(self.publish_channel).message(message).sync()
        else:
            raise ConnectionError('Not currently connected.')
