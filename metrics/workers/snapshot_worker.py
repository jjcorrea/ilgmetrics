#!/usr/bin/python

'''
A duummy Snapshot worker (for now)
'''

from time import mktime
from datetime import datetime
import time
from pymongo import MongoClient
from trello import TrelloClient
from trollop import TrelloConnection
import config
import re
from time import sleep
import sys
from utils import *
from logger import *
from bson.code import Code

class SnapshotWorker(object):
    def __init__(self):
        ''' '''

    def get_single_card(self, id):
        return self.trello_extended_connection.get_card(id)

    def is_status_updated(self, story, title, current_status):
        story_statuses_ordered = self.db.snapshots.find({'story' : story, 'title' : title}).sort([('date_in', -1)])
        if story_statuses_ordered.count()>0:
            last_db_reg = story_statuses_ordered[0]
            last_db_status = last_db_reg.get('status')
            last_db_dt = last_db_reg.get('date_in')
            return last_db_status != current_status
        return True

    def __enter__(self):
        self.trello_extended_connection = TrelloConnection(config.TRELLO_CREDENTIALS.get('api_key'), config.TRELLO_CREDENTIALS.get('token'))
        self.client = TrelloClient(config.TRELLO_CREDENTIALS.get('api_key'), config.TRELLO_CREDENTIALS.get('token'))
        self.db = MongoClient(config.MONGO_CONNECTION_STRING).metrics
        return self
    
    def __exit__(self, type, value, traceback):
        self.trello_extended_connection = None
        self.client = None
        self.db = None

while True:
    try:
        with SnapshotWorker() as worker, Logger() as logger:
            for (team, board) in config.TEAM_BOARD_MAP.iteritems():
                logger.info("["+now()+"] PREPARING "+team+" SNAPSHOT")
                
                board_lists = worker.client.get_board(board).all_lists()
                board_stories = []
                
                for list in board_lists:
                    cards = list.list_cards()
                    status = map_status(extract_string_brackets(list.name))
                    
                    logger.info("[%s][%s] %s" % (team, status, extract_string_brackets(list.name)))
                    
                    if status is not None:
                        for card in cards:
                            card_extended = worker.get_single_card(card.id)
                            title = clean_story_title(card.name)
                            
                            logger.info("[%s][%s] %s" % (team, status, title))
                            
                            if title in board_stories: 
                                logger.error('[%s][%s] DUPLICATION - Card [%s] exists more than once in a single board. Will ignore this.' % (team, status, title))
                                continue
                            else: board_stories.append(title)
                                
                            if (title.lower() not in config.TRELLO_CARD_IGNORE):
                                story = str(extract_task_identifier(card_extended.desc))
                                
                                if worker.is_status_updated(story, title, status): 
                                    mongo_in = {
                                        'card_id':card.id,
                                        'card_url': card_extended.url,
                                        'date_in': datetime.now(),
                                        'story' : story,
                                        'title' : title,
                                        'status' : status,
                                        'points' : extract_story_points(card.name),
                                        'team' : team,
                                        'services' : str([extract_string_brackets(label['name']) for label in card_extended.labels])
                                    }
                                    
                                    logger.info('[%s] status for story (%s) ' % (team, status))
                                    worker.db.snapshots.insert(mongo_in)

                # REDUCED STORY STATUSES 
                logger.info("["+now()+"] RUNNING MAP-REDUCES...")
                map = Code("function(){ emit(this.team+'#'+this.title, this.status); }")
                reduce = Code("function(id, statuses){ var status_str = ''; for(var i = 0; i < statuses.length; i++){ status_str += statuses[i]+'#'; } return status_str  }")
                worker.db.snapshots.map_reduce(map, reduce, 'snapshots_reduced_story_statuses')                                    
        
                logger.info("["+now()+"] FINISHED TEAM PROCESSING.")
    except:
        pass
    
    logger.info("["+now()+"] WILL SLEEP %s SECONDS" % (config.SNAPSHOT_INTERVAL))
    sleep(config.SNAPSHOT_INTERVAL)        
        
