from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import MindMapNode, NodeEditLog
from .serializers import (
    MindMapNodeSerializer, MindMapTreeSerializer,
    NodeCreateSerializer, NodeUpdateSerializer, NodeEditLogSerializer
)
from projects.models import Project, ProjectMember

class MindMapNodeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        if project_id:
            # 检查用户是否是项目成员
            try:
                project = Project.objects.get(id=project_id)
                ProjectMember.objects.get(project=project, user=self.request.user)
                return MindMapNode.objects.filter(project=project).order_by('created_at')
            except (Project.DoesNotExist, ProjectMember.DoesNotExist):
                return MindMapNode.objects.none()
        return MindMapNode.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NodeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NodeUpdateSerializer
        return MindMapNodeSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_id = self.kwargs.get('project_pk')
        if project_id:
            try:
                context['project'] = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                pass
        return context
    
    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, id=project_id)
        
        # 检查项目成员权限：有编辑权限及以上的用户可以添加节点
        try:
            member = ProjectMember.objects.get(project=project, user=self.request.user)
            if member.permission not in ['edit', 'admin']:
                raise PermissionError("没有编辑权限，无法添加节点")
        except ProjectMember.DoesNotExist:
            raise PermissionError("你不是项目成员")
        
        # 保存节点，序列化器会自动设置project和creator
        serializer.save()
    
    def perform_update(self, serializer):
        # 检查是否可以编辑此节点：只能编辑自己创建的节点
        if not serializer.instance.can_be_edited_by(self.request.user):
            raise PermissionError("只能编辑自己创建的节点")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # 检查删除权限：只能删除自己创建的且没有子节点的节点
        if not instance.can_be_deleted_by(self.request.user):
            raise PermissionError("只能删除自己创建的且没有子节点的节点")
        
        # 记录删除日志
        NodeEditLog.objects.create(
            node=instance,
            user=self.request.user,
            action='delete',
            old_data={
                'content': instance.content,
                'parent_id': instance.parent.node_id if instance.parent else None
            }
        )
        instance.delete()
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def tree(self, request, project_pk=None):
        """获取思维导图树形结构"""
        project = get_object_or_404(Project, id=project_pk)
        
        # 检查权限
        try:
            ProjectMember.objects.get(project=project, user=request.user)
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': '你不是项目成员'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 获取根节点
        root_nodes = MindMapNode.objects.filter(
            project=project, 
            is_root=True
        ).order_by('created_at')
        
        serializer = MindMapTreeSerializer(
            root_nodes, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def simple_mind_map_format(self, request, project_pk=None):
        """获取simple-mind-map格式的数据"""
        project = get_object_or_404(Project, id=project_pk)
        
        # 检查权限
        try:
            ProjectMember.objects.get(project=project, user=request.user)
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': '你不是项目成员'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 获取根节点
        root_nodes = MindMapNode.objects.filter(
            project=project, 
            is_root=True
        ).order_by('created_at')
        
        if root_nodes.exists():
            # 如果有多个根节点，创建一个虚拟根节点
            if root_nodes.count() > 1:
                mind_map_data = {
                    'data': {
                        'text': project.name,
                        'uid': 'root',
                        'isRoot': True,
                        'expand': True
                    },
                    'children': [node.to_simple_mind_map_format(request.user) for node in root_nodes]
                }
            else:
                mind_map_data = root_nodes.first().to_simple_mind_map_format(request.user)
        else:
            # 如果没有节点，创建默认根节点
            mind_map_data = {
                'data': {
                    'text': project.name,
                    'uid': 'root',
                    'isRoot': True,
                    'expand': True
                },
                'children': []
            }
        
        return Response(mind_map_data)
    
    @action(detail=False, methods=['get'])
    def logs(self, request, project_pk=None):
        """获取节点编辑日志"""
        project = get_object_or_404(Project, id=project_pk)
        
        # 检查权限
        try:
            ProjectMember.objects.get(project=project, user=request.user)
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': '你不是项目成员'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        logs = NodeEditLog.objects.filter(
            node__project=project
        ).order_by('-timestamp')[:50]  # 最近50条日志
        
        serializer = NodeEditLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_stats(self, request, project_pk=None):
        """获取用户在项目中的统计信息"""
        project = get_object_or_404(Project, id=project_pk)
        
        # 检查权限
        try:
            ProjectMember.objects.get(project=project, user=request.user)
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': '你不是项目成员'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_nodes = MindMapNode.objects.filter(
            project=project, 
            creator=request.user
        )
        
        stats = {
            'total_nodes': user_nodes.count(),
            'recent_nodes': MindMapNodeSerializer(
                user_nodes.order_by('-created_at')[:5], 
                many=True,
                context={'request': request}
            ).data,
            'project_total_nodes': project.nodes.count(),
            'user_percentage': (
                user_nodes.count() / project.nodes.count() * 100 
                if project.nodes.count() > 0 else 0
            )
        }
        
        return Response(stats)
