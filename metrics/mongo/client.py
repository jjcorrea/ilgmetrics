#from trello import *
from pymongo import MongoClient
from django.conf import settings

'''
TODO:


'''
class PyMongoClient(object):
    ''' A usefull mongo client wrapper  '''
    
    def __init__(self):
        ''' '''
        
    def __enter__(self):
        self.client = MongoClient(settings.MONGO_CONNECTION_STRING)
        return self.client

    def __exit__(self, type, value, traceback):
        '''self.client.logout()'''  
        