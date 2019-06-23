from django.shortcuts import render,redirect
from django.urls import reverse
from django_redis import get_redis_connection
from django.http import JsonResponse

from user.models import AddressInfo,UserInfo
from goods.models import GoodsSKU
from .models import OrderInfo,OrderGoods
import logging
# Create your views here.

logger = logging.getLogger('django_console')
def order(request):
    '''
    购物车进入订单界面
    :param request:
    :return:
    '''
    user_id = request.session.get('user_id')

    good_ids = request.POST.getlist('good_ids')
    logger.info('用户进入订单结算界面'+str(user_id)+str(len(good_ids))+'得的'+str(good_ids[0]))
    if len(good_ids) == 0:
        logger.info('没获取到商品id')
        return redirect(reverse('goods_namespace:index_url'))

    address = AddressInfo.objects.filter(uuser=user_id)

    cart_key = 'cart_'+str(user_id)
    conn = get_redis_connection('default')
    goods = []
    total_count = 0
    total_amount = 0
    for good_id in good_ids:
        logger.info('现在读取商品'+str(good_id))
        good = GoodsSKU.objects.get(id=int(good_id))
        count = int(conn.hget(cart_key,good_id))
        amount = good.price * count
        good.count = count
        good.amount = amount

        logger.info(str(good.count)+str(good.amount))
        goods.append(good)
        total_count += count
        total_amount += amount
    tran_pay = 0
    total_pay = total_amount + tran_pay
    context = {
        'address':address,
        'goods':goods,
        'good_ids':good_ids,
        'total_count':total_count,
        'total_amount':total_amount,
        'total_pay':total_pay,
        'tran_pay':tran_pay,
    }
    logger.info('返回订单数据')
    return render(request,'order/place_order.html',context)

from django.db import transaction
@transaction.atomic
def commit(request):
    '''
    提交订单
    :param request:
    :return:
    '''
    logger.info('开始提交订单')
    user_id = request.session.get('user_id')
    get = request.GET
    address_id = get.get('address_id')
    pay_method = get.get('pay_method')
    good_ids = get.get('good_ids')

    # 参数校验
    if not all([address_id, pay_method, good_ids]):
        return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

    # 校验地址id
    try:
        addr = AddressInfo.objects.get(id=address_id)
    except AddressInfo.DoesNotExist:
        return JsonResponse({'res': 2, 'errmsg': '地址信息错误'})

    # 校验支付方式
    if pay_method not in OrderInfo.PAY_METHODS.keys():
        return JsonResponse({'res': 3, 'errmsg': '非法的支付方式'})

    #生成订单信息
    from datetime import datetime
    order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user_id)

    tran_pay = 0

    total_count,total_amount = 0,0

    #####设置保存点
    sid = transaction.savepoint()

    try:
        #添加订单信息
        order = OrderInfo.objects.create(
            order_id=order_id,
            user=UserInfo.objects.get(id=user_id),
            address=addr,
            pay_method=pay_method,
            total_count=total_count,
            total_amount=total_amount,
            transit_amount=tran_pay
        )

        #向OrderGoods中添加数据
        conn = get_redis_connection('default')
        cart_key = 'cart_' + str(user_id)
        good_ids = eval(good_ids)
        print(good_ids, type(good_ids))

        for good_id in [int(i) for i in good_ids]:
            # good_id = int(good_id)
            logger.info('开始了'+str(good_id))
            try:
                good = GoodsSKU.objects.get(id=good_id)
            except GoodsSKU.DoesNotExist:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

            count = int(conn.hget(cart_key, good_id))

            #判断商品库存
            if count > good.stock:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

            #设置库存数量为版本记录点
            origin_stock = good.stock
            #跟新库存和销量
            new_stock = origin_stock - count
            good.sales += count

            res = GoodsSKU.objects.filter(id=good_id,stock=origin_stock).update(stock=new_stock)

            if res == 0:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res': 7, 'errmsg': '下单失败'})
            # 向df_order_goods中添加订单单个商品记录
            OrderGoods.objects.create(
                order=order,
                good=good,
                count=count,
                price=good.price
            )

            total_count += count
            total_amount += good.price*count

        logger.info('开始计算商品总额')
        order.total_count = total_count
        order.total_amount = total_amount
        order.save()
    except Exception as e:
        transaction.savepoint_rollback(sid)
        return JsonResponse({'res':7,'error':'下单失败'})

    conn.hdel(cart_key,*good_ids)

    logger.info('订单建立成功')
    return JsonResponse({'res': 5, 'errmsg': '订单创建成功'})