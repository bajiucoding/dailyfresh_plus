from django.db import models

# Create your models here.

class AddressManager(models.Manager):
    '''
    自定义模型管理器
    '''
    def get_default_address(self,user):
        '''
        获取用户user的默认地址
        :param user:
        :return:
        '''
        try:
            address = self.model.objects.get(uuser=user,isDefault=True)
        except self.model.DoesNotExist:
            #该地址不存在
            address = None
        return address

class UserManager(models.Manager):
    '''
    自定义账户模型管理器
    '''
    def create_user(self,name,pwd,email):
        '''
        创建用户
        :param user:
        :param pwd:
        :param email:
        :return:
        '''
        new_user = UserInfo()
        new_user.uname = name
        new_user.upwd = pwd
        new_user.uemail = email
        new_user.save()

class UserInfo(models.Model):
    '''
    用户信息模型,uname,upwd,uemail,uactive,
    '''
    uname = models.CharField(verbose_name='用户名',max_length=20)
    upwd = models.CharField(verbose_name='密码',max_length=30)
    uemail = models.CharField(verbose_name='邮箱',max_length=40)
    uactive = models.BooleanField(verbose_name='是否激活',default=False)

    objects = UserManager()

    class Meta:
        db_table = 'user'
        verbose_name = '账户'
        verbose_name_plural = verbose_name

class AddressInfo(models.Model):
    '''
    用户收货地址模型,uuser,ureceiver,uaddress,ucode,uphone,uisDefault
    '''
    uuser = models.ForeignKey('UserInfo',verbose_name='所属账户',on_delete=models.CASCADE)
    ureceiver = models.CharField(verbose_name='收货人',max_length=10,default=None)
    uaddress = models.CharField(verbose_name='收货地址',max_length=300,default=None)
    ucode = models.CharField(verbose_name='邮编',max_length=6,default=None)
    uphone = models.CharField(verbose_name='手机号',max_length=11,default=None)
    isDefault = models.BooleanField(verbose_name='是否默认地址',default=False)
    isDelete = models.BooleanField(verbose_name='是否删除',default=False)

    objects = AddressManager()

    class Meta:
        db_table = 'address'
        verbose_name = '地址'   #便于理解的名字，下边是复数对象时
        verbose_name_plural = verbose_name



