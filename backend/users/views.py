from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model, authenticate, login, logout
from .serializers import UserSerializer, UserCreateSerializer
from projects.models import ProjectMember
from mindmaps.models import MindMapNode

User = get_user_model()

@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
    """获取CSRF token"""
    return JsonResponse({
        'detail': 'CSRF cookie set',
        'success': True
    })

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """获取当前用户信息"""
        if not request.user.is_authenticated:
            return Response({'error': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """用户登录"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': '用户名和密码不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            serializer = UserSerializer(user)
            return Response({
                'user': serializer.data,
                'message': '登录成功'
            })
        else:
            return Response(
                {'error': '用户名或密码错误'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """用户登出"""
        logout(request)
        return Response({'message': '登出成功'})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def dashboard(self, request):
        """获取用户仪表板数据"""
        if not request.user.is_authenticated:
            return Response({'error': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user
        
        # 获取参与的项目
        member_projects = ProjectMember.objects.filter(user=user).select_related('project')
        
        # 统计数据
        projects_data = []
        total_nodes = 0
        
        for member in member_projects:
            project = member.project
            user_nodes = MindMapNode.objects.filter(project=project, creator=user)
            node_count = user_nodes.count()
            total_nodes += node_count
            
            projects_data.append({
                'id': project.id,
                'name': project.name,
                'permission': member.permission,
                'joined_at': member.joined_at,
                'user_nodes_count': node_count,
                'total_nodes_count': project.nodes.count(),
                'last_updated': project.updated_at
            })
        
        return Response({
            'projects': projects_data,
            'total_projects': len(projects_data),
            'total_nodes_created': total_nodes,
            'user_info': UserSerializer(user).data
        })
