import configparser

import arrow

import tivotalk.mind.rpc as rpc
import tivotalk.mind.api as api


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('test.conf')
    cert_pass = config['DEFAULT']['cert_password']
    address = config['DEFAULT']['address']
    mak = config['DEFAULT']['mak']
    sm = rpc.SocketMaker("cdata.pem", cert_pass)
    # cred = rpc.MRPCCredential.new_mak(mak=mak)
    cred = rpc.MRPCCredential.new_web(config['DEFAULT']['username'],
                                      config['DEFAULT']['password'],
                                      'Ada')
    session = rpc.MRPCSession(sm, address=address, credential=cred, debug=False)
    session.connect()
    mind = api.Mind(session)
    f = api.SearchFilter()
    f.by_title(title='big bang theory')
    midnight = arrow.get(arrow.now('US/Eastern').date(), 'US/Eastern').replace(days=1).to('UTC')
    f.by_end_time(min_utc_time=arrow.now('US/Eastern').to('UTC'), max_utc_time=midnight)
    offer_list = mind.offer_search(filt=f)
    offer = offer_list[0]
    print('{}: {}'.format(offer['title'], offer['startTime']))
    print('collectionId: {}'.format(offer['collectionId']))
    f = api.SearchFilter()
    f.by_collection_id(offer['collectionId'])
    collections = mind.collection_search(filt=f, limit=1)
    col = collections[0]
    print('{}'.format(col['description']))
    session.close()
