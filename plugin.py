#!/usr/bin/env python

import sys
sys.dont_write_bytecode = True

import sys
import time
import logging

from util import dbg

debug = True


class Plugin(object):
    CONFIG = {}

    def __init__(self, name, config=None):
        self.name = name
        self.jobs = []
        self.module = __import__(name)
        self.register_jobs()
        self.outputs = []
        if config is None:
            if name in self.CONFIG:
                config = self.CONFIG[name]
        if config:
            logging.info("config found for: " + name)
            self.module.config = config
        if 'setup' in dir(self.module):
            self.module.setup()

    def register_jobs(self):
        if 'crontable' in dir(self.module):
            for interval, function in self.module.crontable:
                self.jobs.append(
                    Job(interval, eval("self.module." + function)))
            logging.info(self.module.crontable)
            self.module.crontable = []
        else:
            self.module.crontable = []

    def do(self, function_name, *data):
        if function_name in dir(self.module):
            # this makes the plugin fail with stack trace in debug mode
            if not debug:
                try:
                    eval("self.module." + function_name)(*data)
                except:
                    dbg("problem in module {} {}".format(function_name, data))
            else:
                eval("self.module." + function_name)(*data)

        if "catch_all" in dir(self.module):
            try:
                self.module.catch_all(*data)
            except:
                dbg("problem in catch all")

    def do_jobs(self):
        for job in self.jobs:
            job.check()

    def do_output(self):
        items = []
        if 'outputs' in dir(self.module):
            if self.module.outputs:
                logging.info("output from {}".format(self.module))
                items += self.module.outputs
                self.module.outputs = []
        return items

    def do_relay_out(self):
        items = []
        if 'relay_outs' in dir(self.module):
            if self.module.relay_outs:
                logging.info("relay_out from {}".format(self.module))
                items += self.module.relay_outs
                self.module.relay_outs = []
        return items


class Job(object):

    def __init__(self, interval, function):
        self.function = function
        self.interval = interval
        self.lastrun = 0

    def __str__(self):
        return "{} {} {}".format(self.function, self.interval, self.lastrun)

    def __repr__(self):
        return self.__str__()

    def check(self):
        if self.lastrun + self.interval < time.time():
            if not debug:
                try:
                    self.function()
                except:
                    dbg("problem")
            else:
                self.function()
            self.lastrun = time.time()
            pass
