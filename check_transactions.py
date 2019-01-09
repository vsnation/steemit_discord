import json

from pymongo import MongoClient
from steem import Steem

with open('../services.json') as file:
    config = json.load(file)
    posting_key = config['steemit']['posting_key']
    active_key = config['steemit']['active_key']
    connectionString = config['volentix_mongo']['connectionString']


mongo_client = MongoClient(connectionString)
db = mongo_client.get_default_database()
users_col = db['Users']

steem = Steem(keys=[posting_key, active_key])

unverified = list(users_col.find({'SteemUserName': None}))

history = steem.steemd.get_account_history('volentix', -100, 100)

# check history events
for _item in history:
    if 'transfer' in str(_item):
        # get steemit user
        steemit_user = _item[1]['op'][1]

        _is_memo_exists = users_col.find_one({'SteemMemo': steemit_user['memo'], 'SteemUserName': None}) is not None
        if _is_memo_exists:
            users_col.update(
                {'SteemMemo': steemit_user['memo']},
                {
                    "$set":
                        {
                            'SteemUserName': steemit_user['from']
                        }
                }
            )
            print('%s steemit account verified' % steemit_user['from'])
