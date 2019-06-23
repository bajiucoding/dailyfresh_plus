#coding=utf-8
'''
*************************
file:       dailyfresh_plus urls
author:     gongyi
date:       2019/6/18 16:16
****************************
change activity:
            2019/6/18 16:16
'''
from django.conf.urls import url
from .views import order,commit

urlpatterns = [
    url(r'^place',order,name='place_url'),
    url(r'^commit',commit,name='commit_url'),
]