from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.template import RequestContext
from metrics.trello_api.miner import *
from metrics.mongo.client import *
import datetime
from time import mktime, strptime
import time

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
 

    