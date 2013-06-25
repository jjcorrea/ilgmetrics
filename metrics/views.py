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

def prepare_cfd_query(snapshots, status, ignored_titles, end, tm_in):
    query ={'status':{'$in':settings.CFD_STATUS_MAP[status]}, 'title' : {'$nin': ignored_titles}, 'date_in' : {'$lt' : end}}
    if tm_in and tm_in <> 'ALL': query['team'] = tm_in
    return snapshots.find(query)

def prepare_story_metrics_query(snapshots, status, start, end, team):
    query = {'status':{'$in':status}, 'date_in' : {'$gt': start,'$lt' : end}}
    if team and team <> 'ALL': query['team'] = team
    return snapshots.find(query)

def generate_data_subranges(start, end):
    # gets the secs between END and START
    seconds_between_dates = (end-start).total_seconds()
    second_td_increment = seconds_between_dates / 5
    date_ranges = []
    
    d = start
    delta = datetime.timedelta(seconds=second_td_increment)
    while d <= end:
        #print d.strftime("%Y-%m-%d %H:%M:%S")
        date_ranges.append(d)
        d += delta
        
    return date_ranges

# VIEWS

def home_page(request):
    return render_to_response('home.html', {})

def cfd_chart_page(request):
    from trello import TrelloClient
    client = TrelloClient(settings.TRELLO_CREDENTIALS.get('api_key'), settings.TRELLO_CREDENTIALS.get('token'))
    graph_data = []
    
    st_in = ''
    en_in = ''
    tm_in = ''
    
    if request.method == 'POST':
        st_in = request.POST['start_datepick']
        en_in = request.POST['end_datepick']
        tm_in = request.POST['team']
        
        if st_in and en_in and tm_in: 
            with PyMongoClient() as mongo:
                snapshots = mongo.metrics.snapshots
                
                start = datetime.datetime.fromtimestamp(mktime(strptime(st_in, '%d/%m/%Y')))
                end = datetime.datetime.fromtimestamp(mktime(strptime(en_in, '%d/%m/%Y')))
                
                date_ranges = generate_data_subranges(start, end)
        
                # counter lists
                total_backlog_list = []
                total_in_progress_list = []
                total_done_list = []
        
                # seek for previous card status
                for idx, date in enumerate(date_ranges):
                    next_date_expected_index = idx+1
                    next_date_index = next_date_expected_index if len(date_ranges)>next_date_expected_index else len(date_ranges)-1
                    range_end = date_ranges[next_date_index]
                    
                    done_raw_rs = prepare_cfd_query(snapshots, 'DONE', [], range_end, tm_in)
                    in_progress_raw_rs = prepare_cfd_query(snapshots, 'IN_PROGRESS', [r['title'] for r in done_raw_rs], range_end, tm_in)
                    backlog_rs = prepare_cfd_query(snapshots, 'BACKLOG', [r['title'] for r in done_raw_rs] + [r['title'] for r in in_progress_raw_rs], range_end, tm_in)
        
                    total_backlog_list.append(backlog_rs.count())
                    total_in_progress_list.append(in_progress_raw_rs.count())
                    total_done_list.append(done_raw_rs.count())
                                
                graph_data = (total_backlog_list, total_in_progress_list, total_done_list, [d.strftime("%d/%m/%Y %H:%M") for d in date_ranges])
    
    posted_data = (st_in,en_in,tm_in)
    return render_to_response('cfd_chart.html', {'graph_data':graph_data, 'posted':posted_data}, context_instance=RequestContext(request))

def story_metrics_page(request):
    '''
    output_data = ''
    st_in = ''
    en_in = ''
    tm_in = ''
    
    if request.method == 'POST':
        st_in = request.POST['start_datepick']
        en_in = request.POST['end_datepick']
        tm_in = request.POST['team']
    
        if st_in and en_in and tm_in: 
            with PyMongoClient() as mongo:
                snapshots = mongo.metrics.snapshots
                start = datetime.datetime.fromtimestamp(mktime(strptime(st_in, '%d/%m/%Y')))
                end = datetime.datetime.fromtimestamp(mktime(strptime(en_in, '%d/%m/%Y')))
                    
                backlog_rs = prepare_story_metrics_query(snapshots, settings.CFD_STATUS_MAP['BACKLOG'], start, end, tm_in)
                in_progress_rs = prepare_story_metrics_query(snapshots, settings.CFD_STATUS_MAP['IN_PROGRESS'], start, end, tm_in)
                done_rs = prepare_story_metrics_query(snapshots, settings.CFD_STATUS_MAP['DONE'], start, end, tm_in)
                
                backlog = [set([b['title'] for b in backlog_rs])]
                in_progress = [set([b['title'] for b in in_progress_rs])]
                done = [set([b['title'] for b in done_rs])]
                
                output_data = (backlog, in_progress, done)
        
    posted_data = (st_in, en_in, tm_in)
    return render_to_response('story_metrics.html', {'metrics': output_data, 'posted':posted_data}, context_instance=RequestContext(request))
    '''
    with PyMongoClient() as mongo:
        snapshots = mongo.metrics.snapshots
        services = {'Search':0, 'Retrieve':0, 'Export':0, 'Ontology':0, 'Chemistry':0, 'Alert':0}
        
        for service in services.keys():
            res = snapshots.find({'services': {'$in':[service]}})
            services[service] = res.count()
            #print [r for r in res]
    
    return render_to_response('story_metrics.html', {'services_share': services}, context_instance=RequestContext(request))


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
 

    