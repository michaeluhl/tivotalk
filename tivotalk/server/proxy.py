import arrow
import datetime
import json
import logging
import time

from fuzzywuzzy import process

from tivotalk.server.pubcom import Communicator
import tivotalk.mind.api as api
import tivotalk.mind.rpc as rpc
import lambdaskill.utils as utils


logger = logging.getLogger('tivoproxy')
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(sh)
if logger.level == logging.NOTSET:
    logger.setLevel(logging.WARNING)


LOCAL_TZ = time.tzname[time.localtime().tm_isdst]


def channel_to_identifier(channel):
    keys = channel.keys() & {'channelNumber', 'sourceType', 'stationId'}
    return {k: channel[k] for k in keys}


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
        self.tz = config.get('TT_TIVO_TZ', LOCAL_TZ)
        self.channels = {'c_num': {}, 'c_name': {}}
        try:
            with open('channels.json', 'rt') as cf:
                channel_data = json.load(cf)
        except FileNotFoundError:
            logger.warning('Channel Info Not Found, Downloading from TiVo...')
            with self.manager.mind() as m:
                channel_data = m.channel_search()
                with open('channels.json', 'wt') as cf:
                    json.dump(channel_data, cf)
        self.channels['c_num'] = {c['channelNumber']: c for c in channel_data if c['isReceived']}
        self.channels['c_name']= {c['name']: c for c in channel_data if c['isReceived']}

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
                    logger.debug('Result: {}'.format(str(r)))
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

    def do_cmd_whatson(self, msg):
        with self.manager.mind() as m:
            dates = utils.parse_date(msg.get('rec_time'))
            if not isinstance(dates, tuple):
                dates = (dates, dates + datetime.timedelta(days=1))
            start = arrow.get(dates[0], self.tz)
            end = arrow.get(dates[1], self.tz)
            f = api.SearchFilter()
            f.set_response_template([{"type": "responseTemplate",
                                      "typeName": "recording",
                                      "fieldName": ["title", "contentId", "scheduledStartTime"]}])
            recordings = m.recording_search(filt=f)
            result = [(r['title'], r['contentId']) for r in recordings if arrow.get(r['scheduledStartTime']) >= start and arrow.get(r['scheduledStartTime']) <= end]
            return {'cmd': msg['cmd'], 'status': 'SUCCESS', 'recordings': result, 'total_count': len(result)}

    def do_cmd_tellabout(self, msg):
        fields = ["title", "subtitle", "seasonNumber", "episodeNum", "description"]
        with self.manager.mind() as m:
            details = []
            for id in msg['content_ids']:
                f = api.SearchFilter()
                f.by_content_id(id)
                f.set_response_template([{"type": "responseTemplate",
                                          "typeName": "content",
                                          "fieldName": fields}])
                content = m.content_search(filt=f, limit=1)
                if len(content) > 0:
                    content = content[0]
                details.append({k: content.get(k, None) for k in fields})
            return {'cmd': msg['cmd'], 'status': 'SUCCESS', 'details': details, 'total_count': len(details)}

    def do_cmd_whenis(self, msg):
        with self.manager.mind() as m:
            f = api.SearchFilter()
            f.by_title(msg['title'])
            channel_params = {k: msg[k] for k in ('c_name', 'c_num') if msg[k] is not None}
            if channel_params:
                for k, v in channel_params.items():
                    options = self.channels[k].keys()
                    options = [o for o in options if self.channels[k][o]['isHdtv']]
                    match = process.extractOne(v, options)
                    logger.debug('Channel Match: {}'.format(str(match)))
                    f.by_station_id(self.channels[k][match[0]]['stationId'])
                    logger.debug("Using Channel: {}".format(self.channels[k][match[0]]['stationId']))
            start, end = utils.parse_date(msg['rec_time'])
            start = arrow.get(start, self.tz)
            end = arrow.get(end, self.tz)
            f.by_start_time(min_utc_time=start.to('UTC'), max_utc_time=end.to('UTC'))
            keep_fields = ("title", "subtitle", "contentId", "offerId", "startTime", "channel")
            offers = [{k: o[k] for k in keep_fields} for o in m.offer_search(filt=f, limit=10)]
            for o in offers:
                o['channel'] = o['channel']['name']
            return {'cmd': msg['cmd'], 'status': 'SUCCESS', 'offers': offers, 'total_count': len(offers)}


if __name__ == '__main__':
    import configparser

    cfg = configparser.ConfigParser()
    cfg.read('tivotalk.conf')
    config = cfg['General']

    logger.setLevel(logging.DEBUG)

    p = TiVoProxy(config=config)
    p.run()
