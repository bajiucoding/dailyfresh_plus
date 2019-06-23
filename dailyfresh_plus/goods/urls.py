#coding=utf-8
'''
*************************
file:       dailyfresh_plus urls
author:     gongyi
date:       2019/6/10 16:16
****************************
change activity:
            2019/6/10 16:16
'''
from django.conf.urls import url
from . import views

urlpatterns=[
    url(r'^$',views.index,name='index_url'),
    url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)',views.list,name='list_url'),
    url(r'^detail/(\d+)$',views.detail,name='detail_url'),
]