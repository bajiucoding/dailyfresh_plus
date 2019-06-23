from django.shortcuts import render,redirect
from django.views.generic import View
from celery_task.tasks import send_email_task
from django.http import HttpResponse
from django.urls import reverse
from itsdangerous import TimedJSONWebSignatureSerializer as serializer
from itsdangerous import SignatureExpired
from django_redis import get_redis_connection
from django.core.paginator import Paginator
import re
import logging

from .models import UserInfo,AddressInfo
from dailyfresh_plus import settings
from .auth import auth


# Create your views here.

logger = logging.getLogger('django_console')

class registerView(View):
    '''
    封装注册相关操作的类
    '''
    def get(self,request):
        '''
        展示注册界面
        :param request:
        :return:
        '''
        logger.info('显示注册界面')
        return render(request,'user/register.html')

    def post(self,request):
        '''
        传递注册数据，完成注册操作
        :param request:
        :return:
        '''
        #接收post的数据
        post = request.POST
        uname = post.get('user_name')
        upwd = post.get('pwd')
        upwd1 = post.get('cpwd')
        uemail = post.get('email')
        allow = post.get('allow')

        #数据验证

        #验证是否非空
        if not all([uname,upwd,upwd1,uemail]):
            return render(request,reverse('user/register.html'),{'error_msg':'数据不可为空'})
        #验证用户名是否存在
        user = UserInfo.objects.filter(uname=uname)
        if user:
            return render(request,reverse('user/register.html'),{'error_msg':'用户名已存在'})
        #验证两次密码是否相等
        if not upwd == upwd1:
            return render(request,reverse('user/register.html'),{'error_msg':'两次密码需要一致'})
        #验证邮箱是否符合格式
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',uemail):
            return render(request,'user/register.html',{'error_msg':'邮箱格式不正确'})
        #验证是否勾选同意协议
        if allow != 'on':
           return render(request,reverse('user/register.html'),{'error_msg':'请勾选同意协议'})
        #调用模型管理器中定义的create_user方法
        logger.info(uname+'注册成功，开始保存用户信息')
        UserInfo.objects.create_user(uname,upwd,uemail)
        logger.info('保存用户信息成功')
        self.send(uname)
        # 返回应答，跳转到首页
        return redirect(reverse('goods:index_url'))

    def send(self,uname):
        '''
        定义发送邮件的函数，调用celery
        :param uname:
        :param uemail:
        :return:
        '''
        user = UserInfo.objects.filter(uname=uname)
        logger.info('开始发送激活邮件，当前用户'+uname+user[0].uemail)
        #发送激活邮件
        #创建对象，两个参数，分别为加密密钥和过期时间
        serial = serializer(settings.EMAIL_KEY,3600)
        #要加密的信息
        info = {'confirm':user[0].id}
        #进行加密，token为加密结果，是bytes数据。用decode将其转换为utf-8数据
        token = serial.dumps(info).decode('utf-8')

        #发送激活邮件
        send_email_task.delay(user[0].uemail,uname,token)
        logger.info('已发送邮件'+str(token))


def active(request,token):
    if request.method == 'GET':
        logger.info('开始进行激活操作,获得的token是'+str(token))
        key = serializer(settings.EMAIL_KEY,3600)
        logger.info('生成解密key')
        try:
            #根据key从签名内容中解析出原本的信息，即在注册中定义的字典
            info = key.loads(token)
            logger.info('激活用户id是'+str(info['confirm']))
            #从字典中获取用户id
            user_id = info['confirm']
            #根据id获取用户信息,修改激活字段并保存
            user = UserInfo.objects.filter(id=user_id).update(uactive=True)
            # user.uactive = True
            # user[0].save()
            logger.info('已经完成激活操作')
            return redirect('/user/login')
            #return redirect(reverse('user_namespace:login_url'))
        except SignatureExpired:
            return HttpResponse('激活链接已过期')

class loginView(View):
    '''
    登录视图
    '''
    def get(self,request):
        '''
        显示登录界面
        :param request:
        :return:
        '''
        if 'username' in request.COOKIES:
            #先判断下，如果有cookies存在，直接从cookies中读取username，
            username = request.COOKIES.get('username')
            logger.info('开始返回登录界面，有cookies')
        else:
            username = ''
            logger.info('开始返回登录界面，没有cookies')
        #这里返回值，就是默认不管有没有cookies，这个界面都会默认勾选上checked
        context = {'username':username,'checked':"checked"}
        return render(request,'user/login.html',context)

    def post(self,request):
        '''
        登录操作
        :param rerquest:
        :return:
        '''
        post = request.POST
        name = post.get('username')
        pwd = post.get('pwd')
        remember = post.get('remember')
        logger.info('开始进行登录验证')
        user = UserInfo.objects.filter(uname=name)
        if user.count() == 1:
            #说明该用户名存在
            if not user[0].uactive:
                #调用在注册类中定义的send函数发送激活邮件
                registerView().send(user[0].uname)
                return render(request,'user/login.html',{'error_msg':'当前账号未激活，已自动为您发送激活邮件，请去邮箱激活'})

            if pwd == user[0].upwd:
                #保存session
                request.session['user_name'] = name
                request.session['user_id'] = user[0].id
                request.session.set_expiry(0)
                logger.info('保存session成功')
                response = redirect('user/login.html')
                if remember != 'on':
                    #未勾选记住用户名，删除这个cookie
                    response.delete_cookie('user_name')
                    logger.info('不保存用户名，删除cookie')
                else:
                    #勾选了记住用户名，保存cookie
                    response.set_cookie('user_name',name)
                    logger.info('登录且保存用户名成功'+name)
                return redirect(reverse('goods_namespace:index_url'))
            else:
                return render(request,'user/login.html',{'name':name,'pwd':pwd,'error_msg':'密码错误'})
        else:
            return render(request, 'user/login.html', {'name': name, 'pwd': pwd, 'error_msg': '用户名不存在'})

def logout(request):
    '''
    注销当前用户的方法
    :param request:
    :return:
    '''
    logger.info('当前用户'+request.session['user_name']+'退出登录')
    del request.session['user_id']
    del request.session['user_name']
    return redirect('/')

@auth
def info(request):
    '''
    展示用户信息界面
    :param request:
    :return:info页面，姓名、联系方式、地址
    '''
    logger.info('调用info方法，进入用户信息中心界面')
    id = request.session.get('user_id')
    name = request.session['user_name']

    logger.info('开始获取浏览历史记录')
    user_id = request.session['user_id']
    conn = get_redis_connection('default')
    history_key = 'history_' + str(user_id)
    historys = conn.lrange(history_key, 0, 4)
    if len(historys) == 0:
        pages = None
    goods = []
    for good_id in historys:
        # 遍历获得商品信息
        from goods.models import GoodsSKU
        good = GoodsSKU.objects.filter(id=good_id)[0]
        goods.append(good)

    #根据id获取其收货地址相关信息
    addressObj = AddressInfo.objects.get_default_address(id)
    # phone = addressObj.uphone
    # address = addressObj.uaddress
    context = {
        'title':'info',
        'name':name,
        'address':addressObj,
        'goods':goods
    }
    return render(request,'user/user_center_info.html',context)

@auth
def order(request,page):
    '''
    用户订单界面。要读取用户订单信息
    :param request:
    :param page：当前显示页数
    :return:
    '''
    logger.info('进入order界面')
    user_id = request.session['user_id']
    from order.models import OrderInfo,OrderGoods
    #获得订单信息
    orders = OrderInfo.objects.filter(user_id=user_id)
    #遍历订单数据，再根据订单获得具体商品数据
    for order in orders:
        logger.info('取出当前订单'+str(order.order_id))
        ordergoods = OrderGoods.objects.filter(order_id=order.order_id)
        logger.info('当前订单对应商品表长度'+str(len(ordergoods)))
        for ordergood in ordergoods:
            #对应订单商品表
            amount = ordergood.price * ordergood.count
            ordergood.amount = amount

        order.status = OrderInfo.ORDER_STATUS[order.order_status]
        # logger.info('附加商品'+str(ordergoods[0].order_id)+str(ordergoods[0].good.name)+str(ordergoods[0].count))
        order.ordergoods = ordergoods
        print(type(order.ordergoods),'  sssss  ',len(order.ordergoods))
        # print()
        logger.info('给order附加属性'+str(order.ordergoods[0].good.name))
    # 分页
    paginator = Paginator(orders, 4)

    # 获取第page页的内容
    try:
        page = int(page)
    except Exception as e:
        page = 1

    if page > paginator.num_pages:
        page = 1

    # 获取第page页的Page实例对象
    order_page_obj = paginator.page(page)

    # 进行页码的控制，页面上最多显示5个页码
    # 1.总页数小于5页，页面上显示所有页码
    # 2.如果当前页是前3页，显示1-5页
    # 3.如果当前页是后3页，显示后5页
    # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
    num_pages = paginator.num_pages
    if num_pages < 5:
        pages = range(1, num_pages + 1)
    elif page <= 3:
        pages = range(1, 6)
    elif num_pages - page <= 2:
        pages = range(num_pages - 4, num_pages + 1)
    else:
        pages = range(page - 2, page + 3)

    context = {
        'title': 'order',                   #页面名称，可以不要
        'order_page_obj':order_page_obj,            #页面元素实例，将订单数据分给几个页面后，这是当前页面，
        'page':pages,                       #页码数
        'orders':orders,                    #订单集合，是一个列表，包含很多对象
    }
    return render(request,'user/user_center_order.html',context)


class siteView(View):
    '''
    用户收货地址界面，可以进行修改。需要传递数据修改时，就用到get和post了
    :param request:
    :return:
    '''

    @staticmethod
    @auth
    def get(request):
        '''
        get方法，接收get请求，返回当前页面和当前用户信息
        :param request:
        :return:
        '''
        logger.info('开始执行site类中的get方法'+str(request.session.get('user_id')))
        userAddress = AddressInfo.objects.get_default_address(request.session.get('user_id'))#这里直接得到一个objects类型
        context = {
            'title': 'site',
            'userAddress':userAddress,
        }
        return render(request,'user/user_center_site.html',context)

    @staticmethod
    @auth
    def post(request):
        '''
        post方法，修改用户收货地址
        :param request:
        :return:
        '''
        post = request.POST
        user = request.user
        user1 = UserInfo.objects.filter(id=request.session['user_id'])[0]
        logger.info('开始执行site类中的post方法'+str(request.session.get('user_id'))+str(type(user)))
        userAddress = AddressInfo.objects.get_default_address(request.session.get('user_id'))  # 这里直接得到一个objects类型
        #接收前端界面post的数据
        receiver = post.get('receiver')
        address = post.get('address')
        code = post.get('code')
        phone = post.get('phone')
        isdefault = post.get('isdefault',0)

        #数据完整性校验
        if not all([receiver,address,code,phone]):
            logger.info('传入数据有空值')
            return render(request,'user/user_center_site.html',{'error_msg':'数据不能为空'})
        if userAddress and isdefault:
            #有默认地址，而且还将这个设定为默认，就将之前的修改为非默认
            userAddress.isDefault = False
            userAddress.save()
            isdefault = True
        if not userAddress:
            #如果没有默认地址，这个自动设为默认
            isdefault = True
        if not isdefault:
            #这种情况是有默认地址，且这个不是默认，就转化即可
            isdefault = False
        logger.info('下边开始保存地址'+str(isdefault)+str(user.id))
        AddressInfo.objects.create(uuser=user1,ureceiver=receiver,uaddress = address,ucode = code,uphone = phone,isDefault=isdefault)
        # userAddress.ureceiver = receiver
        # userAddress.uaddress = address
        # userAddress.ucode = code
        # userAddress.uphone = phone
        # if isdefault == 1:
        #     userAddress.isDefault = True
        # #向数据库中写入数据
        # userAddress.save()
        context = {
            'title': 'site',
            'userAddress': userAddress,
        }
        return render(request,'user/user_center_site.html',context)


