import json

import datetime
import string
import random

import discord
from pymongo import MongoClient
from steem import Steem

with open('services.json') as file:
    config = json.load(file)
    discord_bot_token = config['discord']['reveal_token']
    posting_key = config['steemit']['posting_key']
    active_key = config['steemit']['active_key']
    connectionString = config['volentix_mongo']['connectionString']

client = discord.Client()
steem = Steem(keys=[posting_key, active_key])

mongo_client = MongoClient(connectionString)
db = mongo_client.get_default_database()
users_col = db['Users']


"""
    Handle message events
"""
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # If user typed $register
    if message.content.startswith('$register'):
        # get author_id | uniq
        author_id = message.author.id

        account = users_col.find_one({'DiscordAccountId': author_id})

        if account is not None:
            if account['SteemUserName'] is None:
                msg = 'Please send 0.001 Steem from your Steemit account to' \
                      ' @volentix with memo %s' % account['SteemMemo']
            else:
                msg = 'Your steemit account already linked'
            await client.send_message(message.author, msg)
        else:
            memo = '-'.join(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(9)) for _ in range(3))

            users_col.update(
                {
                    "DiscordAccountId": author_id
                },
                {
                    "$set":
                        {
                            "DiscordAccountId": author_id,
                            "SteemUserName": None,
                            "SteemMemo": memo,
                            'CreatedAt': datetime.datetime.now(),
                            "DiscordName": str(message.author)
                        }
                }, upsert=True
            )
            msg = 'Please send 0.001 Steem from your account to @volentix with memo %s' % memo
            await client.send_message(message.author, msg)


@client.event
async def on_ready():
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------')



client.run(discord_bot_token)
