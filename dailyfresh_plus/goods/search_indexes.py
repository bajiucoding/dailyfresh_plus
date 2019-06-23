#coding=utf-8
'''
*************************
file:       dailyfresh_plus search_indexes
author:     gongyi
date:       2019/6/16 17:27
****************************
change activity:
            2019/6/16 17:27
'''
from haystack import indexes
from goods.models import GoodsSKU

#指定要对哪些数据建立索引
class GoodsSKUIndex(indexes.SearchIndex,indexes.Indexable):
    text = indexes.CharField(document=True,use_template=True)

    def get_model(self):
        return GoodsSKU

    def index_queryset(self, using=None):
        return self.get_model().objects.all()