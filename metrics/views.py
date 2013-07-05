from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.template import RequestContext
from trello_api.miner import *
from mongo.client import *
import datetime
from time import mktime, strptime
import time
from utils import *
from models import *
from bson.code import Code
import re

BAD_REQUEST = HttpResponse('BAD REQUEST', status=400)

#
# API
#

def extract_last_status(global_status, status_group):
    status_list = status_group.split("#")
    all_substatus = settings.CFD_STATUS_MAP[global_status]
    
    for story_status in reversed(status_list):
         if story_status in all_substatus:
             print 'will return [%s]' % (story_status)
             return story_status
         
def build_story_output(story):
    return {'team':story['team'], 'date': story['date_in'].strftime("%d/%m/%Y %H:%M"), 'status': story['status'] , 'title':story['title'], 'services':eval(story['services'])}

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
    print regex
    return regex

def prepare_api_stories_output(snapshots, snapshots_reduced, team, global_status):
    json = {}
    status = global_status
    
    query = {'_id':{'$regex':team},'value':{'$regex':re.compile(joinstmap(global_status))}}
    
    print query
    
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
            json = prepare_api_stories_output(snapshots, snapshots_reduced, team, global_status)
            
    return HttpResponse(simplejson.dumps(json), content_type="application/json")

#
# VIEWS
#


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


def home_page(request):
    #response_data = {}
    return render_to_response('home.html')

def in_progress_page(request):
    return render_to_response('in_progress.html', {}, context_instance=RequestContext(request))

def todo_page(request):
    return render_to_response('todo.html', {}, context_instance=RequestContext(request))


def done_page(request):
    return render_to_response('done.html', {}, context_instance=RequestContext(request))


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


#
# POC trello requests
#
def get_boards(request):
    json = {}
    
    with TrelloWrapper() as trello_client:
        boards = trello_client.list_boards()
        json.update({'boards' : [{'id': b.id, 'name': b.name} for b in boards]})
    
    return HttpResponse(simplejson.dumps(json), content_type="application/json")

def get_board_lists(request, board_id):
    json = {}
    
    with TrelloWrapper() as trello_client:
        lists = trello_client.get_board(board_id).all_lists()
        json.update({'lists' : [{'id': b.id, 'name': b.name} for b in lists]})
    
    return HttpResponse(simplejson.dumps(json), content_type="application/json")

def get_list_cards(request, board_id, list_id):
    json = {}
    
    with TrelloWrapper() as trello_client:
        cards = trello_client.get_list(list_id).list_cards()
        json.update({'cards' : [{'id': b.id, 'labels':get_single_card(b.id).labels, 'desc': get_single_card(b.id).desc} for b in cards]})
    
    return HttpResponse(simplejson.dumps(json), content_type="application/json")
    
def get_single_card(id):
    with TrelloWrapperExtendedDesc() as trello_client:
        return trello_client.get_card(id)

def get_metrics_data(request):
    json = {}
    
    with PyMongoClient() as mongo:
        metrics = mongo.metrics.data
        
        for metric in metrics.find():
            json.update({'metrics' : [metric.get('id') for metric in metrics.find()]})
    
    return HttpResponse(simplejson.dumps(json), content_type="application/json")
 

    