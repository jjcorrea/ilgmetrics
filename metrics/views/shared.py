import datetime
from time import mktime, strptime
from metrics import settings
from metrics.mongo.client import *
import re
import random
    
#
# SHARED
#

def joinstmap(st):
    unwanted_statuses = []
    if st == 'BACKLOG':
         unwanted_statuses = ['IN_PROGRESS', 'DONE']
    elif st == 'IN_PROGRESS':
         unwanted_statuses = ['DONE']
    elif st == 'DONE':
         unwanted_statuses = []
         
    ignored_statuses = []
    if len(unwanted_statuses)>0: 
        for ost in unwanted_statuses:ignored_statuses += settings.CFD_STATUS_MAP[ost] 
    
    # 1-WANTED, 2-UNWANTED (not used if DONE)
    regex = len(unwanted_statuses)>0 and '^(?=.*(%s))(?!.*(%s)).*' % ('|'.join(settings.CFD_STATUS_MAP[st]), '|'.join(ignored_statuses)) or '^(?=.*(%s)).*' % ('|'.join(settings.CFD_STATUS_MAP[st]))  
    return regex


def prepare_stories_output(snapshots, snapshots_reduced, team, global_status):
    json = {}
    status = global_status
    
    query = {'_id':{'$regex':team},'value':{'$regex':re.compile(joinstmap(global_status))}}
    team_stories = snapshots_reduced.find(query)
    
    # generates a list of LASTSTATUS and TITLE
    title_and_last_status_list = [(story['_id'].replace(team+'#', ''), extract_last_status(global_status, story['value'])) for story in team_stories]
    
    # GET the id list of all the specific SNAPSHOTs
    ids = []
    for title, status in title_and_last_status_list:
        res = next(snapshots.find({'title':title, 'status':status}), None)
        if res: 
            print('[%s][%s][%s] %s' % (team, status, res['_id'], title))
            ids.append(res['_id'])
        
    json['documents'] = [build_story_output(story) for story in snapshots.find({'_id':{'$in':ids}}).sort([('date_in', -1)])]

    return json     


def extract_last_status(global_status, status_group):
    status_list = status_group.split("#")
    all_substatus = settings.CFD_STATUS_MAP[global_status]
    
    for story_status in reversed(status_list):
         if story_status in all_substatus:
             print 'will return [%s]' % (story_status)
             return story_status

def build_story_output(story):
    response = {'team':story['team'], 'date': story['date_in'].strftime("%d/%m/%Y %H:%M"), 'status': story['status'] , 'title':story['title'], 'services':eval(story['services'])}
    
    if story.has_key('card_id'):
        response['card_id'] = story['card_id']
    
    return response


def find_unique_stories(global_status, ignored_titles=[], end=None, tm_in=None):
    with PyMongoClient() as mongo:
        snapshots = mongo.metrics.snapshots
        query ={'status':{'$in':settings.CFD_STATUS_MAP[global_status]}}
        if tm_in and tm_in <> 'ALL': query['team'] = tm_in
        if end: query['date_in'] = {'$lt':end}
        if len(ignored_titles)>0: query['title'] = {'$nin': ignored_titles}
        return snapshots.find(query).distinct('title')    

def prepare_story_metrics_query(snapshots, status, start, end, team):
    query = {'status':{'$in':status}, 'date_in' : {'$gt': start,'$lt' : end}}
    if team and team <> 'ALL': query['team'] = team
    return snapshots.find(query)

def generate_data_subranges(start, end, tracking_points):
    seconds_between_dates = (end-start).total_seconds()
    second_td_increment = seconds_between_dates / tracking_points
    date_ranges = []
    
    d = start
    delta = datetime.timedelta(seconds=second_td_increment)
    while d <= end:
        #print d.strftime("%Y-%m-%d %H:%M:%S")
        date_ranges.append(d)
        d += delta
        
    return date_ranges

# MAP REDUCE
from bson.code import Code

def _map(js):
    map = Code("function(){ %s }" % (js))
    return map
    
def _reduce(js):
    reduce = Code("function(key, value){ %s }" % (js_reduce))
    return reduce

def snapshots_map_reduce(uid, js_map, js_reduce):
    db = MongoClient(settings.MONGO_CONNECTION_STRING).metrics
    worker.db.snapshots.map_reduce(_map(js), _reduce(js), uid)                                    

# GRID OPERATIONS

def gdata(team_regex, status, story_points):
    #TODO start filtering by true story_points
    #query = {'team':{'$regex':team_regex}, 'status':status}
    #return snapshots.find(query).count()
    return '%.2f' % random.uniform(0.1, 10.10)

def build_grid(team_regex, points, statuses):
    result = []
    for point in points:
        row = [point]
        for status in statuses:
            row.append(gdata(team_regex, status, point))
        result.append(row)
    return result

