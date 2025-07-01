from django.db import models
from django.conf import settings
from projects.models import Project
import json

class MindMapNode(models.Model):
    """思维导图节点模型"""
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='nodes',
        verbose_name='所属项目'
    )
    node_id = models.CharField(max_length=100, verbose_name='节点ID')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='children',
        verbose_name='父节点'
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_nodes',
        verbose_name='创建者'
    )
    
    # 节点内容
    text = models.TextField(verbose_name='节点文本')
    image = models.URLField(blank=True, null=True, verbose_name='节点图片')
    hyperlink = models.URLField(blank=True, null=True, verbose_name='超链接')
    note = models.TextField(blank=True, verbose_name='备注')
    
    # 节点样式
    background_color = models.CharField(max_length=7, default='#ffffff', verbose_name='背景色')
    font_color = models.CharField(max_length=7, default='#000000', verbose_name='字体颜色')
    font_size = models.IntegerField(default=14, verbose_name='字体大小')
    font_weight = models.CharField(max_length=10, default='normal', verbose_name='字体粗细')
    
    # 位置信息
    position_x = models.FloatField(default=0, verbose_name='X坐标')
    position_y = models.FloatField(default=0, verbose_name='Y坐标')
    
    # 扩展数据
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='扩展数据')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '思维导图节点'
        verbose_name_plural = '思维导图节点'
        unique_together = ('project', 'node_id')
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.project.name} - {self.text[:20]}'
    
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
    
    def to_simple_mind_map_format(self):
        """转换为simple-mind-map格式"""
        data = {
            'data': {
                'text': self.text,
                'uid': self.node_id,
                'image': self.image or '',
                'hyperlink': self.hyperlink or '',
                'note': self.note or '',
                'backgroundColor': self.background_color,
                'color': self.font_color,
                'fontSize': self.font_size,
                'fontWeight': self.font_weight,
                'creator': self.creator.username,
                'created_at': self.created_at.isoformat(),
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
        return f'{self.user.username} {self.get_action_display()} {self.node.text[:20]}'
