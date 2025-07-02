from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, UserProfile, LoginAttempt

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['username', 'real_name', 'police_number', 'department', 'status', 'is_face_registered']
    list_filter = ['status', 'department', 'is_face_registered', 'is_staff']
    search_fields = ['username', 'real_name', 'police_number']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('公安信息', {'fields': ('real_name', 'police_number', 'phone_number', 'department')}),
        ('审核信息', {'fields': ('status', 'approved_by', 'approved_at')}),
        ('人脸识别', {'fields': ('face_encodings', 'is_face_registered')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('公安信息', {'fields': ('real_name', 'police_number', 'phone_number', 'department')}),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at']
    list_filter = ['created_at']

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['police_number', 'attempt_type', 'result', 'ip_address', 'attempted_at']
    list_filter = ['attempt_type', 'result', 'attempted_at']
    search_fields = ['police_number', 'ip_address']
    ordering = ['-attempted_at']
