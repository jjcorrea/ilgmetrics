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
# GUI STUFF
#
def home_page(request):
    #response_data = {}
    return render_to_response('home.html')

def _kanban_search(request, status):
    kanban_search_results = {'state':'default'}
    
    if request.method == 'GET':
        st_in = request.GET['sdt'] if request.GET.has_key('sdt') else None
        en_in = request.GET['edt'] if request.GET.has_key('edt') else None
        tm_in = request.GET['team'] if request.GET.has_key('team') else None
        comp_st_in = request.GET['compare_sdt'] if request.GET.has_key('compare_sdt') else None
        comp_en_in = request.GET['compare_edt'] if request.GET.has_key('compare_edt') else None 
        comp_tm_in = request.GET['compare_team'] if request.GET.has_key('compare_team') else None
        
        if tm_in and tm_in.lower() == 'all': tm_in = 'SPARTA|KOALA|BARCELONA|DRIVE'
        
        if not all(x is None for x in [st_in, en_in, tm_in, comp_st_in, comp_en_in, comp_tm_in]):
            with PyMongoClient() as mongo:
                snapshots = mongo.metrics.snapshots
                snapshots_reduced = mongo.metrics.snapshots_reduced_story_statuses
                kanban_search_results = prepare_stories_output(snapshots, snapshots_reduced, tm_in, status)
                
                statuses = ['DESIGN','TEST_AND_CODE','CODE_REVIEW','BLOCKED','ACCEPTANCE']
                kanban_search_results['story_grid'] = build_grid(tm_in, [0.5,1,2,3,5,8,13,20,40,100], statuses)
                kanban_search_results['bug_grid'] = build_grid(tm_in, [0.5,1,2,3,5,8,13,20,40,100], statuses)

            if not all(x is None for x in [comp_st_in, comp_en_in, comp_tm_in]):
                kanban_search_results['state'] = 'comparison'
            else:
                kanban_search_results['state'] = 'search'
        
    kanban_search_results['sdt'] = st_in
    kanban_search_results['edt'] = en_in
    kanban_search_results['team'] = tm_in
    kanban_search_results['csdt'] = comp_st_in
    kanban_search_results['cedt'] = comp_en_in
    kanban_search_results['cteam'] = comp_tm_in
    kanban_search_results['members'] = TeamMember.objects.filter(team=Team.objects.filter(team_name=tm_in))
    
    return kanban_search_results

def todo_page(request):
    return render_to_response('kanban/todo.html', {'search_results':_kanban_search(request, 'BACKLOG')}, context_instance=RequestContext(request))

def in_progress_page(request):
    return render_to_response('kanban/in_progress.html', {'search_results':_kanban_search(request, 'IN_PROGRESS')}, context_instance=RequestContext(request))

def done_page(request):
    return render_to_response('kanban/done.html', {'search_results':_kanban_search(request, 'DONE')}, context_instance=RequestContext(request))

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
                
                done_raw_rs = find_unique_stories('DONE', [], range_end, tm_in)
                in_progress_raw_rs = find_unique_stories('IN_PROGRESS', done_raw_rs, range_end, tm_in)
                backlog_rs = find_unique_stories('BACKLOG', done_raw_rs + in_progress_raw_rs, range_end, tm_in)
    
                total_backlog_list.append(len(backlog_rs))
                total_in_progress_list.append(len(in_progress_raw_rs))
                total_done_list.append(len(done_raw_rs))
                            
            graph_data = (total_backlog_list, total_in_progress_list, total_done_list, [d.strftime("%d/%m/%Y %H:%M") for d in date_ranges])

    posted_data = (st_in,en_in,tm_in,tp_in)
    return render_to_response('cfd_chart.html', {'graph_data':graph_data, 'posted':posted_data}, context_instance=RequestContext(request))

def dashboard(request):
    global_metrics = {}
    
    with PyMongoClient() as mongo:
        snapshots = mongo.metrics.snapshots

        # workstream share
        workstream_share = {'Search':0, 'Retrieve':0, 'Export':0, 'Ontology':0, 'Chemistry':0, 'Alert':0}
        for service in workstream_share.keys():
            res = snapshots.find({'services': {'$regex' : service}}).distinct('title')
            workstream_share[service] = len(res)
    
    statuses = ['DESIGN','TEST_AND_CODE','CODE_REVIEW','BLOCKED','ACCEPTANCE']
    global_metrics['story_grid'] = build_grid('SPARTA|KOALA|BARCELONA|DRIVE', [0.5,1,2,3,5,8,13,20,40,100], statuses)
    global_metrics['bug_grid'] = build_grid('SPARTA|KOALA|BARCELONA|DRIVE', [0.5,1,2,3,5,8,13,20,40,100], statuses)
        
    return render_to_response('story_metrics.html', {'workstream_share': workstream_share, 'global_metrics':global_metrics}, context_instance=RequestContext(request))

    