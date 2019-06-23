from django.contrib import admin
from django.core.cache import cache
from .models import GoodsType,GoodsSKU,GoodsInfo,IndexTypeGoodsBanner,IndexPromotionBanner,IndexGoodsBanner
from celery_task.tasks import createStaticIndex
# Register your models here.

class baseModel(admin.ModelAdmin):
    def save_model(self,request,obj,form,change):
        '''
        新增数据时使用
        :param request:
        :param obj:
        :param form:
        :param change:
        :return:
        '''
        super().save(request,obj,form,change)

        #celery重新生成静态首页
        createStaticIndex.delay()
        #清除首页的缓存数据
        cache.delete('index_page_data')

    def delete_model(self,request,obj):
        '''
        删除数据时调用
        :param request:
        :param obj:
        :return:
        '''
        super().delete(request,obj)
        createStaticIndex.delay()

        cache.delete('index_page_data')

class GoodsTypeAdmin(baseModel):
    pass

class IndexGoodsBannerAdmin(baseModel):
    pass

class IndexTypeGoodsBannerAdmin(baseModel):
    pass

class IndexPromotion(baseModel):
    pass

admin.site.register(GoodsType,GoodsTypeAdmin)
admin.site.register(GoodsSKU)
admin.site.register(GoodsInfo)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotion)




