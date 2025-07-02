from django.db import models
from django.conf import settings
import os
from django.utils import timezone


def case_attachment_upload_path(instance, filename):
    """案件附件上传路径"""
    # 按案件编号和日期组织文件路径
    date_str = timezone.now().strftime('%Y%m%d')
    return f'case_attachments/{instance.project.case_number}/{date_str}/{filename}'

class Project(models.Model):
    """案件模型"""
    
    # 公安单位选择
    UNIT_CHOICES = [
        ('direct', '直属单位'),
        ('tianyuan', '天元分局'),
        ('lusong', '芦淞分局'),
        ('hetang', '荷塘分局'),
        ('shifeng', '石峰分局'),
        ('dongjiaba', '董家塅分局'),
        ('economic', '经开区分局'),
        ('lukou', '渌口分局'),
        ('liling', '醴陵市公安局'),
        ('youxian', '攸县公安局'),
        ('chaling', '茶陵县公安局'),
        ('yanling', '炎陵县公安局'),
    ]
    
    PERMISSION_CHOICES = [
        ('read', '只读'),
        ('edit', '编辑'),
        ('admin', '管理员'),
    ]
    
    # 案件基本信息
    name = models.CharField(max_length=200, verbose_name='案件名称')
    case_number = models.CharField(max_length=50, unique=True, verbose_name='案件编号')
    filing_unit = models.CharField(max_length=20, choices=UNIT_CHOICES, verbose_name='立案单位')
    case_summary = models.TextField(verbose_name='简要案情')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_projects',
        verbose_name='创建人'
    )
    
    # 成员关系
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        through='ProjectMember',
        related_name='projects',
        verbose_name='参与人员'
    )
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '案件'
        verbose_name_plural = '案件'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name}({self.case_number})"
    
    def get_filing_unit_display_name(self):
        """获取立案单位显示名称"""
        return dict(self.UNIT_CHOICES).get(self.filing_unit, self.filing_unit)

class ProjectMember(models.Model):
    """案件参与人员关系模型"""
    PERMISSION_CHOICES = [
        ('read', '只读'),
        ('edit', '编辑'), 
        ('admin', '管理员'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='案件')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='参与人员')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='read', verbose_name='权限')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='加入时间')
    
    class Meta:
        unique_together = ('project', 'user')
        verbose_name = '案件参与人员'
        verbose_name_plural = '案件参与人员'
    
    def __str__(self):
        return f'{self.user.real_name} - {self.project.name} ({self.get_permission_display()})'

class CaseAttachment(models.Model):
    """案件附件模型"""
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='case_attachments',
        verbose_name='所属案件'
    )
    file = models.FileField(
        upload_to=case_attachment_upload_path,
        verbose_name='附件文件'
    )
    original_name = models.CharField(max_length=255, verbose_name='原始文件名')
    file_size = models.PositiveIntegerField(verbose_name='文件大小(字节)')
    file_type = models.CharField(max_length=100, verbose_name='文件类型')
    description = models.TextField(blank=True, verbose_name='文件描述')
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_attachments',
        verbose_name='上传者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    
    class Meta:
        verbose_name = '案件附件'
        verbose_name_plural = '案件附件'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.project.name} - {self.original_name}'
    
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
