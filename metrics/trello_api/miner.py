#from trello import *
from trollop import TrelloConnection
from trello import *
from django.conf import settings

'''
TODO:

From Trello
1- Extract info from card description (Start, End, Test and Code, Real bug, JIRA code) -->Design, Test & Code, Deploy, Code Review, Block, PO Acceptance
2- Extract workstream from card labels 
3- 


'''

class TrelloWrapperExtendedDesc(object):
    ''' A usefull trello mining tool  '''
    
    def __init__(self):
        ''' '''
    # Used in with stmts    
    def __enter__(self):
        self.client = TrelloConnection(settings.TRELLO_CREDENTIALS.get('api_key'), settings.TRELLO_CREDENTIALS.get('token'))
        return self.client

    def __exit__(self, type, value, traceback):
        '''self.client.logout()'''  
    
    
class TrelloWrapper(object):
    ''' A usefull trello mining tool  '''
    
    def __init__(self):
        ''' '''
    # Used in with stmts    
    def __enter__(self):
        self.client = TrelloClient(settings.TRELLO_CREDENTIALS.get('api_key'), settings.TRELLO_CREDENTIALS.get('token'))
        return self.client

    def __exit__(self, type, value, traceback):
        self.client.logout()  
        