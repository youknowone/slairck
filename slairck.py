#!/usr/bin/env python

import sys
sys.dont_write_bytecode = True

import sys
import time
import logging

from util import load_config
from slackbot import SlackBot
from ircbot import IrcBot


def main_loop(bots, config):
    if "LOGFILE" in config:
        logging.basicConfig(filename=config[
                            "LOGFILE"], level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        for bot in bots:
            bot.init()
        while True:
            for bot in bots:
                # print 'processing', bot
                bot.process()
                relay_ins = bot.collect_relay()
                for xbot in bots:
                    if type(bot) == type(xbot):
                        continue
                    xbot.relay(bot, relay_ins)

            time.sleep(.2)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logging.exception(e)
        logging.exception('OOPS')


def run():
    while True:
        config = load_config('config')
        slackbot = SlackBot(config['slack']['token'], config)
        ircbot = IrcBot(config['irc']['host'], int(config['irc'].get('port', '6667')), config)

        if "DAEMON" in config:
            if config["DAEMON"]:
                import daemon
                with daemon.DaemonContext():
                    main_loop((slackbot, ircbot), config)
        main_loop((slackbot, ircbot), config)


if __name__ == "__main__":
    run()
