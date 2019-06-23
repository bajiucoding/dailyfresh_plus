from django.shortcuts import render,redirect
from django.urls import reverse
from django.core.cache import cache
from django.core.paginator import Paginator
from django_redis import get_redis_connection

from .models import GoodsType,GoodsImage,GoodsInfo,GoodsSKU,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner
import logging
# Create your views here.

logger = logging.getLogger('django_console')
def index(request):
    '''
    首页
    :param request:
    :return:
    '''
    logger.info('开始调用index方法')
    #尝试从缓存中获取网页数据
    context = cache.get('index_page_data')
    if context is None:
        #没有缓存时就先设置缓存
        logger.info('开始设置缓存')
        #获取商品种类信息
        types = GoodsType.objects.all()

        #获取首页展示商品信息
        goodsBanner = IndexGoodsBanner.objects.all().order_by('index')

        #获取首页促销活动信息
        promotionBanner = IndexPromotionBanner.objects.all().order_by('index')

        #获取首页展示商品分类信息
        for type in types:
            #获取商品信息，display_type决定是图片还是标题文字
            imageBanner = IndexTypeGoodsBanner.objects.filter(type=type,display_type=1).order_by('index')
            titleBanner = IndexTypeGoodsBanner.objects.filter(type=type,display_type=0).order_by('index')

            #动态给type添加属性，分别是图片和标题
            type.imagebanner = imageBanner
            type.titlebanner = titleBanner
        logger.info('获取信息完毕'+str(goodsBanner.count()))
        context = {
            'types':types,
            'goodsBanner':goodsBanner,
            'promotion':promotionBanner,
        }
        #设置缓存，有效期是1小时
        cache.set('index_page_data',context,60*60)
    else:
        logger.info('有缓存')
        #return HttpResponse('没有')
    #获取用户购物车商品数目
    cart_count = 0
    if request.session.has_key('user_id'):
        #用户已登录
        conn = get_redis_connection('default')
        cart_key = 'cart_'+str(request.session.get('user_id'))
        for i in conn.hkeys(cart_key):
            cart_count += int(conn.hget(cart_key, i))
    context['cart_count'] = cart_count
    return render(request,'goods/index.html',context)


def list(request,type_id,page):
    '''
    商品列表页
    :param request: 
    :param type_id:商品种类id
    :param page:页码
    :return: 
    '''
    logger.info('开始调用list方法，接收两个参数'+str(type_id)+str(page))
    try:
        type = GoodsType.objects.get(id=type_id)
    except GoodsType.DoesNotExist:
        #该种类id不存在时，直接返回首页
        return redirect(reverse('goods_namespace:index_url'))
    #获取商品分类信息
    types = GoodsType.objects.all()
    #获取商品排序规则 default默认id排序，price价格排序，sales销量排序
    sort = request.GET.get('sort')

    if sort == 'price':
        skus = GoodsSKU.objects.filter(type=type).order_by('price')
    elif sort == 'sales':
        #根据销量降序排列
        skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
    else:
        sort = 'default'
        skus = GoodsSKU.objects.filter(type=type).order_by('id')

    paginator = Paginator(skus,2)  #分页，每页有5个元素

    try:
        page = int(page)
    except Exception as e:
        page = 1

    if page > paginator.num_pages:
        #页数超过了
        page = 1

    #获取第page页的实例对象
    page_obj = paginator.page(page)
    #新品
    new = GoodsSKU.objects.filter(type=type).order_by('-id')[:2]

    #分页处理。分页之后多余5页，只显示5页，小于5页，显示全部。
    num_pages = paginator.num_pages
    if num_pages < 5:
        #总页数小于5页，就显示全部
        page_num = range(1,num_pages + 1)
    elif page <= 3:
        #当前页码小于3，就显示前5页
        page_num = range(1,6)
    elif num_pages - page <= 2:
        #当前页码属于最后3页
        page_num = range(num_pages - 4,num_pages - 1)
    else:
        page_num = range(page - 2,page + 3)
    #获取购物车数量，先不写
    cart_count = 0
    if request.session.has_key('user_id'):
        #用户已登录
        user_id = request.session.get('user_id')
        conn = get_redis_connection('default')
        cart_key = 'cart_'+str(user_id)
        for i in conn.hkeys(cart_key):
            cart_count += int(conn.hget(cart_key, i))

    context = {
        'type':type,              #该类商品
        'types':types,            #所有商品种类
        'pages':page_obj,         #每页元素集合
        'pageNum':page_num,       #当前页码
        'new':new,                #新产品
        'sort':sort,              #排序规则
        'cart_count':cart_count,  #购物车
    }

    return render(request,'goods/list.html',context)

def detail(request,id):
    '''
    商品详情展示
    :param request:
    :param id:商品skuid
    :return:当前商品信息、
    '''
    logger.info('进入商品详情界面,当前商品id'+str(id))


    #获取商品信息
    try:
        good = GoodsSKU.objects.get(id=id)
    except GoodsSKU.DoesNotExist:
        #商品不存在就返回首页
        return redirect(reverse('goods_namespace:index_url'))
    logger.info('已经获得商品信息'+str(good.id)+str(good.name)+str(good.type_id))
    #获取商品分类
    type = GoodsType.objects.get(id=good.type_id)
    #获取同种类新品信息
    new = GoodsSKU.objects.filter(type=good.type_id).order_by('-id')[:2]
    #new1 = good.type.order_by('-id')[:2]
    logger.info('获取商品信息完毕，新品'+str(new[0].name)+str(type.id))

    context = {
        'type':type,
        'new':new,
        'good':good
    }
    cart_count = 0
    if request.session.has_key('user_id'):
        #如果用户登录了
        # 添加浏览记录
        conn = get_redis_connection('default')
        user_id = request.session.get('user_id')
        #购物车数量返回
        cart_key = 'cart_' + str(user_id)
        cart_count = 0
        for i in conn.hkeys(cart_key):
            cart_count += int(conn.hget(cart_key, i))

        # 用户浏览记录命名：history_用户id
        history = 'history_' + str(user_id)
        # 如果history中有当前商品，移除。否则不管
        conn.lrem(history, 0, id)  # lrem方法，第二个参数为0，在history中删除所有值为id的元素，
        # 在左侧添加元素
        conn.lpush(history, id)
        # 截断，使之长度为5
        conn.ltrim(history, 0, 4)
    context['cart_count'] = cart_count
    return render(request,'goods/detail.html',context)


