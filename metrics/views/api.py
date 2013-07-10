from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.template import RequestContext
from metrics.mongo.client import *
import datetime
from time import mktime, strptime
import time
from metrics.utils import *
from metrics.models import *
import metrics.settings
from bson.code import Code
from shared import *
import re

BAD_REQUEST = HttpResponse('BAD REQUEST', status=400)


#
# SHARED
#

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


def find_unique_stories(snapshots, global_status, ignored_titles=[], end=None, tm_in=None):
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

#
# API
#
def _api_joinstmap(st):
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
    print regex
    return regex

def _api_prepare_stories_output(snapshots, snapshots_reduced, team, global_status):
    json = {}
    status = global_status
    
    query = {'_id':{'$regex':team},'value':{'$regex':re.compile(_api_joinstmap(global_status))}}
    team_stories = snapshots_reduced.find(query)
    
    # generates a list of LASTSTATUS and TITLE
    title_and_last_status_list = [(story['_id'].replace(team+'#', ''), extract_last_status(global_status, story['value'])) for story in team_stories]
    
    # GET the id list of all the specific SNAPSHOTs
    ids = []
    for title, status in title_and_last_status_list:
        res = next(snapshots.find({'title':title, 'status':status}), None)
        if res: 
            #print('[%s][%s][%s] %s' % (team, status, res['_id'], title))
            ids.append(res['_id'])
        
    json[global_status] = [build_story_output(story) for story in snapshots.find({'_id':{'$in':ids}}).sort([('date_in', -1)])]

    return json     

def api_remove_global_status(story_id, global_status):
    with PyMongoClient() as mongo:
        print 'Removing story STATUS: %s' % story_id
        snapshots = mongo.metrics.snapshots
        snapshots.remove({'card_id':story_id, 'status': {'$in':settings.CFD_STATUS_MAP[global_status]}})
        
def api_remove_story(story_id):
    with PyMongoClient() as mongo:
        print 'Removing STORY: %s' % story_id
        snapshots = mongo.metrics.snapshots
        snapshots.remove({'card_id':story_id})

def api_snapshots(request, category):
    category = category.lower()
    json = {}
    
    if (request.method == 'POST') or (not category): return BAD_REQUEST
    
    with PyMongoClient() as mongo:
        snapshots = mongo.metrics.snapshots
        snapshots_reduced = mongo.metrics.snapshots_reduced_story_statuses
        
        if category == 'teams':
            json['teams'] = [team for team in snapshots.distinct('team')]
        elif category == 'stories':    
            if (not request.GET.has_key('team')) or (not request.GET.has_key('global_status')): return BAD_REQUEST
            team = request.GET['team'].upper()
            global_status = request.GET['global_status'].upper()
            json = _api_prepare_stories_output(snapshots, snapshots_reduced, team, global_status)

        elif category == 'remove':    
            if (not request.GET.has_key('story')): return BAD_REQUEST
            
            story = request.GET['story']
            
            if request.GET.has_key('global_status'):
                status = request.GET['global_status']
                api_remove_status(story, status)
            else:
                api_remove_story(story)
            
    return HttpResponse(simplejson.dumps(json), content_type="application/json")
