#!/usr/bin/env python

import sys
sys.dont_write_bytecode = True

import yaml
import sys
import time
import logging
from argparse import ArgumentParser

debug = True


def dbg(debug_string):
    if debug:
        logging.info(debug_string)


def main_loop(bot, config):
    if "LOGFILE" in config:
        logging.basicConfig(filename=config[
                            "LOGFILE"], level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        bot.init()
        while True:
            bot.process()
            time.sleep(.1)
    except ValueError:
        sys.exit(0)
    except:
        logging.exception('OOPS')


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        help='Full path to config file.',
        metavar='path'
    )
    return parser.parse_args()


def load_config(name='config'):
    args = parse_args()
    return yaml.load(open(args.config or name + '.yaml', 'r'))
