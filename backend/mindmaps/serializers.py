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
            'id', 'node_id', 'parent_node_uid', 'creator', 'creator_name', 'content', 'text', 
            'icon', 'note', 'hyperlink', 'is_root', 'is_system_default', 'tags', 
            'children_count', 'can_edit', 'can_delete', 'can_add_children',
            'created_at', 'updated_at', 'level', 'sort_order'
        ]
        read_only_fields = ['id', 'is_root', 'is_system_default', 'creator', 'created_at', 'updated_at']
    
    def get_children_count(self, obj):
        return obj.get_children().count()
    
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
            'node_id', 'parent_id', 'content', 'text', 'icon', 'note', 'hyperlink', 'tags'
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
        parent_node_uid = ''
        if parent_id:
            try:
                parent = MindMapNode.objects.get(project=project, node_id=parent_id)
                parent_node_uid = parent.node_id
            except MindMapNode.DoesNotExist:
                raise serializers.ValidationError(f"父节点不存在: {parent_id}")
        
        # 创建节点
        node = MindMapNode.objects.create(
            project=project,
            parent_node_uid=parent_node_uid,
            creator=request.user,
            **validated_data
        )
        
        return node

class NodeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindMapNode
        fields = ['content', 'text', 'icon', 'note', 'hyperlink', 'tags']
    
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
                    'text': instance.text
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
            'id', 'node_id', 'creator', 'content', 'text', 'icon', 'hyperlink', 'note',
            'is_root', 'is_system_default', 'tags', 'children', 
            'can_edit', 'can_delete', 'can_add_children', 'created_at'
        ]
    
    def get_children(self, obj):
        children = obj.get_children()
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

class NodeEditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    node_text = serializers.CharField(source='node.content', read_only=True)
    
    class Meta:
        model = NodeEditLog
        fields = ['id', 'user', 'action', 'node_text', 'old_data', 'new_data', 'timestamp']
