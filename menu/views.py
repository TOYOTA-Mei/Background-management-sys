from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from menu.models import SysMenu, SysMenuSerializer


# Create your views here.
class TreeListView(View):
    # 构造菜单树
    def buildTreeMenu(self, sysMenuList):
        resultMenuList: list[SysMenu] = list()
        for menu in sysMenuList:
            # 寻找子节点
            for e in sysMenuList:
                if e.parent_id == menu.id:
                    if not hasattr(menu, "children"):
                        menu.children = list()
                    menu.children.append(e)
            # 判断父节点，添加到集合
            if menu.parent_id == 0:
                resultMenuList.append(menu)
        return resultMenuList

    def get(self, request):
        menuQuerySet = SysMenu.objects.order_by("order_num")
        # 构造菜单树
        sysMenuList: list[SysMenu] = self.buildTreeMenu(menuQuerySet)
        serializerMenuList: list[SysMenuSerializer] = list()
        for sysMenu in sysMenuList:
            serializerMenuList.append(SysMenuSerializer(sysMenu).data)
        return JsonResponse({'code': 200, 'treeList': serializerMenuList})
