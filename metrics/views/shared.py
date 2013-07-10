
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