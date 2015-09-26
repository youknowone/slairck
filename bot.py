#!/usr/bin/env python

import sys
sys.dont_write_bytecode = True

import glob
import yaml
import json
import os
import sys
import time
import logging
from argparse import ArgumentParser

from slackclient import SlackClient
from plugin import Plugin, Job
from util import dbg


class BotMixin(object):
    
    
    def output(self):
        for plugin in self.bot_plugins:
            for output in plugin.do_output():
                self.send_item(output)
    
    def collect_relay(self):
        items = self.relay_outs
        self.relay_outs = []

        for plugin in self.bot_plugins:
            items += plugin.do_relay_out()
        
        return items

    def relay(self, bot, relay_ins):
        for data in relay_ins: 
            if "type" in data:
                function_name = "relay_" + data["type"]
                dbg("got {}".format(function_name))
                for plugin in self.bot_plugins:
                    plugin.register_jobs()
                    plugin.do(function_name, bot, data)

    def crons(self):
        for plugin in self.bot_plugins:
            plugin.do_jobs()

    def load_plugins(self):
        directory = os.path.dirname(sys.argv[0])
        if not directory.startswith('/'):
            directory = os.path.abspath(
                "{}/{}".format(os.getcwd(), directory))
        
        prefix = directory + '/' + self.plugin + '/'
        for plugin in glob.glob(prefix + '*'):
            sys.path.insert(0, plugin)
            sys.path.insert(0, prefix)
        for plugin in glob.glob(prefix + '*.py') + glob.glob(prefix + '*/*.py'):
            logging.info(plugin)
            name = plugin.split('/')[-1][:-3]
#            try:
            print('load plugin: {} {}'.format(self.__class__.__name__, name))
            self.bot_plugins.append(Plugin(name, self.config))
#            except:
#                print "error loading plugin %s" % name

