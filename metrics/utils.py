#!/usr/bin/python

'''
A duummy Snapshot worker (for now)
'''

from time import mktime
import datetime
import time
import settings
import re
import sys

def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError: return ""

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
def extract_string_brackets(inp): 
    return re.sub('\[[^>]*\](\s)?', '', inp)

def extract_string_parenthesis(inp):
    return re.sub('\([^>]*\)(\s)?', '', inp)

def extract_task_identifier(inp):
    return find_between(inp, '[Jira](', ')').split("/")[-1]

def extract_story_points(inp):
    return find_between(inp, '(', ')')

def clean_story_title(inp):
    return extract_string_brackets(extract_string_parenthesis(inp)).strip()
    
def map_status(inp):
    for k, v in settings.STATUS_MAP.iteritems():
        if inp.strip().upper() in map(str.upper, v): return k
    return None
