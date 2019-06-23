#coding=utf-8
'''
*************************
file:       dailyfresh_plus urls
author:     gongyi
date:       2019/6/16 21:58
****************************
change activity:
            2019/6/16 21:58
'''
from django.conf.urls import url
from .views import cart,add,edit,delete

urlpatterns = [
    url(r'^$',cart,name='cart_url'),
    url(r'^add/',add,name='add_url'),
    url(r'^edit/',edit,name='edit_url'),
    url(r'^delete/',delete,name='delete_url'),
]