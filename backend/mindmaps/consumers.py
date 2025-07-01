import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import MindMapNode, NodeEditLog
from projects.models import Project, ProjectMember

User = get_user_model()

class MindMapConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'mindmap_{self.project_id}'
        self.user = self.scope['user']
        
        # 检查用户权限
        if not await self.check_permission():
            await self.close()
            return
        
        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 发送当前在线用户列表
        await self.send_online_users()
    
    async def disconnect(self, close_code):
        # 离开房间组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'node_create':
                await self.handle_node_create(data)
            elif message_type == 'node_update':
                await self.handle_node_update(data)
            elif message_type == 'node_delete':
                await self.handle_node_delete(data)
            elif message_type == 'cursor_move':
                await self.handle_cursor_move(data)
            elif message_type == 'user_selection':
                await self.handle_user_selection(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '无效的JSON格式'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error', 
                'message': str(e)
            }))
    
    async def handle_node_create(self, data):
        """处理节点创建"""
        try:
            node_data = data.get('node_data', {})
            parent_id = data.get('parent_id')
            
            # 检查编辑权限
            if not await self.check_edit_permission():
                await self.send_error("没有编辑权限")
                return
            
            # 创建节点
            node = await self.create_node(node_data, parent_id)
            
            # 广播给房间内所有用户
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'node_created',
                    'node': await self.serialize_node(node),
                    'user': self.user.username
                }
            )
            
        except Exception as e:
            await self.send_error(f"创建节点失败: {str(e)}")
    
    async def handle_node_update(self, data):
        """处理节点更新"""
        try:
            node_id = data.get('node_id')
            updates = data.get('updates', {})
            
            # 检查编辑权限
            if not await self.check_edit_permission():
                await self.send_error("没有编辑权限")
                return
            
            # 更新节点
            node = await self.update_node(node_id, updates)
            if not node:
                await self.send_error("节点不存在或无权限修改")
                return
            
            # 广播给房间内所有用户
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'node_updated',
                    'node': await self.serialize_node(node),
                    'user': self.user.username
                }
            )
            
        except Exception as e:
            await self.send_error(f"更新节点失败: {str(e)}")
    
    async def handle_node_delete(self, data):
        """处理节点删除"""
        try:
            node_id = data.get('node_id')
            
            # 删除节点
            success = await self.delete_node(node_id)
            if not success:
                await self.send_error("删除失败：节点不存在、无权限或存在子节点")
                return
            
            # 广播给房间内所有用户
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'node_deleted',
                    'node_id': node_id,
                    'user': self.user.username
                }
            )
            
        except Exception as e:
            await self.send_error(f"删除节点失败: {str(e)}")
    
    async def handle_cursor_move(self, data):
        """处理光标移动"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'cursor_moved',
                'user': self.user.username,
                'x': data.get('x', 0),
                'y': data.get('y', 0)
            }
        )
    
    async def handle_user_selection(self, data):
        """处理用户选择"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_selected',
                'user': self.user.username,
                'node_id': data.get('node_id')
            }
        )
    
    # WebSocket事件处理器
    async def node_created(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def node_updated(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def node_deleted(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def cursor_moved(self, event):
        # 不发送给自己
        if event['user'] != self.user.username:
            await self.send(text_data=json.dumps(event))
    
    async def user_selected(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def send_error(self, message):
        """发送错误消息"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    async def send_online_users(self):
        """发送在线用户列表"""
        # 这里可以实现获取在线用户的逻辑
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': [self.user.username]  # 简化实现
        }))
    
    @database_sync_to_async
    def check_permission(self):
        """检查用户是否有项目访问权限"""
        try:
            project = Project.objects.get(id=self.project_id)
            member = ProjectMember.objects.get(project=project, user=self.user)
            return True
        except (Project.DoesNotExist, ProjectMember.DoesNotExist):
            return False
    
    @database_sync_to_async
    def check_edit_permission(self):
        """检查用户是否有编辑权限"""
        try:
            project = Project.objects.get(id=self.project_id)
            member = ProjectMember.objects.get(project=project, user=self.user)
            return member.permission in ['edit', 'admin']
        except (Project.DoesNotExist, ProjectMember.DoesNotExist):
            return False
    
    @database_sync_to_async
    def create_node(self, node_data, parent_id):
        """创建节点"""
        project = Project.objects.get(id=self.project_id)
        parent = None
        if parent_id:
            parent = MindMapNode.objects.get(node_id=parent_id, project=project)
        
        node = MindMapNode.objects.create(
            project=project,
            node_id=node_data.get('uid'),
            parent=parent,
            creator=self.user,
            text=node_data.get('text', ''),
            image=node_data.get('image', ''),
            hyperlink=node_data.get('hyperlink', ''),
            note=node_data.get('note', ''),
            background_color=node_data.get('backgroundColor', '#ffffff'),
            font_color=node_data.get('color', '#000000'),
            font_size=node_data.get('fontSize', 14),
            font_weight=node_data.get('fontWeight', 'normal'),
            extra_data=node_data.get('extra_data', {})
        )
        
        # 记录日志
        NodeEditLog.objects.create(
            node=node,
            user=self.user,
            action='create',
            new_data=node_data
        )
        
        return node
    
    @database_sync_to_async
    def update_node(self, node_id, updates):
        """更新节点"""
        try:
            project = Project.objects.get(id=self.project_id)
            node = MindMapNode.objects.get(node_id=node_id, project=project)
            
            # 检查是否有权限修改（只能修改自己创建的节点）
            if node.creator != self.user:
                return None
            
            # 保存旧数据
            old_data = {
                'text': node.text,
                'image': node.image,
                'hyperlink': node.hyperlink,
                'note': node.note,
                'backgroundColor': node.background_color,
                'color': node.font_color,
                'fontSize': node.font_size,
                'fontWeight': node.font_weight
            }
            
            # 更新字段
            for field, value in updates.items():
                if hasattr(node, field):
                    setattr(node, field, value)
            
            node.save()
            
            # 记录日志
            NodeEditLog.objects.create(
                node=node,
                user=self.user,
                action='update',
                old_data=old_data,
                new_data=updates
            )
            
            return node
        except MindMapNode.DoesNotExist:
            return None
    
    @database_sync_to_async
    def delete_node(self, node_id):
        """删除节点"""
        try:
            project = Project.objects.get(id=self.project_id)
            node = MindMapNode.objects.get(node_id=node_id, project=project)
            
            # 检查删除权限
            if not node.can_be_deleted_by(self.user):
                return False
            
            # 记录日志
            NodeEditLog.objects.create(
                node=node,
                user=self.user,
                action='delete',
                old_data={
                    'text': node.text,
                    'parent_id': node.parent.node_id if node.parent else None
                }
            )
            
            node.delete()
            return True
        except MindMapNode.DoesNotExist:
            return False
    
    @database_sync_to_async
    def serialize_node(self, node):
        """序列化节点"""
        return {
            'id': node.node_id,
            'text': node.text,
            'image': node.image,
            'hyperlink': node.hyperlink,
            'note': node.note,
            'backgroundColor': node.background_color,
            'color': node.font_color,
            'fontSize': node.font_size,
            'fontWeight': node.font_weight,
            'creator': node.creator.username,
            'created_at': node.created_at.isoformat(),
            'parent_id': node.parent.node_id if node.parent else None
        }
