from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import json
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
                'parent_id': instance.parent_node_uid if instance.parent_node_uid else None
            }
        )
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
    
    # 新增的方法，匹配前端API路径
    
    @action(detail=False, methods=['post'])
    def create_with_project_id(self, request):
        """使用projectId创建节点 - 优化版本使用 from_simple_mind_map_data"""
        try:
            # 从请求数据中获取projectId
            project_id = request.data.get('projectId')
            if not project_id:
                return Response(
                    {'error': 'projectId是必需的'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            project = get_object_or_404(Project, id=project_id)
            
            # 检查权限
            try:
                member = ProjectMember.objects.get(project=project, user=self.request.user)
                if member.permission not in ['edit', 'admin']:
                    return Response(
                        {'error': '没有编辑权限，无法添加节点'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ProjectMember.DoesNotExist:
                return Response(
                    {'error': '你不是项目成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 获取节点数据
            data = request.data.get('data', {})
            parent_uid = request.data.get('parent_uid', '')
            
            # 构建节点数据（匹配 from_simple_mind_map_data 的格式）
            node_data = {
                'projectId': project_id,
                'data': json.loads(data),
                'parent_uid': parent_uid,
                'image': request.FILES.get('image'),
                'attachment': request.FILES.get('attachment')
            }
            
            # 使用模型的批量创建方法
            created_nodes = MindMapNode.from_simple_mind_map_data([node_data], request.user)
            
            if not created_nodes:
                return Response(
                    {'error': '节点创建失败'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            node = created_nodes[0]
            
            # 记录创建日志
            NodeEditLog.objects.create(
                node=node,
                user=request.user,
                action='create',
                new_data={
                    'content': node.text,
                    'parent_uid': node.parent_node_uid
                }
            )
            
            serializer = MindMapNodeSerializer(node, context={'request': request})
            return Response({
                'success': True,
                'node_id': node.id,
                'node_uid': node.node_id,
                'node': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'创建节点失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='create-simple')
    def create_simple(self, request):
        """简单创建节点方法，用于调试"""
        try:
            # 从请求数据中获取projectId
            project_id = request.data.get('projectId')
            if not project_id:
                return Response(
                    {'error': 'projectId是必需的'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            project = get_object_or_404(Project, id=project_id)
            
            # 检查权限
            try:
                member = ProjectMember.objects.get(project=project, user=request.user)
                if member.permission not in ['edit', 'admin']:
                    return Response(
                        {'error': '没有编辑权限，无法添加节点'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ProjectMember.DoesNotExist:
                return Response(
                    {'error': '你不是项目成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 获取节点数据
            data = request.data.get('data', {})
            parent_uid = request.data.get('parent_uid', '')
            
            # 生成节点ID
            from .models import generate_node_id
            node_id = data.get('uid') or generate_node_id()
            
            # 直接创建节点
            node = MindMapNode.objects.create(
                project=project,
                node_id=node_id,
                parent_node_uid=parent_uid if parent_uid else '',
                creator=request.user,
                text=data.get('text', '新节点'),
                rich_text=data.get('richText', False),
                expand=data.get('expand', True),
                icon=data.get('icon', []),
                hyperlink=data.get('hyperlink', ''),
                hyperlink_title=data.get('hyperlinkTitle', ''),
                note=data.get('note', ''),
                tags=data.get('tag', []),
                is_root=not parent_uid,
                is_system_default=data.get('isSystemDefault', False),
            )
            
            # 记录创建日志
            NodeEditLog.objects.create(
                node=node,
                user=request.user,
                action='create',
                new_data={
                    'content': node.text,
                    'parent_uid': node.parent_node_uid
                }
            )
            
            serializer = MindMapNodeSerializer(node, context={'request': request})
            return Response({
                'success': True,
                'node_id': node.id,
                'node_uid': node.node_id,
                'node': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'创建节点失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['put'])
    def update_with_node_uid(self, request):
        """使用node_uid更新节点"""
        try:
            node_uid = request.data.get('node_uid')
            project_id = request.data.get('projectId')
            
            if not node_uid or not project_id:
                return Response(
                    {'error': 'node_uid和projectId都是必需的'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            project = get_object_or_404(Project, id=project_id)
            node = get_object_or_404(MindMapNode, project=project, node_id=node_uid)
            
            # 检查权限
            if not node.can_be_edited_by(request.user):
                return Response(
                    {'error': '只能编辑自己创建的节点'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 更新节点数据
            node_data = request.data.get('data', {})
            old_data = {
                'content': node.content,
                'text': node.text
            }
            
            node.content = node_data.get('text', node.content)
            # 更新其他字段
            if 'rich_text' in node_data:
                node.rich_text = node_data['rich_text']
            if 'expand' in node_data:
                node.expand = node_data['expand']
            if 'icon' in node_data:
                node.icon = node_data['icon']
            if 'hyperlink' in node_data:
                node.hyperlink = node_data['hyperlink']
            if 'hyperlink_title' in node_data:
                node.hyperlink_title = node_data['hyperlink_title']
            if 'note' in node_data:
                node.note = node_data['note']
            if 'tags' in node_data:
                node.tags = node_data['tags']
            node.save()
            
            # 记录更新日志
            NodeEditLog.objects.create(
                node=node,
                user=request.user,
                action='update',
                old_data=old_data,
                new_data=node_data
            )
            
            serializer = MindMapNodeSerializer(node, context={'request': request})
            return Response({
                'success': True,
                'node': serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': f'更新节点失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['delete'])
    def delete_by_uid(self, request, node_uid=None):
        """使用node_uid删除节点"""
        try:
            project_id = request.data.get('projectId')
            
            if not project_id:
                return Response(
                    {'error': 'projectId是必需的'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            project = get_object_or_404(Project, id=project_id)
            node = get_object_or_404(MindMapNode, project=project, node_id=node_uid)
            
            # 检查删除权限：只能删除自己创建的且没有子节点的节点
            if not node.can_be_deleted_by(request.user):
                return Response(
                    {'error': '只能删除自己创建的且没有子节点的节点'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            node.delete()
            
            return Response({
                'success': True,
                'message': f'节点 {node_uid} 已删除'
            })
            
        except Exception as e:
            return Response(
                {'error': f'删除节点失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['put'])
    def move_node(self, request):
        """移动节点到新的父节点"""
        try:
            node_uid = request.data.get('node_uid')
            new_parent_uid = request.data.get('new_parent_uid')
            old_parent_uid = request.data.get('old_parent_uid')
            project_id = request.data.get('projectId')
            
            if not all([node_uid, project_id]):
                return Response(
                    {'error': 'node_uid和projectId都是必需的'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            project = get_object_or_404(Project, id=project_id)
            node = get_object_or_404(MindMapNode, project=project, node_id=node_uid)
            
            # 检查权限
            if not node.can_be_edited_by(request.user):
                return Response(
                    {'error': '只能移动自己创建的节点'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 查找新父节点
            new_parent = None
            if new_parent_uid and new_parent_uid != 'root':
                try:
                    new_parent = MindMapNode.objects.get(
                        project=project,
                        node_id=new_parent_uid
                    )
                except MindMapNode.DoesNotExist:
                    return Response(
                        {'error': f'新父节点 {new_parent_uid} 不存在'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # 更新节点的父节点
            old_parent_uid = node.parent_node_uid
            node.parent_node_uid = new_parent_uid
            node.is_root = new_parent_uid is None
            node.save()
            
            # 记录移动日志
            NodeEditLog.objects.create(
                node=node,
                user=request.user,
                action='move',
                old_data={
                    'old_parent_id': old_parent_uid
                },
                new_data={
                    'new_parent_id': new_parent_uid
                }
            )
            
            serializer = MindMapNodeSerializer(node, context={'request': request})
            return Response({
                'success': True,
                'node': serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': f'移动节点失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """批量更新节点"""
        try:
            project_id = request.data.get('projectId')
            changes = request.data.get('changes', [])
            
            if not project_id:
                return Response(
                    {'error': 'projectId是必需的'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            project = get_object_or_404(Project, id=project_id)
            
            # 检查权限
            try:
                member = ProjectMember.objects.get(project=project, user=request.user)
                if member.permission not in ['edit', 'admin']:
                    return Response(
                        {'error': '没有编辑权限'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ProjectMember.DoesNotExist:
                return Response(
                    {'error': '你不是项目成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            results = []
            for change in changes:
                try:
                    action = change.get('action')
                    node_uid = change.get('node_uid')
                    node_data = change.get('node_data')
                    
                    if action == 'update' and node_uid:
                        node = MindMapNode.objects.get(
                            project=project,
                            node_id=node_uid
                        )
                        
                        if node.can_be_edited_by(request.user):
                            old_data = {
                                'content': node.content,
                                'text': node.text
                            }
                            
                            node.content = node_data.get('text', node.content)
                            # 更新其他字段
                            if 'rich_text' in node_data:
                                node.rich_text = node_data['rich_text']
                            if 'expand' in node_data:
                                node.expand = node_data['expand']
                            if 'icon' in node_data:
                                node.icon = node_data['icon']
                            if 'hyperlink' in node_data:
                                node.hyperlink = node_data['hyperlink']
                            if 'hyperlink_title' in node_data:
                                node.hyperlink_title = node_data['hyperlink_title']
                            if 'note' in node_data:
                                node.note = node_data['note']
                            if 'tags' in node_data:
                                node.tags = node_data['tags']
                            node.save()
                            
                            # 记录日志
                            NodeEditLog.objects.create(
                                node=node,
                                user=request.user,
                                action='update',
                                old_data=old_data,
                                new_data=node_data
                            )
                            
                            results.append({
                                'node_uid': node_uid,
                                'success': True
                            })
                        else:
                            results.append({
                                'node_uid': node_uid,
                                'success': False,
                                'error': '没有编辑权限'
                            })
                    else:
                        results.append({
                            'node_uid': node_uid,
                            'success': False,
                            'error': '不支持的操作或缺少必要参数'
                        })
                        
                except Exception as e:
                    results.append({
                        'node_uid': node_uid,
                        'success': False,
                        'error': str(e)
                    })
            
            return Response({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            return Response(
                {'error': f'批量更新失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
