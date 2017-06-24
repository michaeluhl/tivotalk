import logging

from tivotalk.server.pubcom import Communicator
import tivotalk.mind.api as api
import tivotalk.mind.rpc as rpc


logger = logging.getLogger('tivoproxy')
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(sh)
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


class TiVoProxy(object):

    def __init__(self, config):
        self.manager = api.MindManager(config['TT_CERT_PATH'],
                                       config['TT_CERT_PWD'],
                                       config['TT_TIVO_ADDR'],
                                       rpc.MRPCCredential.new_mak(config['TT_TIVO_MAK']))
        self.com = Communicator(config['TT_PUBKEY'],
                                config['TT_SUBKEY'],
                                client_id=config['TT_CLIENT_ID'])
        self.com.swap_channels()

    def run(self):
        self.com.connect()
        if self.com.connected.wait(timeout=3.0):
            while True:
                logger.info("Waiting for command...")
                msg = self.com.messages.get().message
                self.com.messages.task_done()
                logger.info("Received message...")
                if 'cmd' in msg:
                    logger.info('Processing command...')
                    h = getattr(self, 'do_cmd_{}'.format(msg['cmd'].lower()), self.do_cmd_default)
                    r = h(msg)
                    logger.info('Result: {}'.format(str(r)))
                    if r is not None:
                        logger.info('Sending response...')
                        self.com.publish(message=r)
                else:
                    logger.warning('Message contained no command: {}'.format(str(msg)))
        else:
            raise ConnectionError('Failed to connect to PubNub.')

    def do_cmd_default(self, msg):
        logger.warning('Unknown command received: {}'.format(msg['cmd']))

    def do_cmd_pause(self, msg):
        with self.manager.mind() as m:
            result = m.send_key('pause')
            return {'cmd': msg['cmd'], 'status': result['type'].upper()}

    def do_cmd_resume(self, msg):
        with self.manager.mind() as m:
            result = m.send_key('play')
            return {'cmd': msg['cmd'], 'status': result['type'].upper()}

    def do_cmd_advance(self, msg):
        with self.manager.mind() as m:
            result = m.send_key('advance')
            return {'cmd': msg['cmd'], 'status': result['type'].upper()}



if __name__ == '__main__':
    import configparser

    cfg = configparser.ConfigParser()
    cfg.read('tivotalk.conf')
    config = cfg['General']

    logger.setLevel(logging.DEBUG)

    p = TiVoProxy(config=config)
    p.run()
