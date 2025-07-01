from django.db import models
from django.conf import settings

class Project(models.Model):
    """项目模型"""
    PERMISSION_CHOICES = [
        ('read', '只读'),
        ('edit', '编辑'),
        ('admin', '管理员'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='项目名称')
    description = models.TextField(blank=True, verbose_name='项目描述')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_projects',
        verbose_name='创建者'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        through='ProjectMember',
        related_name='projects',
        verbose_name='成员'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '项目'
        verbose_name_plural = '项目'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name

class ProjectMember(models.Model):
    """项目成员关系模型"""
    PERMISSION_CHOICES = [
        ('read', '只读'),
        ('edit', '编辑'), 
        ('admin', '管理员'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='read')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('project', 'user')
        verbose_name = '项目成员'
        verbose_name_plural = '项目成员'
    
    def __str__(self):
        return f'{self.user.username} - {self.project.name} ({self.permission})'
