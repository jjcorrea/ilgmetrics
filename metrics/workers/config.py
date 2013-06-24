##### METRICS DAEMON CONFIGURATION

#https://trello.com/1/connect?key=5c212aec85d915429623d7dc30c7c412&name=Metrics&response_type=token&scope=read,write
TRELLO_CREDENTIALS = {
   'api_key' : '5c212aec85d915429623d7dc30c7c412',
   'token'   : '21cf8cce13ac934951aa361bf9719e70879e2f758130a6a4e9d9e27d8ba2e511',
}

MONGO_CONNECTION_STRING = 'mongodb://ilgdev:ilgdev@dharma.mongohq.com:10094/metrics'

# MAP OF BOARD IDs
TEAM_BOARD_MAP = {
    'SPARTA'    : '5102f07a4efe161902000122',
    'DRIVE'     : '5102f04185f40a934d00039c',
    'BARCELONA' : '4ff348ad23fc47565c6d6dee',
    'KOALA'     : '5102f0b20e830bf70100012a',
    #'JOHN_DEERE': '5000345d365ca9cb3839a143',
    'ICATU'     : '51221cf6f4ace0ef46006c40',
}

TRELLO_CARD_IGNORE = [
    'User Story Template',
    'Story template',
    'Bug Template'
]

SNAPSHOT_INTERVAL = 60 # min

# MAP OF ALL POSSIBLE SYNONYMS OF EACH STATUS
STATUS_MAP = {
    'BACKLOG':          ['backlog', 'week backlog', 'sprint backlog', 'mobile week backlog'],
    'BLOCKED':          ['blocked', 'blocked/waiting'],
    'FASTLANE':         ['fast lane', 'matheus lane'],
    'DESIGN':           ['design'],
    'DESIGN_REVIEW':    ['design review'],
    'BRIEFING':         ['briefing', 'story briefing'],
    'DEBRIEFING':       ['story debriefing', 'debriefing'],
    'READY':            ['ready'],
    'BUG_FIXING':       ['bug fixing'],
    'TEST_AND_CODE':    ['test and code', 'test & code'],
    'BUSINESS_REVIEW':  ['business review', 'alemao review'],
    'CODE_REVIEW':      ['code review'],
    'ACCEPTANCE':       ['acceptance', 'aceptance', 'previous week acceptances', 'last week acceptance'],
    'METRICS':          ['metrics', 'done pending statistics', 'done pending statistics (last week)'],
    'DONE':             ['done']
}

CFD_STATUS_MAP = {
    'BACKLOG'        : ['BACKLOG'],
    'IN_PROGRESS'    : ['IN_PROGRESS', 'BLOCKED', 'BUG_FIXING', 'FASTLANE', 'DESIGN', 'DESIGN_REVIEW', 
                        'BRIEFING', 'DEBRIEFING', 'READY', 'BUG_FIXING', 'TEST_AND_CODE', 'BUSINESS_REVIEW', 
                        'CODE_REVIEW'],
    'DONE'           : ['ACCEPTANCE', 'METRICS', 'DONE']
}



