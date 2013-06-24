#!/usr/bin/python
from time import mktime
from datetime import datetime
import time
from pymongo import MongoClient

mif = "/Users/joelcorrea/Desktop/metrics_input.txt"

try:
   with open(mif): pass
except IOError:
   raise Exception('Loader file required! '+mif)
   
def parse_date(strdate):
	print "Trying to parse "+strdate
	if len(strdate)>8:
		return datetime.fromtimestamp(mktime(time.strptime(strdate, "%d/%m/%Y")))
	elif len(strdate)>0:
		return datetime.fromtimestamp(mktime(time.strptime(strdate, "%d/%m/%y")))
	else:
		return None

db = MongoClient().metrics

with open(mif, 'r') as inp:
	content = inp.readlines()
	for line in content:
		tokens = line.split('\t')
		data = {
			"id": tokens[0],  
			"start_date": parse_date(tokens[1]), 
			"end_date": parse_date(tokens[2]),
			"points" : tokens[4],
			"workstream": tokens[5],
			"design": tokens[6],
			"test_and_code": tokens[7],
			"deploy": tokens[8],
			"code_review": tokens[9],
			"block": tokens[10],
			"po_acceptance": tokens[11],
			"type" : tokens[13],
			"invalid_services_bug" : tokens[14],
		}
		db.data.insert(data)
