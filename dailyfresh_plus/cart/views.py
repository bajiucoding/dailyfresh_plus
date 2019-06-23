from django.shortcuts import render

from user.auth import auth
from django.http import JsonResponse
from django_redis import get_redis_connection

from goods.models import GoodsSKU

import logging
# Create your views here.

logger = logging.getLogger('django_console')

@auth
def cart(request):
    '''
    购物车界面显示。需要返回购物车商品种类数量cart_count、购物车内商品GoodsSKU（名称、图片、单位、价格）购买数量num
    :param request:
    :return:
    '''
    user_id = request.session['user_id']
    logger.info('获取购物车信息'+str(user_id))
    conn = get_redis_connection('default')
    cart_key = 'cart_' + str(user_id)
    cart_count = 0
    for i in conn.hkeys(cart_key):
        logger.info(str(type(i))+str(conn.hget(cart_key,i))+'值'+str(type(conn.hget(cart_key,i))))
        cart_count += int(conn.hget(cart_key,i))
    #获得cart内部所有商品记录
    cart_dict = conn.hgetall(cart_key)
    logger.info('共'+str(conn.hlen(cart_key))+'件商品')
    goods = []
    total_count,total_amount = 0,0
    for good_id,num in cart_dict.items():
        num = int(num)
        good = GoodsSKU.objects.filter(id=good_id)[0]
        amount = good.price * num
        #为商品附加两个额外属性 即购买数量num，小计amount
        good.amount = amount
        good.num = num

        goods.append(good)

        total_count += num
        total_amount += amount
    context = {
        'goods':goods,
        'total_count':total_count,
        'total_amount':total_amount,
        'cart_count':cart_count,
    }
    return render(request,'cart/cart.html',context)

@auth
def add(request):
    '''
    购物车中增加商品
    :param reqeust:
    :return:
    '''
    id = request.GET.get('id')
    num = int(request.GET.get('num'))
    logger.info('向购物车中增加商品'+str(id)+str(num))
    #参数校验
    if not all([id,num]):
        return JsonResponse({'response':1,'error':'参数不完整'})

    try:
        good = GoodsSKU.objects.get(id=id)
    except GoodsSKU.DoesNotExist:
        return JsonResponse({'response':2,'error':'商品信息错误'})

    #购物车记录添加
    conn = get_redis_connection('default')
    cart_key = 'cart_'+str(request.session.get('user_id'))
    #获得cart_key这个哈希表中这个商品的数量
    cart_count = conn.hget(cart_key,id)
    if cart_count:
        #如果这个商品存在，直接更新value
        num += int(cart_count)

    if num > good.stock:
        #超过库存
        return JsonResponse({'response':3,'error':'商品库存不足，只有'+str(good.stock)})
    #更新购物车中这个商品的数量
    conn.hset(cart_key,id,num)
    #获得购物车中商品件数
    cart_count = 0
    for i in conn.hkeys(cart_key):
        logger.info(str(type(i)) + str(conn.hget(cart_key, i)) + '值' + str(type(conn.hget(cart_key, i))))
        cart_count += int(conn.hget(cart_key, i))
    logger.info('添加成功'+str(cart_count))

    return JsonResponse({'response':5,'cart_count':cart_count,'error':'添加购物车记录成功'})

@auth
def edit(request):
    '''
    修改购物车中商品数量
    :param request:
    :return:
    '''
    logger.info('修改购物车数量')
    user_id = request.session.get('user_id')
    id = request.GET.get('id')
    num = int(request.GET.get('num'))

    if not all([id,num]):
        return JsonResponse({'res':1,'error':'参数不完整'})

    try:
        good = GoodsSKU.objects.get(id=id)
    except:
        return JsonResponse({'res':2,'error':'商品id不正确'})

    if num > good.stock:
        logger.info('数量超过库存')
        return JsonResponse({'res':3,'error':'数量已超过库存,现有库存'+str(good.stock)+'件'})

    conn = get_redis_connection('default')
    cart_key = 'cart_' + str(user_id)
    #更新购物车数量
    conn.hset(cart_key,id,num)
    cart_count = 0
    for i in conn.hkeys(cart_key):
        cart_count += int(conn.hget(cart_key, i))
    logger.info('修改购物车数量成功'+str(user_id)+str(id)+str(num)+'现在购物车'+str(cart_count))
    return JsonResponse({'res':4,'error':'修改成功','cart_count':cart_count})

@auth
def delete(request):
    '''
    删除商品
    :param request:
    :return:
    '''
    user_id = request.session.get('user_id')
    logger.info('购物车中删除')
    id = request.GET.get('id')
    if not all([id]):
        return JsonResponse({'res':1,'error':'参数不完整'})

    try:
        good = GoodsSKU.objects.get(id=id)
    except:
        return JsonResponse({'res':2,'error':'商品id不正确'})

    conn = get_redis_connection('default')
    cart_key = 'cart_'+str(user_id)
    conn.hdel(cart_key,id)
    logger.info('删除成功')
    cart_count = 0
    for i in conn.hkeys(cart_key):
        cart_count += int(conn.hget(cart_key, i))
    logger.info('购物车数量'+str(cart_count))
    return JsonResponse({'res':3,'error':'删除成功','cart_count':cart_count})
def order(request):
    '''
    订单
    :param request:
    :return:
    '''