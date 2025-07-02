# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile

# Django REST Framework imports
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

# Third-party imports
import json
import jwt
import datetime

# Local imports
from .serializers import UserSerializer, UserCreateSerializer
from .models import LoginAttempt
from projects.models import ProjectMember
from mindmaps.models import MindMapNode

CustomUser = get_user_model()

@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
    """获取CSRF token"""
    return JsonResponse({
        'detail': 'CSRF cookie set',
        'success': True
    })

class UserViewSet(viewsets.ModelViewSet):
    """
    用户管理的ViewSet
    提供用户注册、登录、人脸识别、审核等功能
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        """处理请求分发"""
        response = super().dispatch(request, *args, **kwargs)
        return response
    
    def get_permissions(self):
        """根据不同的action设置不同的权限"""
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['pending_users', 'admin_users']:
            # 管理员功能需要认证权限
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        """根据不同的action返回不同的序列化器"""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        """用户注册"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': '注册成功，请录入人脸信息',
                'user_id': user.id,
                'temp_token': f"register_{user.id}",  # 临时token用于人脸录入
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """获取当前用户信息"""
        print(f'Getting profile for user: {request.user.username if request.user.is_authenticated else "AnonymousUser"}')
        print(f'User is_authenticated: {request.user.is_authenticated}')
        
        if not request.user.is_authenticated:
            return Response({'error': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """用户登录 - 第一步：验证账号密码"""
        police_number = request.data.get('police_number') or request.data.get('username')
        password = request.data.get('password')
        
        if not police_number or not password:
            return Response(
                {'error': '警号和密码不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 使用警号查找用户
        try:
            user_obj = CustomUser.objects.get(police_number=police_number)
            # 使用用户名进行认证
            user = authenticate(request, username=user_obj.username, password=password)
        except CustomUser.DoesNotExist:
            user = None
        
        if not user:
            return Response(
                {'error': '警号或密码错误'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 检查用户状态
        if not user.is_approved():
            return Response(
                {'error': '您的账户尚未通过审核，请联系管理员'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user.status == 'suspended':
            return Response(
                {'error': '您的账户已被暂停，请联系管理员'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查是否已录入人脸
        if not user.is_face_registered:
            return Response({
                'step': 'face_registration_required',
                'message': '需要先录入人脸信息',
                'user_id': user.id,
                'police_number': user.police_number
            }, status=status.HTTP_200_OK)
        
        # 密码验证成功，返回进入人脸识别步骤
        serializer = UserSerializer(user)
        return Response({
            'step': 'face_verification_required',
            'message': '密码验证成功，请进行人脸识别',
            'user': serializer.data,
            'session_token': self._generate_temp_session_token(user)
        }, status=status.HTTP_200_OK)
    
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
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def face_verify(self, request):
        """用户登录 - 第二步：前端人脸识别验证"""
        session_token = request.data.get('session_token')
        verification_result = request.data.get('verification_result')  # 前端人脸比对结果
        
        if not session_token or verification_result is None:
            return Response(
                {'error': '会话令牌和验证结果不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证临时会话令牌并获取用户
        user = self._verify_temp_session_token(session_token)
        if not user:
            return Response(
                {'error': '会话已过期，请重新登录'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 检查前端验证结果
        if verification_result.get('success'):
            # 人脸识别成功，完成登录
            login(request, user)
            
            # 记录登录尝试
            self._log_login_attempt(
                user, 'combined', 'success', 
                request.META.get('REMOTE_ADDR', ''),
                request.META.get('HTTP_USER_AGENT', ''),
                face_confidence=verification_result.get('confidence', 0.0)
            )
            
            serializer = UserSerializer(user)
            return Response({
                'user': serializer.data,
                'message': '登录成功',
                'face_confidence': verification_result.get('confidence', 0.0)
            })
        else:
            # 人脸识别失败
            failure_reason = verification_result.get('reason', '人脸验证失败')
            self._log_login_attempt(
                user, 'face', 'failed', 
                request.META.get('REMOTE_ADDR', ''),
                request.META.get('HTTP_USER_AGENT', ''),
                failure_reason=failure_reason,
                face_confidence=verification_result.get('confidence', 0.0)
            )
            
            return Response(
                {'error': f'人脸识别失败：{failure_reason}'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_face(self, request):
        """人脸特征录入接口 - 通过请求体中的user_id"""
        user_id = request.data.get('user_id')
        face_encodings = request.data.get('face_encodings')  # 前端提取的人脸特征数据
        
        if not user_id or not face_encodings:
            return Response(
                {'error': '用户ID和人脸特征数据不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': '用户不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查临时token权限（用于注册后的人脸录入）
        temp_token = request.data.get('temp_token')
        if temp_token and temp_token == f"register_{user.id}":
            # 注册流程中的人脸录入，允许访问
            pass
        elif request.user.is_authenticated and (request.user == user or request.user.is_staff):
            # 已登录的用户录入自己的人脸或管理员操作
            pass
        else:
            return Response({'error': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
        
        # 保存人脸特征数据
        try:
            # 验证 face_encodings 格式
            if isinstance(face_encodings, str):
                face_encodings = json.loads(face_encodings)
            
            if not isinstance(face_encodings, list) or len(face_encodings) == 0:
                return Response({'error': '人脸特征数据格式错误'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 保存人脸特征
            user.set_face_encodings(face_encodings)
            user.save()
            
            return Response({
                'message': '人脸特征录入成功',
                'face_registered': user.is_face_registered,
                'encodings_count': len(face_encodings)
            })
            
        except (json.JSONDecodeError, ValueError) as e:
            return Response(
                {'error': f'人脸特征数据格式错误：{str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending_users(self, request):
        """获取待审核用户列表 - 仅管理员可访问"""
        print(f'Fetching pending users for user: {request.user.username if request.user.is_authenticated else "AnonymousUser"}')
        print(f'User is_staff: {request.user.is_staff if request.user.is_authenticated else False}')
        print(f'User is_superuser: {request.user.is_superuser if request.user.is_authenticated else False}')
        print(f'User is_authenticated: {request.user.is_authenticated}')
        
        if not request.user.is_authenticated:
            return Response({'error': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
            
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
        
        pending_users = CustomUser.objects.filter(status='pending').order_by('-date_joined')
        serializer = UserSerializer(pending_users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve_user(self, request, pk=None):
        """审核用户 - 仅管理员可操作"""
        if not request.user.is_staff:
            return Response({'error': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object()
        from .serializers import UserApprovalSerializer
        
        serializer = UserApprovalSerializer(
            user, 
            data=request.data, 
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': '用户状态更新成功',
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny], url_path='register-face')
    def register_face_for_user(self, request, pk=None):
        """用户人脸特征录入 - 通过URL中的用户ID"""
        user = self.get_object()
        
        # 检查用户是否有权限录入人脸（自己或管理员）
        if request.user.is_authenticated:
            if request.user != user and not request.user.is_staff:
                return Response({'error': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
        else:
            # 未登录用户只能为刚注册的用户录入人脸（通过临时token验证）
            temp_token = request.data.get('temp_token')
            if not temp_token or temp_token != f"register_{user.id}":
                return Response({'error': '无效的临时token'}, status=status.HTTP_403_FORBIDDEN)
        
        face_encodings = request.data.get('face_encodings')
        if not face_encodings:
            return Response({'error': '请提供人脸特征数据'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 保存人脸特征数据
        try:
            # 验证 face_encodings 格式
            if isinstance(face_encodings, str):
                face_encodings = json.loads(face_encodings)
            
            if not isinstance(face_encodings, list) or len(face_encodings) == 0:
                return Response({'error': '人脸特征数据格式错误'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 保存人脸特征
            user.set_face_encodings(face_encodings)
            user.save()
            
            return Response({
                'message': '人脸特征录入成功',
                'face_registered': user.is_face_registered,
                'encodings_count': len(face_encodings)
            })
            
        except (json.JSONDecodeError, ValueError) as e:
            return Response({
                'error': f'人脸特征数据格式错误：{str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def admin_users(self, request):
        """获取所有用户列表 - 仅管理员可访问"""
        if not (request.user.is_superuser or request.user.is_staff):
            return Response({'error': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
        
        # 获取所有非超级用户
        users = CustomUser.objects.filter(is_superuser=False).order_by('-date_joined')
        
        # 按状态筛选
        status_filter = request.query_params.get('status')
        if status_filter and status_filter != 'all':
            users = users.filter(status=status_filter)
        
        # 搜索功能
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            users = users.filter(
                Q(username__icontains=search) |
                Q(real_name__icontains=search) |
                Q(police_number__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        serializer = UserSerializer(users, many=True)
        
        # 统计数据
        stats = {
            'total': CustomUser.objects.filter(is_superuser=False).count(),
            'pending': CustomUser.objects.filter(status='pending').count(),
            'approved': CustomUser.objects.filter(status='approved').count(),
            'rejected': CustomUser.objects.filter(status='rejected').count(),
            'suspended': CustomUser.objects.filter(status='suspended').count(),
        }
        
        return Response({
            'users': serializer.data,
            'stats': stats
        })

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_face_encodings(self, request):
        """获取用户人脸特征数据供前端进行比对"""
        police_number = request.data.get('police_number')
        
        if not police_number:
            return Response(
                {'error': '警号不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CustomUser.objects.get(police_number=police_number)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': '用户不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查用户状态
        if not user.is_approved():
            return Response(
                {'error': '您的账户尚未通过审核'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not user.is_face_registered:
            return Response(
                {'error': '用户未录入人脸信息'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        face_encodings = user.get_face_encodings()
        if not face_encodings:
            return Response(
                {'error': '未找到人脸特征数据'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'face_encodings': face_encodings,
            'user_id': user.id,
            'police_number': user.police_number
        })

    def _generate_temp_session_token(self, user):
        """生成临时会话令牌"""
        payload = {
            'user_id': user.id,
            'police_number': user.police_number,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5),  # 5分钟过期
            'purpose': 'face_verification'
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    def _verify_temp_session_token(self, token):
        """验证临时会话令牌"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('purpose') != 'face_verification':
                return None
                
            user = CustomUser.objects.get(id=payload['user_id'])
            return user
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, CustomUser.DoesNotExist):
            return None
    
    def _log_login_attempt(self, user, attempt_type, result, ip_address, user_agent, failure_reason='', face_confidence=None):
        """记录登录尝试"""
        LoginAttempt.objects.create(
            user=user,
            police_number=user.police_number,
            attempt_type=attempt_type,
            result=result,
            ip_address=ip_address or '127.0.0.1',
            user_agent=user_agent,
            failure_reason=failure_reason,
            face_confidence=face_confidence
        )

# ===========================================
# CSRF豁免的独立API视图 (用于前端无token调用)
# ===========================================
@csrf_exempt
@require_http_methods(["POST"])
def verify_identity_api(request):
    """
    验证用户身份用于人脸补录 - CSRF豁免版本
    用于用户在人脸补录流程中的身份验证
    需要提供警号、密码和手机号进行三重验证
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    police_number = data.get('police_number')
    password = data.get('password')
    phone_number = data.get('phone_number')
    
    if not all([police_number, password, phone_number]):
        return JsonResponse({'error': '请提供完整的验证信息'}, status=400)
    
    try:
        # 查找用户
        user = CustomUser.objects.get(police_number=police_number)
        
        # 验证密码
        if not user.check_password(password):
            return JsonResponse({'error': '密码错误'}, status=401)
        
        # 验证手机号
        if user.phone_number != phone_number:
            return JsonResponse({'error': '手机号码不匹配'}, status=401)
        
        return JsonResponse({
            'message': '身份验证成功',
            'user': UserSerializer(user).data
        })
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': '用户不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'验证失败: {str(e)}'}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def supplement_face_api(request):
    """
    人脸信息补录 - CSRF豁免版本
    用于用户重新录入人脸特征信息
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    user_id = data.get('user_id')
    face_encodings = data.get('face_encodings', [])
    
    if not user_id:
        return JsonResponse({'error': '请提供用户ID'}, status=400)
        
    if not face_encodings or len(face_encodings) == 0:
        return JsonResponse({'error': '请提供人脸特征数据'}, status=400)
    
    try:
        user = CustomUser.objects.get(id=user_id)
        
        # 保存新的人脸特征数据
        user.set_face_encodings(face_encodings)
        user.save()
        
        return JsonResponse({
            'message': '人脸信息补录成功',
            'face_registered': user.is_face_registered,
            'encodings_count': len(face_encodings)
        })
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': '用户不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'人脸补录失败: {str(e)}'}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def admin_login_api(request):
    """
    管理员登录验证API
    用于管理员专用登录页面的身份验证
    验证成功后建立Django session用于后续管理操作
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'error': '请提供用户名和密码'}, status=400)
        
        # 验证用户是否存在且为管理员
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': '管理员账户不存在'}, status=404)
        
        # 检查密码
        if not user.check_password(password):
            return JsonResponse({'error': '密码错误'}, status=401)
        
        # 检查是否为管理员
        if not (user.is_superuser or user.is_staff):
            return JsonResponse({'error': '您不是系统管理员'}, status=403)
        
        # 执行Django登录，建立session
        login(request, user)
        
        # 验证成功，返回完整的用户信息
        return JsonResponse({
            'success': True,
            'message': '管理员验证成功',
            'admin_url': '/admin/',
            'user': UserSerializer(user).data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'验证失败: {str(e)}'}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def test_auth_status(request):
    """
    测试认证状态API
    用于调试session和认证问题
    返回当前用户的认证状态和session信息
    """
    return JsonResponse({
        'is_authenticated': request.user.is_authenticated,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'username': request.user.username if request.user.is_authenticated else None,
        'is_staff': request.user.is_staff if request.user.is_authenticated else False,
        'is_superuser': request.user.is_superuser if request.user.is_authenticated else False,
        'session_key': request.session.session_key,
        'session_data': dict(request.session) if hasattr(request, 'session') else {}
    })
