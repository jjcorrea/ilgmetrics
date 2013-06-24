from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', 'metrics.views.home_page', name='home'),
    
    url(r'^cfd_chart/$', 'metrics.views.cfd_chart_page', name='cfd_chart_page'),
    url(r'^story_metrics/$', 'metrics.views.story_metrics_page', name='story_metrics_page'),
    
    url(r'^boards/$', 'metrics.views.get_boards', name='boards'),
    url(r'^boards/(?P<board_id>\w+)/lists/$', 'metrics.views.get_board_lists', name='lists'),
    url(r'^boards/(?P<board_id>\w+)/lists/(?P<list_id>\w+)/cards/$', 'metrics.views.get_list_cards', name='cards'),
    url(r'^metrics/$', 'metrics.views.get_metrics_data', name='metrics'),
    
)
