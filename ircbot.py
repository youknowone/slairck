#!/usr/bin/env python

import sys
sys.dont_write_bytecode = True

import re
import time

from ircclient.struct import Message
from ircclient.client import DispatchClient as IrcClient

from bot import BotMixin
from util import dbg, load_config


def log_send(s):
    print('irc<', s,)


def convert_message(message):
    try:
        import html  # py3
        message = html.unescape(message)
    except ImportError:
        pass
    message = re.sub(r'<([A-Za-z0-9]+:[^>]+)>', r'\1', message)
    message = re.sub(r'<#[A-Z0-9]+\|([^>]+)>', r'#\1', message)
    message = message.replace('\r', ' ').replace('\n', r' ')
    return message


class IrcBot(BotMixin):
    def __init__(self, host, port, config):
        self.name = config.get('name', None)
        self.last_ping = 0
        self.bot_plugins = []
        self.irc_client = None
        self.addr = (host, port)
        self.plugin = 'irc'
        self.config = config
        self.relay_outs = []
        assert self.config

    def connect(self):
        """Convenience method that creates Server instance"""
        print('connect irc', self.addr)
        self.irc_client = IrcClient(self.addr, blocking=False)
        self.irc_client.socket.send_callback = log_send
        self.irc_client.connect()

    def init(self):
        self.connect()
        self.load_plugins()

    def process(self):
        self.irc_client.runloop_unit()
        while True:
            message = self.irc_client.dispatch(raw=True)
            if message:
                self.input(message)
            self.crons()
            self.output()
            # self.autoping()
            if not self.irc_client.dispatchable():
                break
        time.sleep(0.1)

    def input(self, data):
        data = Message(data)
        data.config = self.config
        function_name = "process_" + str(data.type).lower()
        dbg("got {}".format(function_name))
        for plugin in self.bot_plugins:
            plugin.register_jobs()
            plugin.do(function_name, data)

    def autoping(self):
        # hardcode the interval to 3 seconds
        now = int(time.time())
        if now > self.last_ping + 30:
            self.irc_client.send_line('ping :dontkillme')
            self.last_ping = now

    def send_item(self, data):
        self.irc_client(data)
        time.sleep(.2)

    def relay(self, bot, relay_ins):
        def channel_for(channel_id):
            return bot.slack_client.server.channels.find(channel_id)

        def name(channel):
            if self.name:
                if not channel.name.startswith(self.name):
                    return None
                return channel.name.split('-', 1)[1]
            else:
                return channel.name

        for data in relay_ins:
            if 'channel' in data:
                channel = channel_for(data['channel'])
                if channel is None:
                    continue

            if data['type'] == 'join':
                line = u'join #{}'.format(name(channel))
                self.irc_client.send_line(line)
            elif data['type'] == 'message':
                print('do?', data)
                message = data.get('text', '')
                message = convert_message(message)
                user_id = data.get('user', None)
                if user_id:
                    user = bot.slack_client.server.users.find(user_id)
                else:
                    user = None
                user  # usable, but not yet
                if message:
                    if self.config.get('mode') == 'relay':
                        line = u'privmsg #{} :<{}> {}'.format(name(channel), user.name if user else user_id, message)
                    else:  # mode proxy
                        line = u'privmsg #{} :{}'.format(name(channel), message)
                    self.irc_client.send_line(line)
            else:
                line = u'privmsg #{} :{}'.format(self.config['irc'].get('nick', 'slairck'), unicode(data))
                self.irc_client.send_line(line)

if __name__ == "__main__":
    from util import main_loop

    config = load_config('irc')
    debug = config["DEBUG"]
    host = config['irc']['host']
    port = config['irc'].get('port', 6667)
    bot = IrcBot(host, port, config=config)
    site_plugins = []
    files_currently_downloading = []
    job_hash = {}

    if config.get('DAEMON', None):
        import daemon
        with daemon.DaemonContext():
            main_loop(bot, config)
    main_loop(bot, config)
