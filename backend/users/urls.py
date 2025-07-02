from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, get_csrf_token, verify_identity_api, supplement_face_api, admin_login_api, test_auth_status

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('api/csrf/', get_csrf_token, name='csrf'),
    path('api/users/verify-identity-supplement/', verify_identity_api, name='verify_identity_api'),
    path('api/users/supplement-face/', supplement_face_api, name='supplement_face_api'),
    path('api/users/admin-login/', admin_login_api, name='admin_login_api'),
    path('api/test-auth/', test_auth_status, name='test_auth_status'),
    path('api/', include(router.urls)),
]
