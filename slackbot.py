#!/usr/bin/env python

import sys
sys.dont_write_bytecode = True

import sys
import time
import websocket

from slackclient import SlackClient
from bot import BotMixin
from util import dbg, load_config


class SlackBot(BotMixin):

    def __init__(self, token, config):
        self.last_ping = 0
        self.token = token
        self.bot_plugins = []
        self.slack_client = None
        self.plugin = 'slack'
        self.config = config
        self.relay_outs = []
        self.error_count = 0

        assert self.config

    def connect(self):
        """Convenience method that creates Server instance"""
        print('connect slack')
        self.slack_client = SlackClient(self.token)
        self.slack_client.rtm_connect()

    def init(self):
        self.load_plugins()
        self.connect()

    def process(self):
        try:
            replies = self.slack_client.rtm_read()
            self.error_count = 0
        except websocket.WebSocketConnectionClosedException:
            self.connect()
            return
        except Exception:
            self.error_count += 1
            if self.error_count > 5:
                self.connect()
            return

        for reply in replies:
            self.input(reply)
        self.crons()
        self.output()
        self.autoping()

    def input(self, data):
        data['config'] = self.config
        if "type" in data:
            function_name = "process_" + data["type"]
            dbg("got {}".format(function_name))
            for plugin in self.bot_plugins:
                plugin.register_jobs()
                plugin.do(function_name, data)

    def autoping(self):
        # hardcode the interval to 3 seconds
        now = int(time.time())
        if now > self.last_ping + 3:
            self.slack_client.server.ping()
            self.last_ping = now

    def send_item(self, data):
        output = data
        channel = self.slack_client.server.channels.find(output[0])
        if channel != None and output[1] != None:
            message = output[1].encode('ascii', 'ignore')
            print('slack<', channel, message)
            channel.send_message("{}".format(message))

    def relay(self, bot, relay_ins):
        prefix = (bot.name + '-') if bot.name else ''

        def channel_for(bot, channel):
            return 0, self.slack_client.server.channels.find('general')

            if bot.name:
                level, channel = 0, self.slack_client.server.channels.find(bot.name + '-' + item['channel'])
                if not channel:
                    level, channel = 1, self.slack_client.server.channels.find(bot.name)
            else:
                level, channel = 0, self.slack_client.server.channels.find(item['channel'])
            if not channel:
                level, channel = 2, self.slack_client.server.channels.find('slairck')
            if not channel:
                level, channel = 2, self.slack_client.server.channels.find('general')
            if not channel:
                level, channel = 2, self.slack_client.server.channels[0]
            return level, channel

        for item in relay_ins:
            if item['type'] == 'connected':
                """
                channels = self.slack_client.server.channels
                if self.config.get('TEST', False):
                    channels = [channels.find(prefix + 'slairck')]
                for channel in channels:
                    if channel.name.startswith(prefix):
                        self.relay_outs.append({'type': 'join', 'channel': channel.id})
                """
                self.relay_outs.append({'type': 'join', 'channel': 'talk42'})
            elif item['type'] == 'join' and item['user'] == self.config['irc']['nick']:
                level, channel = channel_for(bot, item['channel'])
                if level != 0:
                    self.slack_client.server.join_channel(prefix + item['channel'])
                channel.send_message(u'bot joinned to {}{}'.format(prefix, item['channel']))
            elif item['type'] == 'message':
                level, channel = channel_for(bot, item['channel'])
                try:
                    text = u'{}'.format(item['text'])
                except UnicodeDecodeError as e:
                    text = u'{}'.format(e)
                message = text
                username = item['user']
                message = u'<{}> {}'.format(item['user'], text)
                tag = {
                    0: '',
                    1: item['channel'] + ' ',
                    2: prefix + item['channel'] + ' ',
                }[level]
                #self.slack_client.api_call(
                #    'chat.postMessage',
                #    channel=item['channel'],
                #    text=message,
                #    username=username)
                channel.send_message(tag + message)
            elif item.get('debug', False):
                try:
                    if 0 <= int(item['type']) <= 999:
                        continue
                except ValueError:
                    pass
                if item['type'] in ['CONNECTED', 'PING', 'JOIN', 'PART', 'QUIT', 'MODE', 'KICK', 'BAN']:
                    continue
                channel = self.slack_client.server.channels.find('slairck-debug')
                if channel is not None:
                    channel.send_message(unicode(item))


if __name__ == "__main__":
    from util import main_loop

    config = load_config('slack')
    debug = config["DEBUG"]

    bot = SlackBot(config['slack']['token'], config)
    site_plugins = []
    files_currently_downloading = []
    job_hash = {}

    if 'DAEMON' in config:
        if config["DAEMON"]:
            import daemon
            with daemon.DaemonContext():
                main_loop(bot, config)
    main_loop(bot, config)
