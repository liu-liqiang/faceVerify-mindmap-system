from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    department_display = serializers.CharField(source='get_department_display_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'real_name', 'police_number', 
            'phone_number', 'department', 'department_display', 'status', 'status_display',
            'is_face_registered', 'is_superuser', 'is_staff', 'approved_by', 'approved_at',
            'date_joined'
        ]
        read_only_fields = [
            'id', 'username', 'status', 'is_face_registered', 'is_superuser', 'is_staff',
            'approved_by', 'approved_at', 'date_joined'
        ]

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = [
            'real_name', 'police_number', 'phone_number', 'department', 
            'password'
        ]
    
    def validate_police_number(self, value):
        """验证警号格式和唯一性"""
        import re
        if not re.match(r'^[A-Za-z0-9]{3,20}$', value):
            raise serializers.ValidationError('警号只能包含字母和数字，长度3-20位')
        
        if User.objects.filter(police_number=value).exists():
            raise serializers.ValidationError('该警号已存在')
        
        return value
    
    def validate_phone_number(self, value):
        """验证手机号格式和唯一性"""
        import re
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('请输入正确的手机号码')
        
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('该手机号码已被使用')
        
        return value
    

    
    def create(self, validated_data):
        password = validated_data.pop('password')
        # 使用警号作为用户名
        validated_data['username'] = validated_data['police_number']
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserApprovalSerializer(serializers.ModelSerializer):
    """用户审核序列化器"""
    class Meta:
        model = User
        fields = ['id', 'status', 'rejection_reason']
    
    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', instance.status)
        
        # 更新状态
        instance.status = new_status
        instance.rejection_reason = validated_data.get('rejection_reason', '')
        
        # 如果是审核通过，记录审核信息
        if new_status == 'approved' and old_status != 'approved':
            instance.approved_by = self.context['request'].user
            instance.approved_at = timezone.now()
        
        instance.save()
        
        return instance
