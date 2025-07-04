from rest_framework import serializers
from .models import Project, ProjectMember, CaseAttachment
from users.serializers import UserSerializer

class CaseAttachmentSerializer(serializers.ModelSerializer):
    """案件附件序列化器"""
    uploader = UserSerializer(read_only=True)
    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)
    
    class Meta:
        model = CaseAttachment
        fields = [
            'id', 'file', 'original_name', 'file_size', 'file_size_display',
            'file_type', 'description', 'uploader', 'created_at'
        ]
        read_only_fields = ['id', 'original_name', 'file_size', 'file_type', 'uploader', 'created_at']
    
    def create(self, validated_data):
        file = validated_data['file']
        validated_data['original_name'] = file.name
        validated_data['file_size'] = file.size
        validated_data['file_type'] = file.content_type or 'unknown'
        return super().create(validated_data)

class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = ['user', 'permission', 'joined_at']

class ProjectSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    members = ProjectMemberSerializer(source='projectmember_set', many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    node_count = serializers.SerializerMethodField()
    my_node_count = serializers.SerializerMethodField()
    mindmap_attachment_count = serializers.SerializerMethodField()
    my_mindmap_attachment_count = serializers.SerializerMethodField()
    filing_unit_display = serializers.CharField(source='get_filing_unit_display_name', read_only=True)
    attachments = CaseAttachmentSerializer(source='case_attachments', many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'case_number', 'filing_unit', 'filing_unit_display', 
            'case_summary', 'creator', 'members', 'member_count', 'node_count', 
            'my_node_count', 'mindmap_attachment_count', 'my_mindmap_attachment_count',
            'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.projectmember_set.count()
    
    def get_node_count(self, obj):
        return obj.nodes.count() if hasattr(obj, 'nodes') else 0
    
    def get_my_node_count(self, obj):
        """获取当前用户在该项目中创建的节点数"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.nodes.filter(creator=request.user).count() if hasattr(obj, 'nodes') else 0
        return 0
    
    def get_mindmap_attachment_count(self, obj):
        """获取思维导图中所有节点的附件总数"""
        if hasattr(obj, 'nodes'):
            from mindmaps.models import NodeAttachment
            return NodeAttachment.objects.filter(node__project=obj).count()
        return 0
    
    def get_my_mindmap_attachment_count(self, obj):
        """获取当前用户在该项目思维导图中上传的附件数"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(obj, 'nodes'):
            from mindmaps.models import NodeAttachment
            return NodeAttachment.objects.filter(
                node__project=obj, 
                uploader=request.user
            ).count()
        return 0

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'case_number', 'filing_unit', 'case_summary']
    
    def create(self, validated_data):
        request = self.context['request']
        project = Project.objects.create(
            creator=request.user,
            **validated_data
        )
        # 创建者自动成为管理员
        ProjectMember.objects.create(
            project=project,
            user=request.user,
            permission='admin'
        )
        return project

class ProjectMemberInviteSerializer(serializers.Serializer):
    username = serializers.CharField()
    permission = serializers.ChoiceField(choices=ProjectMember.PERMISSION_CHOICES)
    
    def validate_username(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(username=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("用户不存在")
    
    def create(self, validated_data):
        project = self.context['project']
        user = validated_data['username']  # 已经在validate_username中转换为User对象
        permission = validated_data['permission']
        
        member, created = ProjectMember.objects.get_or_create(
            project=project,
            user=user,
            defaults={'permission': permission}
        )
        
        if not created:
            member.permission = permission
            member.save()
        
        return member
