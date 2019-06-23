#coding=utf-8
'''
*************************
file:       dailyfresh_plus urls
author:     gongyi
date:       2019/6/7 15:24
****************************
change activity:
            2019/6/7 15:24
'''
from django.conf.urls import url
from .views import registerView,loginView,active,logout,info,order,siteView

urlpatterns = [
    url(r'^register$',registerView.as_view(),name='register_url'),
    url(r'^login$',loginView.as_view(),name='login_url'),
    url(r'logout/',logout,name='logout_url'),
    url(r'active/(?P<token>.*)',active,name='active_url'),
    url(r'info',info,name='info_url'),
    url(r'order/(?P<page>\d+)',order,name='order_url'),
    url(r'site',siteView.as_view(),name='site_url'),
]