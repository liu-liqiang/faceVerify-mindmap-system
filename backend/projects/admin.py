from django.contrib import admin
from .models import Project, ProjectMember, CaseAttachment

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'case_number', 'filing_unit', 'creator', 'created_at']
    list_filter = ['filing_unit', 'created_at', 'updated_at']
    search_fields = ['name', 'case_number', 'case_summary']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'permission', 'joined_at']
    list_filter = ['permission', 'joined_at']
    search_fields = ['project__name', 'user__real_name']

@admin.register(CaseAttachment)
class CaseAttachmentAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'project', 'uploader', 'file_size_display', 'created_at']
    list_filter = ['file_type', 'uploader', 'created_at']
    search_fields = ['original_name', 'project__name', 'uploader__real_name']
    readonly_fields = ['file_size', 'file_type', 'created_at']
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = '文件大小'
