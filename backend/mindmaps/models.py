from django.db import models
from django.conf import settings
from django.utils import timezone
from projects.models import Project
import json
import os


def node_attachment_upload_path(instance, filename):
    """节点附件上传路径"""
    # 按案件编号和节点ID组织文件路径
    date_str = timezone.now().strftime('%Y%m%d')
    return f'node_attachments/{instance.node.project.case_number}/{instance.node.node_id}/{date_str}/{filename}'

class MindMapNode(models.Model):
    """思维导图节点模型"""
    
    # 基本信息
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='nodes',
        verbose_name='所属案件'
    )
    node_id = models.CharField(max_length=100, verbose_name='节点ID')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='children',
        verbose_name='父级节点'
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_nodes',
        verbose_name='创建者'
    )
    
    # 节点内容
    content = models.TextField(verbose_name='节点内容')
    icon = models.CharField(max_length=50, blank=True, verbose_name='图标')
    note = models.TextField(blank=True, verbose_name='备注')
    
    # 超链接
    hyperlink = models.URLField(blank=True, null=True, verbose_name='超链接')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 其他扩展数据（保留原有的样式等信息）
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='扩展数据')
    
    class Meta:
        verbose_name = '思维导图节点'
        verbose_name_plural = '思维导图节点'
        unique_together = ('project', 'node_id')
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.project.name} - {self.content[:20]}'
    
    def get_children_count(self):
        """获取子节点数量"""
        return self.children.count()
    
    def can_be_deleted_by(self, user):
        """检查是否可以被指定用户删除"""
        # 只能删除自己创建的节点
        if self.creator != user:
            return False
        # 不能删除有子节点的节点
        if self.children.exists():
            return False
        return True
    
    def add_attachment(self, file_name, file_url):
        """添加附件"""
        if not self.attachments:
            self.attachments = []
        attachment = {
            'name': file_name,
            'url': file_url,
            'uploaded_at': timezone.now().isoformat()
        }
        self.attachments.append(attachment)
        self.save()
    
    def to_simple_mind_map_format(self):
        """转换为simple-mind-map格式"""
        data = {
            'data': {
                'text': self.content,
                'uid': self.node_id,
                'icon': self.icon or '',
                'hyperlink': self.hyperlink or '',
                'note': self.note or '',
                'creator': self.creator.real_name,
                'created_at': self.created_at.isoformat(),
                'attachments': self.attachments,
                **self.extra_data
            },
            'children': []
        }
        
        # 递归添加子节点
        for child in self.children.all().order_by('created_at'):
            data['children'].append(child.to_simple_mind_map_format())
        
        return data

class NodeEditLog(models.Model):
    """节点编辑日志"""
    ACTION_CHOICES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
    ]
    
    node = models.ForeignKey(
        MindMapNode, 
        on_delete=models.CASCADE,
        related_name='edit_logs',
        verbose_name='节点'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='操作用户'
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name='操作类型')
    old_data = models.JSONField(null=True, blank=True, verbose_name='旧数据')
    new_data = models.JSONField(null=True, blank=True, verbose_name='新数据')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')
    
    class Meta:
        verbose_name = '节点编辑日志'
        verbose_name_plural = '节点编辑日志'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f'{self.user.real_name} {self.get_action_display()} {self.node.content[:20]}'

class NodeAttachment(models.Model):
    """思维导图节点附件模型"""
    node = models.ForeignKey(
        MindMapNode, 
        on_delete=models.CASCADE, 
        related_name='node_attachments',
        verbose_name='所属节点'
    )
    file = models.FileField(
        upload_to=node_attachment_upload_path,
        verbose_name='附件文件'
    )
    original_name = models.CharField(max_length=255, verbose_name='原始文件名')
    file_size = models.PositiveIntegerField(verbose_name='文件大小(字节)')
    file_type = models.CharField(max_length=100, verbose_name='文件类型')
    description = models.TextField(blank=True, verbose_name='文件描述')
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_node_attachments',
        verbose_name='上传者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    
    class Meta:
        verbose_name = '节点附件'
        verbose_name_plural = '节点附件'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.node.content[:20]} - {self.original_name}'
    
    def get_file_size_display(self):
        """获取友好的文件大小显示"""
        size = self.file_size
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        elif size < 1024 * 1024 * 1024:
            return f'{size / (1024 * 1024):.1f} MB'
        else:
            return f'{size / (1024 * 1024 * 1024):.1f} GB'
    
    def delete(self, *args, **kwargs):
        """删除附件时同时删除文件"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
