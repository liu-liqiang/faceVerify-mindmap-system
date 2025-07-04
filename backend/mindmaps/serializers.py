from rest_framework import serializers
from .models import MindMapNode, NodeEditLog
from users.serializers import UserSerializer

class MindMapNodeSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    creator_name = serializers.CharField(source='creator.real_name', read_only=True)
    children_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_add_children = serializers.SerializerMethodField()
    
    class Meta:
        model = MindMapNode
        fields = [
            'id', 'node_id', 'parent', 'creator', 'creator_name', 'content', 'icon', 
            'note', 'hyperlink', 'is_root', 'is_system_default', 'extra_data', 
            'children_count', 'can_edit', 'can_delete', 'can_add_children',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_root', 'is_system_default', 'creator', 'created_at', 'updated_at']
    
    def get_children_count(self, obj):
        return obj.children.count()
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_be_edited_by(request.user)
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_be_deleted_by(request.user)
        return False
    
    def get_can_add_children(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_add_children(request.user)
        return False

class NodeCreateSerializer(serializers.ModelSerializer):
    parent_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = MindMapNode
        fields = [
            'node_id', 'parent_id', 'content', 'icon', 'note', 'hyperlink', 'extra_data'
        ]
    
    def create(self, validated_data):
        # 从context中获取project
        project = self.context.get('project')
        if not project:
            raise serializers.ValidationError("项目不存在")
        
        # 从context中获取用户
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("用户未认证")
        
        # 处理父节点
        parent_id = validated_data.pop('parent_id', None)
        parent = None
        if parent_id:
            try:
                parent = MindMapNode.objects.get(project=project, node_id=parent_id)
            except MindMapNode.DoesNotExist:
                raise serializers.ValidationError(f"父节点不存在: {parent_id}")
        
        # 创建节点
        node = MindMapNode.objects.create(
            project=project,
            parent=parent,
            creator=request.user,
            **validated_data
        )
        
        return node

class NodeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindMapNode
        fields = ['content', 'icon', 'note', 'hyperlink', 'extra_data']
    
    def update(self, instance, validated_data):
        # 记录编辑日志
        request = self.context.get('request')
        if request and request.user:
            NodeEditLog.objects.create(
                node=instance,
                user=request.user,
                action='update',
                old_data={
                    'content': instance.content,
                    'note': instance.note,
                    'extra_data': instance.extra_data
                },
                new_data=validated_data
            )
        
        return super().update(instance, validated_data)

class MindMapTreeSerializer(serializers.ModelSerializer):
    """递归序列化思维导图树形结构"""
    children = serializers.SerializerMethodField()
    creator = UserSerializer(read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_add_children = serializers.SerializerMethodField()
    
    class Meta:
        model = MindMapNode
        fields = [
            'id', 'node_id', 'creator', 'content', 'icon', 'hyperlink', 'note',
            'is_root', 'is_system_default', 'extra_data', 'children', 
            'can_edit', 'can_delete', 'can_add_children', 'created_at'
        ]
    
    def get_children(self, obj):
        children = obj.children.all().order_by('created_at')
        return MindMapTreeSerializer(children, many=True, context=self.context).data
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_be_edited_by(request.user)
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_be_deleted_by(request.user)
        return False
    
    def get_can_add_children(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_add_children(request.user)
        return False

class NodeCreateSerializer(serializers.ModelSerializer):
    parent_id = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = MindMapNode
        fields = [
            'node_id', 'parent_id', 'text', 'image', 'hyperlink', 'note',
            'background_color', 'font_color', 'font_size', 'font_weight',
            'position_x', 'position_y', 'extra_data'
        ]
    
    def create(self, validated_data):
        request = self.context['request']
        project = self.context['project']
        
        # 确保移除可能导致冲突的字段
        validated_data.pop('project', None)
        validated_data.pop('creator', None)
        
        parent_id = validated_data.pop('parent_id', None)
        parent = None
        if parent_id:
            try:
                parent = MindMapNode.objects.get(node_id=parent_id, project=project)
            except MindMapNode.DoesNotExist:
                raise serializers.ValidationError("父节点不存在")
        
        node = MindMapNode.objects.create(
            project=project,
            parent=parent,
            creator=request.user,
            **validated_data
        )
        
        # 记录日志
        NodeEditLog.objects.create(
            node=node,
            user=request.user,
            action='create',
            new_data=validated_data
        )
        
        return node

class NodeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindMapNode
        fields = [
            'text', 'image', 'hyperlink', 'note',
            'background_color', 'font_color', 'font_size', 'font_weight',
            'position_x', 'position_y', 'extra_data'
        ]
    
    def update(self, instance, validated_data):
        # 检查权限
        request = self.context['request']
        if instance.creator != request.user:
            raise serializers.ValidationError("只能编辑自己创建的节点")
        
        # 保存旧数据
        old_data = {
            'text': instance.text,
            'image': instance.image,
            'hyperlink': instance.hyperlink,
            'note': instance.note,
            'background_color': instance.background_color,
            'font_color': instance.font_color,
            'font_size': instance.font_size,
            'font_weight': instance.font_weight,
            'position_x': instance.position_x,
            'position_y': instance.position_y,
            'extra_data': instance.extra_data
        }
        
        # 更新实例
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 记录日志
        NodeEditLog.objects.create(
            node=instance,
            user=request.user,
            action='update',
            old_data=old_data,
            new_data=validated_data
        )
        
        return instance

class NodeEditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    node_text = serializers.CharField(source='node.content', read_only=True)
    
    class Meta:
        model = NodeEditLog
        fields = ['id', 'user', 'action', 'node_text', 'old_data', 'new_data', 'timestamp']
