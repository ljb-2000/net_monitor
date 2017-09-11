# coding=utf-8

from django.conf.urls import patterns,url
from yw_monitor.views import *

urlpatterns = patterns('yw_monitor.views',
    url(r'^list/$', monitor_list, name='monitor_list'),
    url(r'^monitor/add/$', monitor_add, name='monitor_add'),
    url(r'^monitor/del/$', monitor_delete, name='monitor_delete'),
    url(r'^monitor/detail/(\w+)/$', monitor_detail, name='monitor_detail'),
    url(r'^monitor/edit/$', monitor_edit, name='monitor_edit'),
    url(r'^picture/(?P<picture_name>[\w.]+)/$', picture, name='picture'),
    url(r'^group_list/$', monitor_group_list, name='monitor_group_list'),
    url(r'^group_detail/$', monitor_group_detail, name='monitor_group_detail'),
)
