from rest_framework import serializers
from user.models import SysUser


# 登录请求序列化器
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=100, label='用户名')
    password = serializers.CharField(required=True, max_length=100, label='密码')


# 保存用户请求序列化器
class SaveUserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True, label='用户ID，-1表示添加')
    username = serializers.CharField(required=True, max_length=100, label='用户名')
    password = serializers.CharField(required=True, max_length=100, label='密码')
    avatar = serializers.CharField(required=False, max_length=255, label='用户头像')
    email = serializers.CharField(required=False, max_length=50, label='用户邮箱')
    phonenumber = serializers.CharField(required=False, max_length=11, label='手机号码')
    login_date = serializers.DateField(required=False, label='最后登录时间')
    status = serializers.IntegerField(required=False, label='账号状态（0正常 1停用）')
    create_time = serializers.DateField(required=False, label='创建时间')
    update_time = serializers.DateField(required=False, label='更新时间')
    remark = serializers.CharField(required=False, max_length=500, label='备注')

    class Meta:
        model = SysUser
        fields = ['id', 'username', 'password', 'avatar', 'email', 'phonenumber', 'login_date', 'status', 'create_time', 'update_time', 'remark']


# 修改密码请求序列化器
class ChangePasswordSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, label='用户ID')
    oldPassword = serializers.CharField(required=True, max_length=100, label='原密码')
    newPassword = serializers.CharField(required=True, max_length=100, label='新密码')


# 更新头像请求序列化器
class UpdateAvatarSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, label='用户ID')
    avatar = serializers.CharField(required=True, max_length=255, label='头像文件名')


# 查询用户请求序列化器
class SearchUserSerializer(serializers.Serializer):
    pageNum = serializers.IntegerField(required=True, label='当前页码')
    pageSize = serializers.IntegerField(required=True, label='每页大小')
    query = serializers.CharField(required=False, max_length=100, label='查询关键词')


# 修改用户状态请求序列化器
class UpdateStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, label='用户ID')
    status = serializers.IntegerField(required=True, label='账号状态（0正常 1停用）')


# 授权角色请求序列化器
class GrantRoleSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, label='用户ID')
    roleIds = serializers.ListField(required=True, child=serializers.IntegerField(), label='角色ID列表')


# 用户名查重请求序列化器
class CheckUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=100, label='用户名')
