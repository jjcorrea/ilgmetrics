from django.conf.urls import patterns, include, url
from views.api import *
from views.gui import *
from views.poc import *
import settings 

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    #(r'^static/(?P.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    
    url(r'^$', 'metrics.views.gui.home_page', name='home'),
    
    url(r'^in_progress/$', 'metrics.views.gui.in_progress_page', name='in_progress'),
    url(r'^todo/$', 'metrics.views.gui.todo_page', name='todo'),
    url(r'^done/$', 'metrics.views.gui.done_page', name='done'),
    
    url(r'^cfd_chart/$', 'metrics.views.gui.cfd_chart_page', name='cfd_chart_page'),
    url(r'^dashboard/$', 'metrics.views.gui.dashboard', name='dashboard'),


    url(r'^api/snapshots/(?P<category>\w{0,50})/$', 'metrics.views.api.api_snapshots', name='api_snapshots'),
    
    url(r'^boards/$', 'metrics.views.poc.get_boards', name='boards'),
    url(r'^boards/(?P<board_id>\w+)/lists/$', 'metrics.views.poc.get_board_lists', name='lists'),
    url(r'^boards/(?P<board_id>\w+)/lists/(?P<list_id>\w+)/cards/$', 'metrics.views.poc.get_list_cards', name='cards'),
    url(r'^metrics/$', 'metrics.views.poc.get_metrics_data', name='metrics'),
    
)
