from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.template import RequestContext
from metrics.trello_api.miner import *
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
# GUI
#
def home_page(request):
    #response_data = {}
    return render_to_response('home.html')

def in_progress_page(request):
    return render_to_response('kanban/in_progress.html', {}, context_instance=RequestContext(request))

def todo_page(request):
    return render_to_response('kanban/todo.html', {}, context_instance=RequestContext(request))


def done_page(request):
    return render_to_response('kanban/done.html', {}, context_instance=RequestContext(request))


def cfd_chart_page(request):
    graph_data = []
    
    st_in = ''
    en_in = ''
    tm_in = ''
    tp_in = ''
    
    if request.method == 'POST':
        st_in = request.POST['start_datepick']
        en_in = request.POST['end_datepick']
        tm_in = request.POST['team']
        tp_in = request.POST['tracking_points']
        
        with PyMongoClient() as mongo:
            snapshots = mongo.metrics.snapshots

            if (not st_in) or (not en_in):
                today = datetime.datetime.today()
                start = datetime.datetime(today.year, today.month, today.day)
                end = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
            else:
                start = datetime.datetime.fromtimestamp(mktime(strptime(st_in, '%d/%m/%Y')))
                end = datetime.datetime.fromtimestamp(mktime(strptime(en_in, '%d/%m/%Y')))
            
            if not tp_in:
                tp_in = 5 
            else:
                tp_in = int(tp_in)
                
            date_ranges = generate_data_subranges(start, end, tp_in)
    
            # counter lists
            total_backlog_list = []
            total_in_progress_list = []
            total_done_list = []
    
            # seek for previous card status
            for idx, date in enumerate(date_ranges):
                next_date_expected_index = idx+1
                next_date_index = next_date_expected_index if len(date_ranges)>next_date_expected_index else len(date_ranges)-1
                range_end = date_ranges[next_date_index]
                
                done_raw_rs = find_unique_stories(snapshots, 'DONE', [], range_end, tm_in)
                in_progress_raw_rs = find_unique_stories(snapshots, 'IN_PROGRESS', done_raw_rs, range_end, tm_in)
                backlog_rs = find_unique_stories(snapshots, 'BACKLOG', done_raw_rs + in_progress_raw_rs, range_end, tm_in)
    
                total_backlog_list.append(len(backlog_rs))
                total_in_progress_list.append(len(in_progress_raw_rs))
                total_done_list.append(len(done_raw_rs))
                            
            graph_data = (total_backlog_list, total_in_progress_list, total_done_list, [d.strftime("%d/%m/%Y %H:%M") for d in date_ranges])

    posted_data = (st_in,en_in,tm_in,tp_in)
    return render_to_response('cfd_chart.html', {'graph_data':graph_data, 'posted':posted_data}, context_instance=RequestContext(request))

def story_metrics_page(request):
    with PyMongoClient() as mongo:
        snapshots = mongo.metrics.snapshots

        # workstream share
        workstream_share = {'Search':0, 'Retrieve':0, 'Export':0, 'Ontology':0, 'Chemistry':0, 'Alert':0}
        for service in workstream_share.keys():
            res = snapshots.find({'services': {'$regex' : service}}).distinct('title')
            workstream_share[service] = len(res)
        
    return render_to_response('story_metrics.html', {'workstream_share': workstream_share}, context_instance=RequestContext(request))

    