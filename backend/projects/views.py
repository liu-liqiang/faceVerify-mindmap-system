from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Project, ProjectMember
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, 
    ProjectMemberSerializer, ProjectMemberInviteSerializer
)

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # 只返回用户参与的项目
        return Project.objects.filter(
            projectmember__user=self.request.user
        ).distinct().order_by('-updated_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer
    
    @action(detail=True, methods=['post'])
    def invite_member(self, request, pk=None):
        """邀请用户加入项目"""
        project = self.get_object()
        
        # 检查权限（只有创建者和管理员可以邀请）
        try:
            member = ProjectMember.objects.get(project=project, user=request.user)
            if member.permission not in ['admin']:
                return Response(
                    {'error': '没有权限邀请成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': '你不是项目成员'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProjectMemberInviteSerializer(
            data=request.data, 
            context={'project': project}
        )
        if serializer.is_valid():
            member = serializer.save()
            return Response(
                ProjectMemberSerializer(member).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """获取项目成员列表"""
        project = self.get_object()
        members = ProjectMember.objects.filter(project=project).select_related('user')
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """移除项目成员"""
        project = self.get_object()
        username = request.data.get('username')
        
        if not username:
            return Response(
                {'error': '用户名不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查权限
        try:
            current_member = ProjectMember.objects.get(project=project, user=request.user)
            if current_member.permission != 'admin':
                return Response(
                    {'error': '没有权限移除成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': '你不是项目成员'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 不能移除项目创建者
        if project.creator.username == username:
            return Response(
                {'error': '不能移除项目创建者'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user_to_remove = User.objects.get(username=username)
            member_to_remove = ProjectMember.objects.get(project=project, user=user_to_remove)
            member_to_remove.delete()
            return Response({'message': '成员移除成功'})
        except (User.DoesNotExist, ProjectMember.DoesNotExist):
            return Response(
                {'error': '用户不存在或不是项目成员'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['put'])
    def update_member_permission(self, request, pk=None):
        """更新成员权限"""
        project = self.get_object()
        username = request.data.get('username')
        permission = request.data.get('permission')
        
        if not username or not permission:
            return Response(
                {'error': '用户名和权限不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查权限
        try:
            current_member = ProjectMember.objects.get(project=project, user=request.user)
            if current_member.permission != 'admin':
                return Response(
                    {'error': '没有权限修改成员权限'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': '你不是项目成员'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 不能修改项目创建者权限
        if project.creator.username == username:
            return Response(
                {'error': '不能修改项目创建者权限'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(username=username)
            member = ProjectMember.objects.get(project=project, user=user)
            member.permission = permission
            member.save()
            return Response(ProjectMemberSerializer(member).data)
        except (User.DoesNotExist, ProjectMember.DoesNotExist):
            return Response(
                {'error': '用户不存在或不是项目成员'}, 
                status=status.HTTP_404_NOT_FOUND
            )
