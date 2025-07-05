from django.contrib import admin
from .models import MindMapNode, NodeEditLog, NodeAttachment, NodeImage, AssociativeLine, NodeTag, NodeGeneralization

@admin.register(MindMapNode)
class MindMapNodeAdmin(admin.ModelAdmin):
    list_display = ['text', 'project', 'creator', 'parent_node_uid', 'is_root', 'is_system_default', 'created_at']
    list_filter = ['project', 'creator', 'is_root', 'is_system_default', 'created_at']
    search_fields = ['text', 'project__name', 'creator__real_name', 'creator__username']
    readonly_fields = ['created_at', 'updated_at', 'level']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'creator')

@admin.register(NodeEditLog)
class NodeEditLogAdmin(admin.ModelAdmin):
    list_display = ['node', 'user', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['node__text', 'user__real_name', 'user__username']
    readonly_fields = ['timestamp']

@admin.register(NodeAttachment)
class NodeAttachmentAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'node', 'uploader', 'file_size_display', 'created_at']
    list_filter = ['uploader', 'created_at']
    search_fields = ['original_name', 'node__text', 'uploader__real_name', 'uploader__username']
    readonly_fields = ['file_size', 'created_at']
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = '文件大小'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('node', 'uploader')

@admin.register(NodeImage)
class NodeImageAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'node', 'uploader', 'width', 'height', 'file_size_display', 'created_at']
    list_filter = ['uploader', 'created_at']
    search_fields = ['original_name', 'node__text', 'uploader__real_name', 'uploader__username']
    readonly_fields = ['file_size', 'width', 'height', 'created_at']
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = '文件大小'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('node', 'uploader')

@admin.register(AssociativeLine)
class AssociativeLineAdmin(admin.ModelAdmin):
    list_display = ['source_node', 'target_node', 'text', 'creator', 'created_at']
    list_filter = ['creator', 'created_at']
    search_fields = ['source_node__text', 'target_node__text', 'text', 'creator__real_name', 'creator__username']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('source_node', 'target_node', 'creator')

@admin.register(NodeTag)
class NodeTagAdmin(admin.ModelAdmin):
    list_display = ['text', 'node', 'sort_order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['text', 'node__text']
    ordering = ['node', 'sort_order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('node')

@admin.register(NodeGeneralization)
class NodeGeneralizationAdmin(admin.ModelAdmin):
    list_display = ['text', 'node', 'rich_text', 'sort_order', 'created_at']
    list_filter = ['rich_text', 'created_at']
    search_fields = ['text', 'node__text']
    ordering = ['node', 'sort_order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('node')
