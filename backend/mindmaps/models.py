from django.db import models
from django.conf import settings
from django.utils import timezone
from projects.models import Project
import json
import os
import uuid
import time

def node_attachment_upload_path(instance, filename):
    """节点附件上传路径"""
    # 按案件编号和节点ID组织文件路径
    date_str = timezone.now().strftime('%Y%m%d')
    return f'node_attachments/{instance.node.project.case_number}/{instance.node.node_id}/{date_str}/{filename}'

def node_image_upload_path(instance, filename):
    """节点图片上传路径"""
    date_str = timezone.now().strftime('%Y%m%d')
    return f'node_images/{instance.node.project.case_number}/{instance.node.node_id}/{date_str}/{filename}'

def node_file_upload_path(instance, filename):
    """节点文件上传路径"""
    date_str = timezone.now().strftime('%Y%m%d')
    return f'node_files/{instance.node.project.case_number}/{instance.node.node_id}/{date_str}/{filename}'

class MindMapNode(models.Model):
    """思维导图节点模型"""
    
    # 基本信息，不用向前端传送
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='nodes',
        verbose_name='所属案件'
    )
    # 节点ID由前端生成，确保唯一性
    node_id = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='节点ID',
        help_text='前端生成'
    )
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='children',
        verbose_name='父级节点'
    )
    
    # 新增：根节点标识
    is_root = models.BooleanField(default=False, verbose_name='是否为根节点')
    
    # 新增：是否为系统默认节点（不可删除和编辑内容）
    is_system_default = models.BooleanField(
        default=False, 
        verbose_name='系统默认节点',
        help_text='系统默认生成的节点，不能删除和修改内容，只能添加子节点'
    )
    
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_nodes',
        verbose_name='创建者'
    )
    
    # === Simple Mind Map 数据字段 ===
    
    # 节点文本内容
    text = models.TextField(verbose_name='节点文本')
    rich_text = models.BooleanField(default=False, verbose_name='是否富文本')
    expand = models.BooleanField(default=True, verbose_name='是否展开')
    
    # 图标（存储图标列表的JSON）
    icon = models.JSONField(default=list, blank=True, verbose_name='图标列表')
    
    # 图片（关联到图片模型）
    image = models.ForeignKey(
        'NodeImage', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='nodes',
        verbose_name='关联图片'
    )
    
    # 超链接
    hyperlink = models.URLField(blank=True, verbose_name='超链接地址')
    hyperlink_title = models.CharField(max_length=255, blank=True, verbose_name='超链接标题')
    
    # 备注
    note = models.TextField(blank=True, verbose_name='备注')
    
    # 附件（关联到文件模型）
    attachment = models.ForeignKey(
        'NodeFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nodes',
        verbose_name='关联附件'
    )

    # 标签
    tags = models.JSONField(default=list, blank=True, verbose_name='标签列表')

    # 概要
    generalizations = models.JSONField(default=list, blank=True, verbose_name='概要数据')
    
    # 关联线，存储目标节点ID列表
    associative_line_targets = models.JSONField(default=list, blank=True, verbose_name='关联线目标节点')
    associative_line_text = models.CharField(max_length=255, blank=True, verbose_name='关联线文本')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 样式和其他扩展数据
    style_data = models.JSONField(default=dict, blank=True, verbose_name='样式数据')
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='扩展数据')
    
    class Meta:
        verbose_name = '思维导图节点'
        verbose_name_plural = '思维导图节点'
        unique_together = ('project', 'node_id')
        # 确保每个项目只有一个根节点
        constraints = [
            models.UniqueConstraint(
                fields=['project'], 
                condition=models.Q(is_root=True),
                name='unique_root_per_project'
            )
        ]
        ordering = ['level', 'sort_order', 'created_at']
        indexes = [
            models.Index(fields=['project', 'parent']),
            models.Index(fields=['node_id']),
            models.Index(fields=['creator']),
            models.Index(fields=['level', 'sort_order']),
        ]
    
    def __str__(self):
        return f'{self.project.name} - {self.text[:20]}'
    
    @property
    def content(self):
        """为了兼容旧代码，保留 content 属性"""
        return self.text
    
    @content.setter
    def content(self, value):
        """为了兼容旧代码，保留 content 属性设置"""
        self.text = value
    
    def save(self, *args, **kwargs):
        """保存时的验证逻辑"""
        # 如果设置为根节点，则parent必须为None
        if self.is_root and self.parent is not None:
            raise ValueError("根节点不能有父节点")
        
        # 如果parent为None但不是根节点，则自动设置为根节点
        if self.parent is None and not self.is_root:
            existing_root = MindMapNode.objects.filter(
                project=self.project, 
                is_root=True
            ).exclude(pk=self.pk).first()
            
            if not existing_root:
                self.is_root = True
        
        # 设置层级
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
            
        # 如果节点ID为空，则自动生成
        if not self.node_id:
            self.node_id = generate_node_id()
        
        super().save(*args, **kwargs)
    
    def can_be_edited_by(self, user):
        """检查是否可以被指定用户编辑"""
        # 系统默认节点不能编辑内容，但可以添加子节点
        if self.is_system_default:
            return False
        
        # 创建者总是可以编辑非系统默认节点
        if self.creator == user:
            return True
        
        # 检查用户在项目中的权限
        from projects.models import ProjectMember
        try:
            member = ProjectMember.objects.get(project=self.project, user=user)
            # 只有管理员和编辑权限的用户可以编辑他人的节点
            return member.permission in ['admin', 'edit']
        except ProjectMember.DoesNotExist:
            return False
    
    def can_be_deleted_by(self, user):
        """检查是否可以被指定用户删除"""
        # 系统默认节点不能被删除
        if self.is_system_default:
            return False
        
        # 根节点不能被删除
        if self.is_root:
            return False
        
        # 只有创建者可以删除自己的节点
        if self.creator != user:
            return False
        
        # 不能删除有子节点的节点
        if self.children.exists():
            return False
        
        return True
    
    def can_add_children(self, user):
        """检查是否可以添加子节点"""
        from projects.models import ProjectMember
        try:
            member = ProjectMember.objects.get(project=self.project, user=user)
            # 有编辑权限及以上的用户可以添加子节点
            return member.permission in ['admin', 'edit']
        except ProjectMember.DoesNotExist:
            return False
    
    @classmethod
    def create_default_mindmap(cls, project):
        """为项目创建默认的思维导图结构"""
        creator = project.creator
        
        # 创建根节点（案件名称）
        root_node = cls.objects.create(
            project=project,
            node_id=f"root_{project.id}",
            creator=creator,
            text=project.name,
            is_root=True,
            is_system_default=True,
            style_data={
                'fontWeight': 'bold',
                'fontSize': 18,
                'backgroundColor': '#4CAF50',
                'color': '#ffffff'
            }
        )
        
        # 默认的子节点结构
        default_children = [
            {
                'text': '案件特点',
                'icon': ['star'],
                'style': {
                    'backgroundColor': '#2196F3',
                    'color': '#ffffff'
                }
            },
            {
                'text': '资金流',
                'icon': ['money'],
                'style': {
                    'backgroundColor': '#FF9800',
                    'color': '#ffffff'
                }
            },
            {
                'text': '信息流',
                'icon': ['message'],
                'style': {
                    'backgroundColor': '#9C27B0',
                    'color': '#ffffff'
                }
            },
            {
                'text': '网络流',
                'icon': ['network'],
                'style': {
                    'backgroundColor': '#F44336',
                    'color': '#ffffff'
                }
            }
        ]
        
        # 创建默认子节点
        for i, child_data in enumerate(default_children):
            cls.objects.create(
                project=project,
                node_id=f"default_{project.id}_{i+1}",
                parent=root_node,
                creator=creator,
                text=child_data['text'],
                icon=child_data['icon'],
                is_system_default=True,
                style_data=child_data['style']
            )
        
        return root_node
    
    @classmethod
    def get_root_node(cls, project):
        """获取指定项目的根节点"""
        return cls.objects.filter(project=project, is_root=True).first()
    
    def to_simple_mind_map_format(self, user=None):
        """转换为 Simple Mind Map 格式"""
        # 确保文本内容不为空
        text_content = self.text
        if not text_content or not text_content.strip():
            text_content = '新节点'
        
        # 获取标签数据
        tags = []
        for tag in self.tags.all():
            if tag.style_data:
                tags.append({
                    'text': tag.text,
                    'style': tag.style_data
                })
            else:
                tags.append(tag.text)
        
        # 获取概要数据
        generalizations = []
        for gen in self.generalizations.all():
            gen_data = {
                'text': gen.text,
                'richText': gen.rich_text,
            }
            gen_data.update(gen.style_data)
            generalizations.append(gen_data)
        
        data = {
            'data': {
                'text': text_content.strip(),
                'richText': self.rich_text,
                'expand': self.expand,
                'uid': str(self.node_id),
                'icon': self.icon if self.icon else [],
                'image': self.image_url,
                'imageTitle': self.image_title or '',
                'imageSize': self.image_size,
                'hyperlink': self.hyperlink or '',
                'hyperlinkTitle': self.hyperlink_title or '',
                'note': self.note or '',
                'attachmentUrl': self.attachment_file_url,
                'attachmentName': self.attachment.original_name if self.attachment else (self.attachment_name or ''),
                'tag': tags,
                'generalization': generalizations if generalizations else None,
                'associativeLineTargets': self.associative_line_targets if self.associative_line_targets else [],
                'associativeLineText': self.associative_line_text or '',
                
                # 元数据
                'creator': str(self.creator.real_name or self.creator.username),
                'createdAt': self.created_at.isoformat(),
                'updatedAt': self.updated_at.isoformat(),
                'isRoot': self.is_root,
                'isSystemDefault': self.is_system_default,
                'editable': self.can_be_edited_by(user) if user else False,
                'deletable': self.can_be_deleted_by(user) if user else False,
                'canAddChildren': self.can_add_children(user) if user else False,
            },
            'children': []
        }
        
        # 合并样式数据
        if self.style_data:
            data['data'].update(self.style_data)
        
        # 合并其他扩展数据
        if self.extra_data:
            data['data'].update(self.extra_data)
        
        # 递归添加子节点
        for child in self.children.all().order_by('sort_order', 'created_at'):
            data['children'].append(child.to_simple_mind_map_format(user))
        
        return data
    
    def is_descendant_of(self, ancestor):
        """检查是否是指定节点的后代"""
        current = self.parent
        while current:
            if current == ancestor:
                return True
            current = current.parent
        return False

    @classmethod
    def from_simple_mind_map_data(cls, project, data, parent=None, creator=None):
        """从 Simple Mind Map 数据创建节点"""
        node_data = data.get('data', {})
        
        # 提取样式数据
        style_fields = [
            'backgroundColor', 'color', 'fontSize', 'fontWeight', 'fontFamily',
            'borderWidth', 'borderColor', 'borderStyle', 'borderRadius',
            'paddingX', 'paddingY', 'marginX', 'marginY', 'opacity', 'shape'
        ]
        
        style_data = {}
        extra_data = {}
        
        for key, value in node_data.items():
            if key in style_fields:
                style_data[key] = value
            elif key not in [
                'text', 'richText', 'expand', 'uid', 'icon', 'image', 'imageTitle',
                'imageSize', 'hyperlink', 'hyperlinkTitle', 'note', 'attachmentUrl',
                'attachmentName', 'tag', 'generalization', 'associativeLineTargets',
                'associativeLineText', 'creator', 'createdAt', 'updatedAt',
                'isRoot', 'isSystemDefault', 'editable', 'deletable', 'canAddChildren'
            ]:
                extra_data[key] = value
        
        # 创建节点
        node = cls.objects.create(
            project=project,
            node_id=node_data.get('uid', f'node_{int(timezone.now().timestamp() * 1000)}'),
            parent=parent,
            creator=creator or project.creator,
            text=node_data.get('text', '新节点'),
            rich_text=node_data.get('richText', False),
            expand=node_data.get('expand', True),
            icon=node_data.get('icon', []),
            # image 字段将通过后续的图片处理设置
            image_title=node_data.get('imageTitle', ''),
            image_size=node_data.get('imageSize', {"width": 100, "height": 100, "custom": False}),
            hyperlink=node_data.get('hyperlink', ''),
            hyperlink_title=node_data.get('hyperlinkTitle', ''),
            note=node_data.get('note', ''),
            # attachment 字段将通过后续的文件处理设置
            attachment_url=node_data.get('attachmentUrl', ''),
            attachment_name=node_data.get('attachmentName', ''),
            associative_line_targets=node_data.get('associativeLineTargets', []),
            associative_line_text=node_data.get('associativeLineText', ''),
            is_root=parent is None,
            is_system_default=node_data.get('isSystemDefault', False),
            style_data=style_data,
            extra_data=extra_data
        )
        
        # 处理标签
        tag_data = node_data.get('tag', [])
        for tag_item in tag_data:
            if isinstance(tag_item, str):
                NodeTag.objects.create(node=node, text=tag_item)
            elif isinstance(tag_item, dict):
                NodeTag.objects.create(
                    node=node,
                    text=tag_item.get('text', ''),
                    style_data=tag_item.get('style', {})
                )
        
        # 处理概要
        generalization_data = node_data.get('generalization')
        if generalization_data:
            if not isinstance(generalization_data, list):
                generalization_data = [generalization_data]
            
            for i, gen_item in enumerate(generalization_data):
                style_data = {k: v for k, v in gen_item.items() if k not in ['text', 'richText']}
                NodeGeneralization.objects.create(
                    node=node,
                    text=gen_item.get('text', ''),
                    rich_text=gen_item.get('richText', False),
                    style_data=style_data,
                    sort_order=i
                )
        
        # 递归处理子节点
        children = data.get('children', [])
        for child_data in children:
            cls.from_simple_mind_map_data(project, child_data, node, creator)
        
        # 同步关联线数据到 AssociativeLine 表
        if node.associative_line_targets:
            node.sync_associative_lines()
        
        return node

    def set_image_from_url(self, image_url, title='', uploader=None):
        """从URL设置图片（如果需要的话，可以下载并保存）"""
        if image_url:
            # 这里可以实现从URL下载图片的逻辑
            # 目前先简单设置为空，实际使用时需要通过API上传图片文件
            pass
    
    def set_attachment_from_url(self, attachment_url, name='', uploader=None):
        """从URL设置附件（如果需要的话，可以下载并保存）"""
        if attachment_url:
            # 这里可以实现从URL下载文件的逻辑
            # 目前先简单设置attachment_url字段
            self.attachment_url = attachment_url
            if name:
                self.attachment_name = name
            self.save()
    
    @property
    def image_url(self):
        """获取图片URL（优先使用关联的图片文件）"""
        if self.image and self.image.file:
            return self.image.file.url
        return ''
    
    @property
    def attachment_file_url(self):
        """获取附件URL（优先使用关联的文件）"""
        if self.attachment and self.attachment.file:
            return self.attachment.file.url
        return self.attachment_url or ''

    def get_associative_target_nodes(self):
        """获取当前节点关联的目标节点列表"""
        if not self.associative_line_targets:
            return []
        
        # 通过 node_id 查找目标节点
        target_nodes = MindMapNode.objects.filter(
            project=self.project,
            node_id__in=self.associative_line_targets
        )
        return list(target_nodes)
    
    def add_associative_target(self, target_node_id):
        """添加关联线目标节点"""
        if not self.associative_line_targets:
            self.associative_line_targets = []
        
        if target_node_id not in self.associative_line_targets:
            self.associative_line_targets.append(target_node_id)
            self.save()
            
            # 同时在 AssociativeLine 表中创建记录
            AssociativeLine.objects.get_or_create(
                project=self.project,
                source_node=self,
                target_node_id=MindMapNode.objects.get(
                    project=self.project, 
                    node_id=target_node_id
                ).id,
                defaults={
                    'text': self.associative_line_text or '',
                    'creator': self.creator
                }
            )
    
    def remove_associative_target(self, target_node_id):
        """移除关联线目标节点"""
        if self.associative_line_targets and target_node_id in self.associative_line_targets:
            self.associative_line_targets.remove(target_node_id)
            self.save()
            
            # 同时删除 AssociativeLine 表中的记录
            try:
                target_node = MindMapNode.objects.get(
                    project=self.project, 
                    node_id=target_node_id
                )
                AssociativeLine.objects.filter(
                    source_node=self,
                    target_node=target_node
                ).delete()
            except MindMapNode.DoesNotExist:
                pass
    
    def get_incoming_associative_nodes(self):
        """获取指向当前节点的关联线来源节点"""
        # 查找所有将当前节点作为目标的节点
        source_nodes = MindMapNode.objects.filter(
            project=self.project,
            associative_line_targets__contains=[self.node_id]
        )
        return list(source_nodes)
    
    def sync_associative_lines(self):
        """同步关联线数据到 AssociativeLine 表"""
        # 删除当前节点的所有关联线记录
        AssociativeLine.objects.filter(source_node=self).delete()
        
        # 重新创建关联线记录
        if self.associative_line_targets:
            targets_to_remove = []
            for target_node_id in self.associative_line_targets:
                try:
                    target_node = MindMapNode.objects.get(
                        project=self.project,
                        node_id=target_node_id
                    )
                    AssociativeLine.objects.create(
                        project=self.project,
                        source_node=self,
                        target_node=target_node,
                        text=self.associative_line_text or '',
                        creator=self.creator
                    )
                except MindMapNode.DoesNotExist:
                    # 如果目标节点不存在，标记为需要移除
                    targets_to_remove.append(target_node_id)
            
            # 移除不存在的目标节点
            if targets_to_remove:
                for target_id in targets_to_remove:
                    self.associative_line_targets.remove(target_id)
                self.save()
    
    def update_associative_lines(self, target_node_ids, line_text=''):
        """批量更新关联线目标节点"""
        # 确保传入的是列表
        if not isinstance(target_node_ids, list):
            target_node_ids = [target_node_ids] if target_node_ids else []
        
        # 更新 associative_line_targets 字段
        self.associative_line_targets = target_node_ids
        self.associative_line_text = line_text
        self.save()
        
        # 同步到 AssociativeLine 表
        self.sync_associative_lines()
    
    def clear_associative_lines(self):
        """清除所有关联线"""
        self.associative_line_targets = []
        self.associative_line_text = ''
        self.save()
        
        # 删除 AssociativeLine 表中的记录
        AssociativeLine.objects.filter(source_node=self).delete()
    
    def get_all_associations_data(self):
        """获取节点的所有关联信息（包括入向和出向）"""
        return {
            'outgoing': {
                'targets': self.associative_line_targets,
                'text': self.associative_line_text,
                'nodes': self.get_associative_target_nodes()
            },
            'incoming': {
                'sources': self.get_incoming_associative_nodes()
            }
        }

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
        return f'{self.user.real_name} {self.get_action_display()} {self.node.text[:20]}'

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
        return f'{self.node.text[:20]} - {self.original_name}'
    
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
    
    @property
    def attachment_url(self):
        """获取附件URL"""
        if self.file:
            return self.file.url
        return ''
    
    def delete(self, *args, **kwargs):
        """删除附件时同时删除文件"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

class NodeImage(models.Model):
    """思维导图节点图片模型"""
    node = models.ForeignKey(
        MindMapNode, 
        on_delete=models.CASCADE, 
        related_name='node_images',
        verbose_name='所属节点'
    )
    file = models.ImageField(
        upload_to=node_image_upload_path,
        verbose_name='图片文件',
        help_text='支持 jpg, jpeg, png, gif, webp 格式'
    )
    original_name = models.CharField(max_length=255, verbose_name='原始文件名')
    file_size = models.PositiveIntegerField(verbose_name='文件大小(字节)')
    width = models.PositiveIntegerField(verbose_name='图片宽度')
    height = models.PositiveIntegerField(verbose_name='图片高度')
    title = models.CharField(max_length=255, blank=True, verbose_name='图片标题')
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_node_images',
        verbose_name='上传者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    
    class Meta:
        verbose_name = '节点图片'
        verbose_name_plural = '节点图片'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.node.text[:20]} - {self.original_name}'
    
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
    
    def get_dimensions_display(self):
        """获取图片尺寸显示"""
        return f'{self.width} × {self.height}'
    
    @property
    def image_url(self):
        """获取图片URL"""
        if self.file:
            return self.file.url
        return ''
    
    def delete(self, *args, **kwargs):
        """删除图片时同时删除文件"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

class NodeTag(models.Model):
    """节点标签模型"""
    node = models.ForeignKey(
        MindMapNode,
        on_delete=models.CASCADE,
        related_name='tags',
        verbose_name='所属节点'
    )
    text = models.CharField(max_length=100, verbose_name='标签文本')
    style_data = models.JSONField(default=dict, blank=True, verbose_name='标签样式')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '节点标签'
        verbose_name_plural = '节点标签'
        ordering = ['sort_order', 'created_at']
    
    def __str__(self):
        return f'{self.node.text[:20]} - {self.text}'

class NodeGeneralization(models.Model):
    """节点概要模型"""
    node = models.ForeignKey(
        MindMapNode,
        on_delete=models.CASCADE,
        related_name='generalizations',
        verbose_name='所属节点'
    )
    text = models.TextField(verbose_name='概要文本')
    rich_text = models.BooleanField(default=False, verbose_name='是否富文本')
    style_data = models.JSONField(default=dict, blank=True, verbose_name='概要样式')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '节点概要'
        verbose_name_plural = '节点概要'
        ordering = ['sort_order', 'created_at']
    
    def __str__(self):
        return f'{self.node.text[:20]} - {self.text[:20]}'
