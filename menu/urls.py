from django.urls import path
from menu.views import TreeListView

urlpatterns = [
    path('treeList', TreeListView.as_view(), name='treeList'),  # 查询权限菜单树信息
]
