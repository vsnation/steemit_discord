import json

import datetime
import string
import random

import discord
import re
from pymongo import MongoClient
from steem import Steem

with open('services.json') as file:
    config = json.load(file)
    discord_bot_token = config['discord']['reveal_token']
    posting_key = config['steemit']['posting_key']
    active_key = config['steemit']['active_key']
    connectionString = config['volentix_mongo']['connectionString']



class CommandHandler:

    def __init__(self, discord_client):
        self.client = discord_client
        self.steem = Steem(
            keys=[posting_key, active_key]
        )


    """
        Handle message events
    """

    async def command_handler(self, message, args):
        account = users_col.find_one({'DiscordAccountId': message.author.id})
        self.check_account(account, message=message)

        if args[0] == 'steemit':
            await self.steemit_register(account, message)
        elif args[0] == 'vtx':
            await self.vtx_register(account, message)
        elif args[0] == 'telegram':
            await self.telegram_register(account, message)


    def vtx_register(self, account, message):
        if account['VTXAddress'] is None:
            vtx_address = re.search(EOS_REGEX, message.content)
            if vtx_address is not None:
                vtx_address = vtx_address.group(0)
                users_col.update(
                    account,
                    {
                        "$set":
                            {
                                "VTXAddress": vtx_address
                            }
                    }
                )
                msg = '*You have successfully linked the VTX address.*\n%s' % vtx_address
            else:
                msg = 'We could not find the VTX address in the request, please repeat again using command\n**$register vtx {VTX_ADDRESS}**'

            return self.client.send_message(message.author, msg)

    def telegram_register(self, account, message):
        if account['TelegramUserId'] is None:
            msg = 'Please open this [link](<https://t.me/%s?start=%s>) and push *start* to link your telegram account\n' \
                  'Or send command below to [@%s](<https://t.me/%s?start=%s>) in Telegram\n' \
                  '```/link %s```' % (
                TELEGRAM_PROJECT_BOT, account['TelegramMemo'],
                TELEGRAM_PROJECT_BOT, TELEGRAM_PROJECT_BOT,
                account['TelegramMemo'], account['TelegramMemo'])
            e = discord.Embed(color=0x7289da)
            e.add_field(name='Link your telegram account',
                        value=msg,
                        inline=True)
            return self.client.send_message(message.author, embed=e)
        else:
            msg = 'Your telegram account has already linked!'
            return self.client.send_message(message.author, msg)




    def steemit_register(self, account, message):

        if account['SteemUserName'] is None:
            msg = 'Please send 0.001 Steem from your Steemit account to' \
                  ' %s with memo %s' % (STEEM_PROJECT_ACCOUNT, account['SteemMemo'])
        else:
            msg = 'Your steemit account has already linked!'
        return self.client.send_message(message.author, msg)




    def check_account(self, account, message):
        if account is None:
            steem_memo = self.generate_memo()
            telegram_memo = self.generate_telegram_memo()
            users_col.update(
                {
                    "DiscordAccountId": message.author.id
                },
                {
                    "$set":
                        {
                            "DiscordAccountId": message.author.id,
                            "DiscordMemo": None,
                            "DiscordName": str(message.author),
                            "SteemUserName": None,
                            "SteemMemo": steem_memo,
                            "TelegramMemo": telegram_memo,
                            "TelegramUserId": None,
                            "VTXAddress": None,
                            'CreatedAt': datetime.datetime.now(),
                            "TokenBalance": 0
                        }
                }, upsert=True
            )


    """
        Generate memo to link account
    """
    def generate_memo(self):
        difficulty = 3
        symbols_count = 9
        memo = '-'.join(''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in
            range(symbols_count)) for _ in range(difficulty))
        return memo


    """
        Generate telegram memo
    """
    def generate_telegram_memo(self):
        symbols_count = 9
        memo = ''.join(
            random.choice(string.ascii_uppercase + string.digits) for _ in
            range(symbols_count))
        return memo



# Discord init
client = discord.Client()

# create the CommandHandler object and pass it the client
ch = CommandHandler(client)

# Mongo init
mongo_client = MongoClient(connectionString)
db = mongo_client.get_default_database()
users_col = db['Users']

#
STEEM_PROJECT_ACCOUNT = '@volentix'
TELEGRAM_PROJECT_BOT = 'test_bounty_bot'
EOS_REGEX = r'EOS[A-HJ-NP-Za-km-z1-9]{50}'

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$register'):
        try:
            args = message.content.split(' ')[1:]
            if len(args) == 0:
                msg = '*You have entered an incorrect command*\n' \
                      '**Commands:**\n' \
                      '$register steemit - link steemit account\n' \
                      '$register telegram - link telegram account\n' \
                      '$register vtx {VTX_ADDRESS} - link VTX public address'
                await client.send_message(message.author, msg)
            else:
                await ch.command_handler(message, args)
        except Exception as e:
            print(e)





@client.event
async def on_ready():
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------')



client.run(discord_bot_token)
