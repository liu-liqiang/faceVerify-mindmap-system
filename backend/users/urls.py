from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, get_csrf_token, verify_identity_api, supplement_face_api, admin_login_api, test_auth_status

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('csrf/', get_csrf_token, name='csrf'),
    path('test-auth/', test_auth_status, name='test_auth_status'),
    # 专用API端点（必须放在router之前，以避免被ViewSet路由拦截）
    path('users/verify-identity-supplement/', verify_identity_api, name='verify_identity_api'),
    path('users/supplement-face/', supplement_face_api, name='supplement_face_api'),
    path('users/admin-login/', admin_login_api, name='admin_login_api'),
    path('users/by-police-number/<str:police_number>/', UserViewSet.as_view({'get': 'get_by_police_number'}), name='get_user_by_police_number'),
    path('', include(router.urls)),
]
