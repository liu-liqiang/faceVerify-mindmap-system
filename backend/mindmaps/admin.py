from django.contrib import admin
from .models import MindMapNode, NodeEditLog

@admin.register(MindMapNode)
class MindMapNodeAdmin(admin.ModelAdmin):
    list_display = ['text', 'project', 'creator', 'parent', 'created_at']
    list_filter = ['project', 'creator', 'created_at']
    search_fields = ['text', 'project__name', 'creator__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'creator', 'parent')

@admin.register(NodeEditLog)
class NodeEditLogAdmin(admin.ModelAdmin):
    list_display = ['node', 'user', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['node__text', 'user__username']
    readonly_fields = ['timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('node', 'user')
