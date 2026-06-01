from datetime import datetime

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.template.context_processors import request
from django.views import View
import json
from django.core.cache import cache

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from QianHoufenli import settings
from menu.models import SysMenu, SysMenuSerializer, SysRoleMenu
from role.models import SysRole, SysUserRole
from user.models import SysUser, SysUserSerializer
from user.serializers import (
    LoginSerializer, SaveUserSerializer, ChangePasswordSerializer,
    UpdateAvatarSerializer, SearchUserSerializer, UpdateStatusSerializer,
    GrantRoleSerializer, CheckUsernameSerializer
)
from rest_framework_jwt.settings import api_settings


# Create your views here.
# 用户登录以及查询当前用户角色
class LoginView(APIView):
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

    @swagger_auto_schema(
        operation_summary='用户登录',
        operation_description='用户登录并获取token、角色和菜单信息',
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description='登录成功',
                examples={
                    'application/json': {
                        'code': 200,
                        'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'user': {'id': 1, 'username': 'admin', 'password': '...', 'avatar': '...', 'email': '...', 'phonenumber': '...', 'login_date': '...', 'status': 1, 'create_time': '...', 'update_time': '...', 'remark': '...'},
                        'info': '登录成功！',
                        'roles': '超级管理员,普通角色',
                        'menuList': [{'id': 1, 'name': '系统管理', 'icon': 'system', 'parent_id': 0, 'order_num': 1, 'path': '/sys', 'component': '', 'menu_type': 'M', 'perms': '', 'create_time': '...', 'update_time': '...', 'remark': '...', 'children': []}]
                    }
                }
            ),
            500: openapi.Response(
                description='登录失败',
                examples={
                    'application/json': {
                        'code': 500,
                        'info': '用户名或者密码错误！'
                    }
                }
            ),
            400: openapi.Response(
                description='参数错误',
                examples={
                    'application/json': {
                        'code': 400,
                        'info': '参数错误',
                        'errors': {}
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'info': '参数错误', 'errors': serializer.errors}, status=status.HTTP_200_OK)
        
        data = serializer.validated_data
        username = data.get('username')
        password = data.get('password')
        try:
            user = SysUser.objects.get(username=username)
            if not user.check_password(password):
                return Response({'code': 500, 'info': '用户名或者密码错误！'}, status=status.HTTP_200_OK)
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            # 将用户对象传递进去，获取到该对象的属性值
            payload = jwt_payload_handler(user)
            # 将属性值编码成jwt格式的字符串
            token = jwt_encode_handler(payload)
            
            # 缓存键
            roles_cache_key = f'user_roles_{user.id}'
            menu_cache_key = f'user_menus_{user.id}'
            
            # 尝试从缓存获取角色信息
            roles = cache.get(roles_cache_key)
            if not roles:
                # 使用ORM查询用户角色
                roleList = SysRole.objects.filter(id__in=SysUserRole.objects.filter(user_id=user.id).values('role_id'))
                print(roleList)
                # 获取用户当前所有的角色
                roles = ",".join([role.name for role in roleList])
                # 缓存角色信息
                cache.set(roles_cache_key, roles, 3600)
            
            # 尝试从缓存获取菜单信息
            serializerMenuList = cache.get(menu_cache_key)
            if not serializerMenuList:
                # 使用ORM查询用户角色
                roleList = SysRole.objects.filter(id__in=SysUserRole.objects.filter(user_id=user.id).values('role_id'))
                menuSet: set[SysMenu] = set()
                # 使用ORM查询角色对应的菜单
                for row in roleList:
                    print(row.id, row.name)
                    menuList = SysMenu.objects.filter(id__in=SysRoleMenu.objects.filter(role_id=row.id).values('menu_id'))
                    for row2 in menuList:
                        print(row2.id, row2.name)
                        menuSet.add(row2)
                print(menuSet)
                menuList: list[SysMenu] = list(menuSet)  # set转list
                sorted_menuList = sorted(menuList)  # 根据order_num排序
                print(sorted_menuList)
                # 构造菜单树
                sysMenuList: list[SysMenu] = self.buildTreeMenu(sorted_menuList)
                print(sysMenuList)
                serializerMenuList = list()
                for sysMenu in sysMenuList:
                    serializerMenuList.append(SysMenuSerializer(sysMenu).data)
                # 缓存菜单信息
                cache.set(menu_cache_key, serializerMenuList, 3600)
        except Exception as e:
            print(e)
            return Response({'code': 500, 'info': '用户名或者密码错误！'}, status=status.HTTP_200_OK)
        return Response({'code': 200, 'token': token, 'user': SysUserSerializer(user).data, 'info': '登录成功！',
                         'roles': roles, 'menuList': serializerMenuList}, status=status.HTTP_200_OK)


# 修改基本资料
class SaveView(APIView):
    @swagger_auto_schema(
        operation_summary='保存用户信息',
        operation_description='添加或修改用户信息',
        request_body=SaveUserSerializer,
        responses={
            200: openapi.Response(
                description='保存成功',
                examples={
                    'application/json': {
                        'code': 200
                    }
                }
            ),
            400: openapi.Response(
                description='参数错误',
                examples={
                    'application/json': {
                        'code': 400,
                        'info': '参数错误',
                        'errors': {}
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = SaveUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'info': '参数错误', 'errors': serializer.errors}, status=status.HTTP_200_OK)
        
        data = serializer.validated_data
        print(data)
        if data['id'] == -1:  # 添加
            obj_sysUser = SysUser(username=data['username'],
                                  email=data['email'], phonenumber=data['phonenumber'],
                                  status=data['status'],
                                  remark=data['remark'])
            obj_sysUser.create_time = datetime.now().date()
            obj_sysUser.avatar = 'default.jpg'
            obj_sysUser.set_password("123456")
            obj_sysUser.save()
        else:  # 修改
            obj_sysUser = SysUser.objects.get(id=data['id'])
            obj_sysUser.username = data['username']
            if data['password'] != obj_sysUser.password:  # 密码有变更
                obj_sysUser.set_password(data['password'])
            obj_sysUser.avatar = data['avatar']
            obj_sysUser.email = data['email']
            obj_sysUser.phonenumber = data['phonenumber']
            obj_sysUser.login_date = data['login_date']
            obj_sysUser.status = data['status']
            obj_sysUser.update_time = datetime.now().date()
            obj_sysUser.remark = data['remark']
            obj_sysUser.save()
            # 清除用户缓存
            cache.delete(f'user_roles_{obj_sysUser.id}')
            cache.delete(f'user_menus_{obj_sysUser.id}')
        return Response({'code': 200}, status=status.HTTP_200_OK)


class ActionView(APIView):
    @swagger_auto_schema(
        operation_summary='获取用户信息',
        operation_description='根据ID获取用户信息',
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_QUERY, description='用户ID', type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description='获取成功',
                examples={
                    'application/json': {
                        'code': 200,
                        'user': {'id': 1, 'username': 'admin', 'password': '...', 'avatar': '...', 'email': '...', 'phonenumber': '...', 'login_date': '...', 'status': 1, 'create_time': '...', 'update_time': '...', 'remark': '...'}
                    }
                }
            ),
        },
    )
    def get(self, request):
        """
        根据id获取用户信息
        :param request:
        :return:
        """
        id = request.GET.get("id")
        user_object = SysUser.objects.get(id=id)
        return Response({'code': 200, 'user': SysUserSerializer(user_object).data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='删除用户',
        operation_description='根据ID列表删除用户',
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_INTEGER),
            description='用户ID列表'
        ),
        responses={
            200: openapi.Response(
                description='删除成功',
                examples={
                    'application/json': {
                        'code': 200
                    }
                }
            ),
        },
    )
    def delete(self, request):
        """
        删除操作
        :param request:
        :return:
        """

        idList = request.data
        SysUserRole.objects.filter(user_id__in=idList).delete()
        SysUser.objects.filter(id__in=idList).delete()
        return Response({'code': 200}, status=status.HTTP_200_OK)


# 用户名查重
class CheckView(APIView):
    @swagger_auto_schema(
        operation_summary='检查用户名',
        operation_description='检查用户名是否已存在',
        request_body=CheckUsernameSerializer,
        responses={
            200: openapi.Response(
                description='用户名可用',
                examples={
                    'application/json': {
                        'code': 200
                    }
                }
            ),
            500: openapi.Response(
                description='用户名已存在',
                examples={
                    'application/json': {
                        'code': 500
                    }
                }
            ),
            400: openapi.Response(
                description='参数错误',
                examples={
                    'application/json': {
                        'code': 400,
                        'info': '参数错误',
                        'errors': {}
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = CheckUsernameSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'info': '参数错误', 'errors': serializer.errors}, status=status.HTTP_200_OK)
        
        data = serializer.validated_data
        username = data['username']
        print("username=", username)
        if SysUser.objects.filter(username=username).exists():
            return Response({'code': 500}, status=status.HTTP_200_OK)
        else:
            return Response({'code': 200}, status=status.HTTP_200_OK)


# 修改用户密码
class PwdView(APIView):
    @swagger_auto_schema(
        operation_summary='修改密码',
        operation_description='修改用户密码',
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description='修改成功',
                examples={
                    'application/json': {
                        'code': 200
                    }
                }
            ),
            500: openapi.Response(
                description='修改失败',
                examples={
                    'application/json': {
                        'code': 500,
                        'errorInfo': '原密码错误！'
                    }
                }
            ),
            400: openapi.Response(
                description='参数错误',
                examples={
                    'application/json': {
                        'code': 400,
                        'info': '参数错误',
                        'errors': {}
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'info': '参数错误', 'errors': serializer.errors}, status=status.HTTP_200_OK)
        
        data = serializer.validated_data
        id = data['id']
        oldPassword = data['oldPassword']
        newPassword = data['newPassword']
        obj_user = SysUser.objects.get(id=id)
        if obj_user.check_password(oldPassword):
            obj_user.set_password(newPassword)
            obj_user.update_time = datetime.now().date()
            obj_user.save()
            return Response({'code': 200}, status=status.HTTP_200_OK)
        else:
            return Response({'code': 500, 'errorInfo': '原密码错误！'}, status=status.HTTP_200_OK)


# 上传头像功能
class ImageView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_summary='上传头像',
        operation_description='上传用户头像',
        manual_parameters=[
            openapi.Parameter(
                'avatar',
                openapi.IN_FORM,
                description='头像文件',
                type=openapi.TYPE_FILE,
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description='上传成功',
                examples={
                    'application/json': {
                        'code': 200,
                        'title': '20260416123456.jpg'
                    }
                }
            ),
            500: openapi.Response(
                description='上传失败',
                examples={
                    'application/json': {
                        'code': 500,
                        'errorInfo': '上传头像失败'
                    }
                }
            ),
        },
        consumes=['multipart/form-data']
    )
    def post(self, request):
        file = request.FILES.get('avatar')
        print("file:", file)
        if file:
            file_name = file.name
            suffixName = file_name[file_name.rfind("."):]
            new_file_name = datetime.now().strftime('%Y%m%d%H%M%S') + suffixName
            file_path = str(settings.MEDIA_ROOT) + "\\userAvatar\\" + new_file_name
            print("file_path:", file_path)
            try:
                with open(file_path, 'wb') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                return Response({'code': 200, 'title': new_file_name}, status=status.HTTP_200_OK)
            except:
                return Response({'code': 500, 'errorInfo': '上传头像失败'}, status=status.HTTP_200_OK)


# 修改头像功能
class AvatarView(APIView):
    @swagger_auto_schema(
        operation_summary='更新头像',
        operation_description='更新用户头像信息',
        request_body=UpdateAvatarSerializer,
        responses={
            200: openapi.Response(
                description='更新成功',
                examples={
                    'application/json': {
                        'code': 200
                    }
                }
            ),
            400: openapi.Response(
                description='参数错误',
                examples={
                    'application/json': {
                        'code': 400,
                        'info': '参数错误',
                        'errors': {}
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = UpdateAvatarSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'info': '参数错误', 'errors': serializer.errors}, status=status.HTTP_200_OK)
        
        data = serializer.validated_data
        id = data['id']
        avatar = data['avatar']
        obj_user = SysUser.objects.get(id=id)
        obj_user.avatar = avatar
        obj_user.save()
        return Response({'code': 200}, status=status.HTTP_200_OK)


# 用户信息查询
class SearchView(APIView):
    @swagger_auto_schema(
        operation_summary='查询用户',
        operation_description='分页查询用户信息',
        request_body=SearchUserSerializer,
        responses={
            200: openapi.Response(
                description='查询成功',
                examples={
                    'application/json': {
                        'code': 200,
                        'userList': [{'id': 1, 'username': 'admin', 'password': '...', 'avatar': '...', 'email': '...', 'phonenumber': '...', 'login_date': '...', 'status': 1, 'create_time': '...', 'update_time': '...', 'remark': '...', 'roleList': [{'id': 1, 'name': '超级管理员'}]}],
                        'total': 1
                    }
                }
            ),
            400: openapi.Response(
                description='参数错误',
                examples={
                    'application/json': {
                        'code': 400,
                        'info': '参数错误',
                        'errors': {}
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = SearchUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'info': '参数错误', 'errors': serializer.errors}, status=status.HTTP_200_OK)
        
        data = serializer.validated_data
        pageNum = data['pageNum']  # 当前页
        pageSize = data['pageSize']  # 每页大小
        query = data.get('query', '')  # 查询参数
        print(pageSize, pageNum)
        userListPage = Paginator(SysUser.objects.filter(username__icontains=query), pageSize).page(pageNum)
        print(userListPage)
        obj_users = userListPage.object_list.values()  # 转成字典
        users = list(obj_users)  # 把外层的容器转成List
        for user in users:
            userId = user['id']
            # 使用ORM查询用户角色
            roleList = SysRole.objects.filter(id__in=SysUserRole.objects.filter(user_id=userId).values('role_id'))
            roleListDict = []
            for role in roleList:
                roleDict = {}
                roleDict["id"] = role.id
                roleDict["name"] = role.name
                roleListDict.append(roleDict)
            user['roleList'] = roleListDict
        total = SysUser.objects.filter(username__icontains=query).count()
        return Response({'code': 200, 'userList': users, 'total': total}, status=status.HTTP_200_OK)


# 重置密码
class PasswordView(APIView):
    @swagger_auto_schema(
        operation_summary='重置密码',
        operation_description='将用户密码重置为默认值123456',
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_QUERY, description='用户ID', type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description='重置成功',
                examples={
                    'application/json': {
                        'code': 200
                    }
                }
            ),
        },
    )
    def get(self, request):
        id = request.GET.get("id")
        user_object = SysUser.objects.get(id=id)
        user_object.set_password("123456")
        user_object.update_time = datetime.now().date()
        user_object.save()
        return Response({'code': 200}, status=status.HTTP_200_OK)


# 用户状态修改
class StatusView(APIView):
    @swagger_auto_schema(
        operation_summary='修改用户状态',
        operation_description='修改用户账号状态（0正常 1停用）',
        request_body=UpdateStatusSerializer,
        responses={
            200: openapi.Response(
                description='修改成功',
                examples={
                    'application/json': {
                        'code': 200
                    }
                }
            ),
            400: openapi.Response(
                description='参数错误',
                examples={
                    'application/json': {
                        'code': 400,
                        'info': '参数错误',
                        'errors': {}
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = UpdateStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'info': '参数错误', 'errors': serializer.errors}, status=status.HTTP_200_OK)
        
        data = serializer.validated_data
        id = data['id']
        status = data['status']
        user_object = SysUser.objects.get(id=id)
        user_object.status = status
        user_object.save()
        return Response({'code': 200}, status=status.HTTP_200_OK)


# 用户角色授权
class GrantRole(APIView):
    @swagger_auto_schema(
        operation_summary='授权角色',
        operation_description='为用户分配角色',
        request_body=GrantRoleSerializer,
        responses={
            200: openapi.Response(
                description='授权成功',
                examples={
                    'application/json': {
                        'code': 200
                    }
                }
            ),
            400: openapi.Response(
                description='参数错误',
                examples={
                    'application/json': {
                        'code': 400,
                        'info': '参数错误',
                        'errors': {}
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = GrantRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 400, 'info': '参数错误', 'errors': serializer.errors}, status=status.HTTP_200_OK)
        
        data = serializer.validated_data
        user_id = data['id']
        roleIdList = data['roleIds']
        print(user_id, roleIdList)
        SysUserRole.objects.filter(user_id=user_id).delete()  # 删除用户角色关联表中的指定用户数据
        for roleId in roleIdList:
            userRole = SysUserRole(user_id=user_id, role_id=roleId)
            userRole.save()
        # 清除用户缓存
        cache.delete(f'user_roles_{user_id}')
        cache.delete(f'user_menus_{user_id}')
        return Response({'code': 200}, status=status.HTTP_200_OK)
