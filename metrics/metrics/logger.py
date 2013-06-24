#!/usr/bin/python

'''
A duummy Snapshot worker (for now)
'''

from time import mktime
from datetime import datetime
import time
import config
import re
import sys
from logging import *

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#The background is set with 40 plus the number of the color, and the foreground with 30

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

def formatter_message(message, use_color = True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message

COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}

class Logger(object):
    def __enter__(self):
        basicConfig(level=INFO)
        self.logger = getLogger(__name__)
        return self.logger
    
    def __exit__(self, type, value, traceback):
        ''' '''
