#coding=utf-8
'''
*************************
file:       dailyfresh_plus tasks
author:     gongyi
date:       2019/5/27 18:15
****************************
change activity:
            2019/5/27 18:15
'''
from .celery import app
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
import logging


import os,sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'dailyfresh_plus.settings'

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner


logger = logging.getLogger('django_console')
#创建一个新celery类的实例对象

#创建发送邮件的任务
@app.task
def send_email_task(email_receiver,username,token):
    '''
    设置
    :return:
    '''
    msg = '<h1>{0},欢迎您注册为天天生鲜会员</h1>请点击下面的链接激活你的账户<br/><a href="http://192.168.78.134:8000/user/active/{1}">http://192.168.78.134:8000/user/active/{2}</a>'.format(username,token,token)
    status = send_mail(subject='天天生鲜账户激活',message='',from_email=settings.EMAIL_FROM,recipient_list=[email_receiver],html_message=msg)
    if status == 1:
        logger.info(username+'的激活邮件发送成功')
    else:
        logger.info('激活邮件发送失败')

#生成静态页面
@app.task
def createStaticIndex():
    '''
    产生首页静态页面。将这个静态页面缓存起来，再次访问时可以快速响应，避免每次都要从数据库中读取数据，渲染生成页面
    :return:
    '''
    logger.info('生成静态对象')
    print('开始生成静态对象')
    #获取商品种类信息
    types = GoodsType.objects.all()

    #获取首页展示商品信息
    goodsBanner = IndexGoodsBanner.objects.all().order_by('index')

    #获取首页促销活动信息
    promotion = IndexPromotionBanner.objects.all().order_by('index')

    #获取首页分类商品展示信息。同时给每个种类都加上图片和标题两个属性
    for type in types:
        image = IndexTypeGoodsBanner.objects.filter(type=type,display_type=1).order_by('index')
        title = IndexTypeGoodsBanner.objects.filter(type=type,display_type=0).order_by('index')

        type.image = image
        type.title = title

    context = {
        'types':types,
        'goods':goodsBanner,
        'promotion':promotion,
    }

    #使用模板
    temp = loader.get_template('static_index.html')
    static_index = temp.render(context)

    #生成首页对应的静态文件
    savePath = os.path.join(settings.BASE_DIR,'static/index.html')

    with open(savePath,'w') as f:
        f.write(static_index)