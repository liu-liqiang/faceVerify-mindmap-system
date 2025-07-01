from rest_framework import serializers
from .models import Project, ProjectMember
from users.serializers import UserSerializer

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
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'creator', 'members', 'member_count', 'node_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.projectmember_set.count()
    
    def get_node_count(self, obj):
        return obj.nodes.count()

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'description']
    
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
