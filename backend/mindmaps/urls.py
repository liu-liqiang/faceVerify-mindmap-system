from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MindMapNodeViewSet

# 简化的URL配置
urlpatterns = [
    path('api/projects/<int:project_pk>/nodes/', MindMapNodeViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/projects/<int:project_pk>/nodes/<int:pk>/', MindMapNodeViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    })),
    path('api/projects/<int:project_pk>/nodes/tree/', MindMapNodeViewSet.as_view({'get': 'tree'})),
    path('api/projects/<int:project_pk>/nodes/simple-mind-map/', MindMapNodeViewSet.as_view({'get': 'simple_mind_map_format'})),
    path('api/projects/<int:project_pk>/nodes/logs/', MindMapNodeViewSet.as_view({'get': 'logs'})),
    path('api/projects/<int:project_pk>/nodes/stats/', MindMapNodeViewSet.as_view({'get': 'user_stats'})),
]
