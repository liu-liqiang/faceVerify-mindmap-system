from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MindMapNodeViewSet

# 简化的URL配置
urlpatterns = [
    # 原有的基于项目的URL模式
    path('api/projects/<int:project_pk>/nodes/', MindMapNodeViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/projects/<int:project_pk>/nodes/<int:pk>/', MindMapNodeViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    })),
    path('api/projects/<int:project_pk>/nodes/tree/', MindMapNodeViewSet.as_view({'get': 'tree'})),
    path('api/projects/<int:project_pk>/nodes/simple-mind-map/', MindMapNodeViewSet.as_view({'get': 'simple_mind_map_format'})),
    path('api/projects/<int:project_pk>/nodes/logs/', MindMapNodeViewSet.as_view({'get': 'logs'})),
    path('api/projects/<int:project_pk>/nodes/stats/', MindMapNodeViewSet.as_view({'get': 'user_stats'})),
    
    # 新增的直接访问URL模式，匹配前端请求路径
    path('api/mindmaps/nodes/create/', MindMapNodeViewSet.as_view({'post': 'create_with_project_id'})),
    path('api/mindmaps/nodes/update/', MindMapNodeViewSet.as_view({'put': 'update_with_node_uid'})),
    path('api/mindmaps/nodes/<str:node_uid>/', MindMapNodeViewSet.as_view({'delete': 'delete_by_uid'})),
    path('api/mindmaps/nodes/move/', MindMapNodeViewSet.as_view({'put': 'move_node'})),
    # path('api/mindmaps/batch-update/', MindMapNodeViewSet.as_view({'post': 'batch_update'})),
]
