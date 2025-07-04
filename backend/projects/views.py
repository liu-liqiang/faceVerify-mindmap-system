from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from .models import Project, ProjectMember, CaseAttachment
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, 
    ProjectMemberSerializer, ProjectMemberInviteSerializer,
    CaseAttachmentSerializer
)

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_queryset(self):
        # 返回用户参与的项目（通过ProjectMember关系）
        return Project.objects.filter(
            projectmember__user=self.request.user
        ).distinct().order_by('-updated_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action == 'upload_attachment':
            return CaseAttachmentSerializer
        return ProjectSerializer
    
    def create(self, request, *args, **kwargs):
        """创建新案件项目"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        
        # 处理附件上传
        attachments = request.FILES.getlist('attachments')
        for attachment_file in attachments:
            CaseAttachment.objects.create(
                project=project,
                file=attachment_file,
                original_name=attachment_file.name,
                file_size=attachment_file.size,
                file_type=attachment_file.content_type or 'unknown',
                uploader=request.user,
                description=''  # 可以从表单获取描述
            )
        
        # 返回完整的项目信息
        response_serializer = ProjectSerializer(project, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def invite_member(self, request, pk=None):
        """邀请用户加入项目"""
        project = self.get_object()
        
        # 检查权限（只有项目创建者和思维导图管理员可以邀请）
        if project.creator != request.user:
            try:
                member = ProjectMember.objects.get(project=project, user=request.user)
                if member.permission != 'admin':
                    return Response(
                        {'error': '没有权限邀请成员，只有项目创建者和思维导图管理员可以邀请成员'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ProjectMember.DoesNotExist:
                return Response(
                    {'error': '你不是项目成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = ProjectMemberInviteSerializer(
            data=request.data, 
            context={'project': project}
        )
        if serializer.is_valid():
            member = serializer.save()
            return Response(
                ProjectMemberSerializer(member).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """获取项目成员列表"""
        project = self.get_object()
        members = ProjectMember.objects.filter(project=project).select_related('user')
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """移除项目成员"""
        project = self.get_object()
        username = request.data.get('username')
        
        if not username:
            return Response(
                {'error': '用户名不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查权限（只有项目创建者和思维导图管理员可以移除成员）
        if project.creator != request.user:
            try:
                current_member = ProjectMember.objects.get(project=project, user=request.user)
                if current_member.permission != 'admin':
                    return Response(
                        {'error': '没有权限移除成员，只有项目创建者和思维导图管理员可以移除成员'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ProjectMember.DoesNotExist:
                return Response(
                    {'error': '你不是项目成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # 不能移除项目创建者
        if project.creator.username == username:
            return Response(
                {'error': '不能移除项目创建者'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user_to_remove = User.objects.get(username=username)
            member_to_remove = ProjectMember.objects.get(project=project, user=user_to_remove)
            member_to_remove.delete()
            return Response({'message': '成员移除成功'})
        except (User.DoesNotExist, ProjectMember.DoesNotExist):
            return Response(
                {'error': '用户不存在或不是项目成员'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['put'])
    def update_member_permission(self, request, pk=None):
        """更新成员权限"""
        project = self.get_object()
        username = request.data.get('username')
        permission = request.data.get('permission')
        
        if not username or not permission:
            return Response(
                {'error': '用户名和权限不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查权限（只有项目创建者和思维导图管理员可以修改成员权限）
        if project.creator != request.user:
            try:
                current_member = ProjectMember.objects.get(project=project, user=request.user)
                if current_member.permission != 'admin':
                    return Response(
                        {'error': '没有权限修改成员权限，只有项目创建者和思维导图管理员可以修改成员权限'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ProjectMember.DoesNotExist:
                return Response(
                    {'error': '你不是项目成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # 不能修改项目创建者权限
        if project.creator.username == username:
            return Response(
                {'error': '不能修改项目创建者权限'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(username=username)
            member = ProjectMember.objects.get(project=project, user=user)
            member.permission = permission
            member.save()
            return Response(ProjectMemberSerializer(member).data)
        except (User.DoesNotExist, ProjectMember.DoesNotExist):
            return Response(
                {'error': '用户不存在或不是项目成员'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_attachment(self, request, pk=None):
        """上传案件附件"""
        project = self.get_object()
        
        # 检查权限：项目创建者或有编辑权限以上的成员可以上传附件
        if project.creator != request.user:
            try:
                member = ProjectMember.objects.get(project=project, user=request.user)
                if member.permission == 'read':
                    return Response(
                        {'error': '没有上传附件的权限，需要编辑或管理员权限'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ProjectMember.DoesNotExist:
                return Response(
                    {'error': '你不是项目成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # 文件大小限制 (300MB)
        max_file_size = 300 * 1024 * 1024
        uploaded_file = request.FILES.get('file')
        
        if not uploaded_file:
            return Response(
                {'error': '请选择要上传的文件'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if uploaded_file.size > max_file_size:
            return Response(
                {'error': f'文件大小不能超过300MB，当前文件大小: {uploaded_file.size / (1024*1024):.1f}MB'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 移除文件类型限制，允许上传任何类型的文件
        
        # 打印请求信息以便调试
        print(f"上传附件请求数据: POST={request.POST.keys()}, FILES={request.FILES.keys()}")
        print(f"上传的文件信息: name={uploaded_file.name}, size={uploaded_file.size}, content_type={uploaded_file.content_type}")
        
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print(f"序列化器验证错误: {serializer.errors}")
                return Response(
                    {'error': f'数据验证失败: {serializer.errors}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            attachment = serializer.save(project=project, uploader=request.user)
            print(f"附件保存成功: {attachment.id}")
        except Exception as e:
            import traceback
            print(f"保存附件时出错: {str(e)}")
            traceback.print_exc()
            return Response(
                {'error': f'保存文件时出错: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            CaseAttachmentSerializer(attachment).data, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """获取案件附件列表"""
        project = self.get_object()
        attachments = project.case_attachments.all()
        serializer = CaseAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='attachments/(?P<attachment_id>[^/.]+)/download')
    def download_attachment(self, request, pk=None, attachment_id=None):
        """下载案件附件"""
        from django.http import HttpResponse, Http404
        from django.utils.encoding import escape_uri_path
        import os
        import mimetypes
        
        project = self.get_object()
        
        try:
            attachment = project.case_attachments.get(id=attachment_id)
        except CaseAttachment.DoesNotExist:
            raise Http404("附件不存在")
        
        # 检查文件是否存在
        if not attachment.file or not os.path.exists(attachment.file.path):
            raise Http404("文件不存在")
        
        # 获取文件信息
        file_path = attachment.file.path
        file_size = os.path.getsize(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        
        if not content_type:
            content_type = 'application/octet-stream'
        
        # 创建响应
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Length'] = file_size
            response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{escape_uri_path(attachment.original_name)}'
            return response

    @action(detail=True, methods=['delete'], url_path='attachments/(?P<attachment_id>[^/.]+)')
    def delete_attachment(self, request, pk=None, attachment_id=None):
        """删除案件附件"""
        from django.http import Http404
        import os
        
        project = self.get_object()
        
        # 检查权限：项目创建者、上传者本人或思维导图管理员可以删除附件
        if project.creator != request.user:
            try:
                member = ProjectMember.objects.get(project=project, user=request.user)
                try:
                    attachment = project.case_attachments.get(id=attachment_id)
                except CaseAttachment.DoesNotExist:
                    raise Http404("附件不存在")
                
                # 只有上传者本人或者思维导图管理员可以删除
                if attachment.uploader != request.user and member.permission != 'admin':
                    return Response(
                        {'error': '没有删除此附件的权限，只有上传者本人或思维导图管理员可以删除'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ProjectMember.DoesNotExist:
                return Response(
                    {'error': '你不是项目成员'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # 项目创建者可以删除任何附件
            try:
                attachment = project.case_attachments.get(id=attachment_id)
            except CaseAttachment.DoesNotExist:
                raise Http404("附件不存在")
        
        # 删除文件
        if attachment.file and os.path.exists(attachment.file.path):
            try:
                os.remove(attachment.file.path)
            except OSError:
                pass  # 文件删除失败，但仍然删除数据库记录
        
        # 删除数据库记录
        attachment.delete()
        
        return Response({'message': '附件删除成功'}, status=status.HTTP_200_OK)
