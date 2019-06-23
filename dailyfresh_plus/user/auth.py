#coding=utf-8
'''
*************************
file:       dailyfresh_plus auth
author:     gongyi
date:       2019/6/10 17:17
****************************
change activity:
            2019/6/10 17:17
'''
from django.shortcuts import redirect
def auth(func):
    '''
    装饰器函数，验证用户是否登录
    :param func:
    :return:
    '''
    def wrapper(request,*args,**kwargs):
        if 'user_id' in request.session:
            #如果存在session，说明已经登录了。回去继续执行原函数
            return func(request,*args,**kwargs)
        else:
            #说明未登录，重定向到登录界面，并将用户请求的url放入cookies中
            red = redirect('/user/login')
            red.set_cookie('url',request.get_full_path())
            return red
    return wrapper


