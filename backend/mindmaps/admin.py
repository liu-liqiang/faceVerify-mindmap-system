from django.contrib import admin
from .models import MindMapNode, NodeEditLog, NodeAttachment

@admin.register(MindMapNode)
class MindMapNodeAdmin(admin.ModelAdmin):
    list_display = ['content', 'project', 'creator', 'parent', 'created_at']
    list_filter = ['project', 'creator', 'created_at']
    search_fields = ['content', 'project__name', 'creator__real_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'creator', 'parent')

@admin.register(NodeEditLog)
class NodeEditLogAdmin(admin.ModelAdmin):
    list_display = ['node', 'user', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['node__content', 'user__real_name']
    readonly_fields = ['timestamp']

@admin.register(NodeAttachment)
class NodeAttachmentAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'node', 'uploader', 'file_size_display', 'created_at']
    list_filter = ['file_type', 'uploader', 'created_at']
    search_fields = ['original_name', 'node__content', 'uploader__real_name']
    readonly_fields = ['file_size', 'file_type', 'created_at']
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = '文件大小'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('node', 'user')
