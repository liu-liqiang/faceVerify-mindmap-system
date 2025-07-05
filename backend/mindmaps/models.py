from django.db import models
from django.conf import settings
from django.utils import timezone
from projects.models import Project
import json
import os
import uuid
import time

def generate_node_id():
    """生成唯一的节点ID"""
    timestamp = int(timezone.now().timestamp() * 1000)
    random_str = uuid.uuid4().hex[:8]
    return f'node_{timestamp}_{random_str}'

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
    """节点文件上传路径（附件的别名）"""
    return node_attachment_upload_path(instance, filename)

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
        verbose_name='节点UID',
        help_text='前端生成'
    )
    parent_node_uid = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='父节点UID',
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
    
    # 超链接
    hyperlink = models.URLField(blank=True, verbose_name='超链接地址')
    hyperlink_title = models.CharField(max_length=255, blank=True, verbose_name='超链接标题')
    
    # 备注
    note = models.TextField(blank=True, verbose_name='备注')
    
    # 标签
    tags = models.JSONField(default=list, blank=True, verbose_name='标签列表')

    # 概要
    generalizations = models.JSONField(default=list, blank=True, verbose_name='概要数据')
    
    # 关联线，存储目标节点ID列表
    associative_line_targets = models.JSONField(default=list, blank=True, verbose_name='关联线目标节点')
    associative_line_text = models.JSONField(default=dict, blank=True, verbose_name='关联线文本数据')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 附加字段（为了兼容和扩展）
    level = models.PositiveIntegerField(default=0, verbose_name='节点层级')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='排序顺序')
    
    class Meta:
        verbose_name = '思维导图节点'
        verbose_name_plural = '思维导图节点'
        unique_together = ('project', 'node_id')
        ordering = ['level', 'sort_order', 'created_at']
        indexes = [
            models.Index(fields=['project', 'parent_node_uid']),
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
    
    @property
    def image(self):
        """获取节点的图片"""
        try:
            return self.node_image
        except NodeImage.DoesNotExist:
            return None
    
    @property
    def attachment(self):
        """获取节点的附件"""
        try:
            return self.node_attachment
        except NodeAttachment.DoesNotExist:
            return None
    
    @property
    def has_image(self):
        """检查节点是否有图片"""
        return hasattr(self, 'node_image') and self.node_image is not None
    
    @property
    def has_attachment(self):
        """检查节点是否有附件"""
        return hasattr(self, 'node_attachment') and self.node_attachment is not None
    
    def set_image(self, image_file, title='', uploader=None):
        """设置节点图片"""
        if not uploader:
            uploader = self.creator
        
        # 删除旧图片
        if self.has_image:
            self.node_image.delete()
        
        # 创建新图片
        try:
            from PIL import Image
            img = Image.open(image_file)
            width, height = img.size
        except ImportError:
            # 如果PIL不可用，使用默认尺寸
            width, height = 100, 100
        except Exception:
            # 如果图片无法打开，使用默认尺寸
            width, height = 100, 100
        
        NodeImage.objects.create(
            node=self,
            file=image_file,
            original_name=getattr(image_file, 'name', 'image.jpg'),
            file_size=getattr(image_file, 'size', 0),
            width=width,
            height=height,
            title=title or getattr(image_file, 'name', 'image.jpg'),
            uploader=uploader
        )
    
    def set_attachment(self, attachment_file, uploader=None):
        """设置节点附件"""
        if not uploader:
            uploader = self.creator
        
        # 删除旧附件
        if self.has_attachment:
            self.node_attachment.delete()
        
        # 创建新附件
        NodeAttachment.objects.create(
            node=self,
            file=attachment_file,
            original_name=getattr(attachment_file, 'name', 'attachment'),
            file_size=getattr(attachment_file, 'size', 0),
            uploader=uploader
        )
    
    def remove_image(self):
        """移除节点图片"""
        if self.has_image:
            self.node_image.delete()
    
    def remove_attachment(self):
        """移除节点附件"""
        if self.has_attachment:
            self.node_attachment.delete()
    
    def get_children(self):
        """获取子节点"""
        return MindMapNode.objects.filter(
            project=self.project,
            parent_node_uid=self.node_id
        ).order_by('created_at')
    
    def save(self, *args, **kwargs):
        """保存时的验证逻辑"""
        # 如果节点ID为空，则自动生成
        if not self.node_id:
            self.node_id = generate_node_id()
        
        # 自动计算层级
        if self.parent_node_uid:
            try:
                parent = MindMapNode.objects.get(
                    project=self.project, 
                    node_id=self.parent_node_uid
                )
                self.level = parent.level + 1
            except MindMapNode.DoesNotExist:
                self.level = 0
        else:
            self.level = 0
        
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
        if self.get_children().exists():
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
        )
        
        # 默认的子节点结构
        default_children = [
            {'text': '案件特点'},
            {'text': '资金流'},
            {'text': '信息流'},
            {'text': '网络流'},
        ]
        
        # 创建默认子节点
        for i, child_data in enumerate(default_children):
            cls.objects.create(
                project=project,
                node_id=f"default_{project.id}_{i+1}",
                parent_node_uid=root_node.node_id,
                creator=creator,
                text=child_data['text'],
                is_system_default=True,
            )
        
        return root_node
    
    @classmethod
    def get_root_node(cls, project):
        """获取指定项目的根节点"""
        return cls.objects.filter(project=project, is_root=True).first()
    
    def to_simple_mind_map_format(self, user=None):
        """转换为 Simple Mind Map 格式"""
        data = {
            'data': {
                'text': self.text.strip(),
                'richText': self.rich_text,
                'expand': self.expand,
                'uid': self.node_id,
                'icon': self.icon if self.icon else [],
                'image': self.image.image_url if self.image else '', 
                'imageTitle': self.image.title if self.image else '',
                'imageSize': {
                    'width': self.image.width if self.image else 100,
                    'height': self.image.height if self.image else 100,
                    'custom': False
                },
                'hyperlink': self.hyperlink or '',
                'hyperlinkTitle': self.hyperlink_title or '',
                'note': self.note or '',
                'attachmentUrl': self.attachment.attachment_url if self.attachment else '',
                'attachmentName': self.attachment.original_name if self.attachment else '',
                'tag': self.tags if self.tags else [],
                'generalization': self.generalizations if self.generalizations else [],
                'associativeLineTargets': self.associative_line_targets if self.associative_line_targets else [],
                'associativeLineText': self.associative_line_text or {},
                
                # 自定义字段
                '_creator': str(self.creator.police_number) if hasattr(self.creator, 'police_number') else str(self.creator.username),
                '_createdAt': self.created_at.isoformat(),
                '_updatedAt': self.updated_at.isoformat(),
                '_isRoot': self.is_root,
                '_isSystemDefault': self.is_system_default,
                '_editable': self.can_be_edited_by(user) if user else False,
                '_deletable': self.can_be_deleted_by(user) if user else False,
                '_canAddChildren': self.can_add_children(user) if user else False,
                '_hasImage': self.has_image,
                '_hasAttachment': self.has_attachment,
            },
            'children': []
        }
        
        # 递归添加子节点
        for child in self.get_children():
            data['children'].append(child.to_simple_mind_map_format(user))
        
        return data
    
    @classmethod
    def from_simple_mind_map_data(cls, nodes_data, user):
        """从 Simple Mind Map 数据批量创建节点
        
        Args:
            nodes_data (list): 前端传入的数据格式：
                [
                    {
                        projectId: 1,
                        data: {
                            text: '节点文本',
                            richText: false,
                            expand: true,
                            uid: 'node_123', 
                            icon: ['star', 'heart'],
                            hyperlink: 'https://example.com',
                            hyperlinkTitle: '链接标题',
                            note: '备注信息',
                            tag: ['标签1', '标签2'],
                            generalization: [{'text': '概要1', 'richText': false}],
                            associativeLineTargets: ['target_node_1', 'target_node_2'],
                            associativeLineText: {'target_node_1': '关联文本1', 'target_node_2': '关联文本2'},
                            ... # 其他字段
                        },
                        parent_uid: 'parent_node_uid', # 父节点UID
                        image: File, # 图片文件对象
                        attachment: File, # 附件文件对象
                    },
                    ...
                ]
            user: 创建节点的用户
        
        Returns:
            list: 创建成功的节点列表
        """
        if not isinstance(nodes_data, list):
            nodes_data = [nodes_data]
        
        created_nodes = []
        nodes_map = {}  # 用于存储已创建的节点，key为node_id
        
        try:
            # 第一步：按层级排序，确保父节点先创建
            sorted_nodes_data = cls._sort_nodes_by_hierarchy(nodes_data)
            
            # 第二步：批量创建节点
            for node_item in sorted_nodes_data:
                try:
                    # 获取项目
                    project_id = node_item.get('projectId')
                    if not project_id:
                        print(f"节点缺少 projectId: {node_item.get('data', {}).get('uid', 'unknown')}")
                        continue
                    
                    try:
                        project = Project.objects.get(id=project_id)
                    except Project.DoesNotExist:
                        print(f"项目不存在: {project_id}")
                        continue
                    
                    # 获取节点数据
                    node_data = node_item.get('data', {})
                    parent_uid = node_item.get('parent_uid')
                    image_file = node_item.get('image')
                    attachment_file = node_item.get('attachment')
                    
                    # 确定父节点
                    parent_node_uid = ''
                    if parent_uid:
                        # 先从已创建的节点中查找
                        if parent_uid in nodes_map:
                            parent_node_uid = parent_uid
                        else:
                            # 从数据库中查找
                            try:
                                parent_node = cls.objects.get(project=project, node_id=parent_uid)
                                parent_node_uid = parent_node.node_id
                            except cls.DoesNotExist:
                                print(f"父节点不存在: {parent_uid}")
                                continue
                    
                    # 生成节点ID
                    node_id = node_data.get('uid')
                    if not node_id:
                        node_id = generate_node_id()
                    
                    # 检查节点ID是否已存在
                    if cls.objects.filter(project=project, node_id=node_id).exists():
                        print(f"节点ID已存在: {node_id}")
                        continue
                    
                    # 创建节点
                    node = cls.objects.create(
                        project=project,
                        node_id=node_id,
                        parent_node_uid=parent_node_uid,
                        creator=user,
                        text=node_data.get('text', '新节点'),
                        rich_text=node_data.get('richText', False),
                        expand=node_data.get('expand', True),
                        icon=node_data.get('icon', []),
                        hyperlink=node_data.get('hyperlink', ''),
                        hyperlink_title=node_data.get('hyperlinkTitle', ''),
                        note=node_data.get('note', ''),
                        tags=node_data.get('tag', []),
                        generalizations=node_data.get('generalization', []),
                        associative_line_targets=node_data.get('associativeLineTargets', []),
                        associative_line_text=node_data.get('associativeLineText', {}),
                        is_root=not parent_node_uid,
                        is_system_default=node_data.get('isSystemDefault', False),
                    )
                    
                    # 处理图片
                    if image_file:
                        cls._handle_node_image(node, image_file, user)
                    
                    # 处理附件
                    if attachment_file:
                        cls._handle_node_attachment(node, attachment_file, user)
                    
                    # 记录创建的节点
                    nodes_map[node_id] = node
                    created_nodes.append(node)
                    
                except Exception as e:
                    print(f"创建节点失败: {e}")
                    continue
            
            return created_nodes
            
        except Exception as e:
            print(f"批量创建节点失败: {e}")
            return []
    
    @classmethod
    def _sort_nodes_by_hierarchy(cls, nodes_data):
        """按层级排序节点数据，确保父节点先创建"""
        # 构建节点依赖关系
        nodes_dict = {}
        for node_item in nodes_data:
            node_id = node_item.get('data', {}).get('uid')
            if node_id:
                nodes_dict[node_id] = node_item
        
        sorted_nodes = []
        processed = set()
        
        def process_node(node_item):
            node_id = node_item.get('data', {}).get('uid')
            if not node_id or node_id in processed:
                return
            
            parent_uid = node_item.get('parent_uid')
            if parent_uid and parent_uid in nodes_dict and parent_uid not in processed:
                # 先处理父节点
                process_node(nodes_dict[parent_uid])
            
            sorted_nodes.append(node_item)
            processed.add(node_id)
        
        # 处理所有节点
        for node_item in nodes_data:
            process_node(node_item)
        
        return sorted_nodes
    
    @classmethod
    def _handle_node_image(cls, node, image_file, user):
        """处理节点图片"""
        try:
            if not image_file:
                return None
            
            # 检查文件类型
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image_file, 'content_type') and image_file.content_type not in allowed_types:
                print(f"不支持的图片格式: {image_file.content_type}")
                return None
            
            # 检查文件大小（限制为10MB）
            max_size = 10 * 1024 * 1024  # 10MB
            if hasattr(image_file, 'size') and image_file.size > max_size:
                print(f"图片文件过大: {image_file.size} bytes")
                return None
            
            # 创建图片记录
            try:
                from PIL import Image
                # 获取图片尺寸
                img = Image.open(image_file)
                width, height = img.size
            except ImportError:
                # 如果PIL不可用，使用默认尺寸
                width, height = 100, 100
            except Exception:
                width, height = 100, 100
            
            # 创建 NodeImage 对象
            node_image = NodeImage.objects.create(
                node=node,
                file=image_file,
                original_name=getattr(image_file, 'name', 'image.jpg'),
                file_size=getattr(image_file, 'size', 0),
                width=width,
                height=height,
                title=getattr(image_file, 'name', 'image.jpg'),
                uploader=user
            )
            
            return node_image
            
        except Exception as e:
            print(f"处理图片失败: {e}")
            return None
    
    @classmethod
    def _handle_node_attachment(cls, node, attachment_file, user):
        """处理节点附件"""
        try:
            if not attachment_file:
                return None
            
            # 检查文件大小（限制为50MB）
            max_size = 50 * 1024 * 1024  # 50MB
            if hasattr(attachment_file, 'size') and attachment_file.size > max_size:
                print(f"附件文件过大: {attachment_file.size} bytes")
                return None
            
            # 创建附件记录
            node_attachment = NodeAttachment.objects.create(
                node=node,
                file=attachment_file,
                original_name=getattr(attachment_file, 'name', 'attachment'),
                file_size=getattr(attachment_file, 'size', 0),
                uploader=user
            )
            
            return node_attachment
            
        except Exception as e:
            print(f"处理附件失败: {e}")
            return None
    
    @classmethod
    def update_from_simple_mind_map_data(cls, nodes_data, user):
        """批量更新节点数据"""
        if not isinstance(nodes_data, list):
            nodes_data = [nodes_data]
        
        updated_nodes = []
        
        for node_item in nodes_data:
            try:
                # 获取项目和节点
                project_id = node_item.get('projectId')
                node_data = node_item.get('data', {})
                node_id = node_data.get('uid')
                
                if not project_id or not node_id:
                    continue
                
                try:
                    project = Project.objects.get(id=project_id)
                    node = cls.objects.get(project=project, node_id=node_id)
                except (Project.DoesNotExist, cls.DoesNotExist):
                    continue
                
                # 检查权限
                if not node.can_be_edited_by(user):
                    continue
                
                # 更新节点数据
                node.text = node_data.get('text', node.text)
                node.rich_text = node_data.get('richText', node.rich_text)
                node.expand = node_data.get('expand', node.expand)
                node.icon = node_data.get('icon', node.icon)
                node.hyperlink = node_data.get('hyperlink', node.hyperlink)
                node.hyperlink_title = node_data.get('hyperlinkTitle', node.hyperlink_title)
                node.note = node_data.get('note', node.note)
                node.tags = node_data.get('tag', node.tags)
                node.generalizations = node_data.get('generalization', node.generalizations)
                node.associative_line_targets = node_data.get('associativeLineTargets', node.associative_line_targets)
                node.associative_line_text = node_data.get('associativeLineText', node.associative_line_text)
                
                node.save()
                
                # 处理新的图片（如果有）
                image_file = node_item.get('image')
                if image_file:
                    # 删除旧图片
                    if node.has_image:
                        node.node_image.delete()
                    # 创建新图片
                    cls._handle_node_image(node, image_file, user)
                
                # 处理新的附件（如果有）
                attachment_file = node_item.get('attachment')
                if attachment_file:
                    # 删除旧附件
                    if node.has_attachment:
                        node.node_attachment.delete()
                    # 创建新附件
                    cls._handle_node_attachment(node, attachment_file, user)
                
                updated_nodes.append(node)
                
            except Exception as e:
                print(f"更新节点失败: {e}")
                continue
        
        return updated_nodes
    
    @classmethod
    def delete_nodes_by_ids(cls, project_id, node_ids, user):
        """批量删除节点"""
        if not isinstance(node_ids, list):
            node_ids = [node_ids]
        
        deleted_count = 0
        
        try:
            project = Project.objects.get(id=project_id)
            
            for node_id in node_ids:
                try:
                    node = cls.objects.get(project=project, node_id=node_id)
                    
                    if node.can_be_deleted_by(user):
                        # 删除关联的图片和附件文件
                        if node.has_image:
                            node.node_image.delete()
                        if node.has_attachment:
                            node.node_attachment.delete()
                        
                        # 删除节点
                        node.delete()
                        deleted_count += 1
                    
                except cls.DoesNotExist:
                    continue
        
        except Project.DoesNotExist:
            pass
        
        return deleted_count
    
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
            try:
                target_node = MindMapNode.objects.get(
                    project=self.project, 
                    node_id=target_node_id
                )
                from django.apps import apps
                AssociativeLineModel = apps.get_model('mindmaps', 'AssociativeLine')
                AssociativeLineModel.objects.get_or_create(
                    project=self.project,
                    source_node=self,
                    target_node=target_node,
                    defaults={
                        'text': self.associative_line_text.get(target_node_id, '') if isinstance(self.associative_line_text, dict) else '',
                        'creator': self.creator
                    }
                )
            except MindMapNode.DoesNotExist:
                pass
    
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
                # 延迟导入避免循环引用
                AssociativeLine = self.__class__.__module__.split('.')[0] + '.models.AssociativeLine'
                from django.apps import apps
                AssociativeLineModel = apps.get_model('mindmaps', 'AssociativeLine')
                AssociativeLineModel.objects.filter(
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
        # 使用延迟导入避免循环引用
        from django.apps import apps
        try:
            AssociativeLineModel = apps.get_model('mindmaps', 'AssociativeLine')
            # 删除当前节点的所有关联线记录
            AssociativeLineModel.objects.filter(source_node=self).delete()
            
            # 重新创建关联线记录
            if self.associative_line_targets:
                targets_to_remove = []
                for target_node_id in self.associative_line_targets:
                    try:
                        target_node = MindMapNode.objects.get(
                            project=self.project,
                            node_id=target_node_id
                        )
                        text = ''
                        if isinstance(self.associative_line_text, dict):
                            text = self.associative_line_text.get(target_node_id, '')
                        
                        AssociativeLineModel.objects.create(
                            project=self.project,
                            source_node=self,
                            target_node=target_node,
                            text=text,
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
        except Exception as e:
            # 如果AssociativeLine模型不存在，忽略错误
            print(f"AssociativeLine模型不存在或发生错误: {e}")
    
    def update_associative_lines(self, target_node_ids, line_text_dict=None):
        """批量更新关联线目标节点"""
        # 确保传入的是列表
        if not isinstance(target_node_ids, list):
            target_node_ids = [target_node_ids] if target_node_ids else []
        
        # 更新 associative_line_targets 字段
        self.associative_line_targets = target_node_ids
        if line_text_dict:
            self.associative_line_text = line_text_dict
        self.save()
        
        # 同步到 AssociativeLine 表
        self.sync_associative_lines()
    
    def clear_associative_lines(self):
        """清除所有关联线"""
        self.associative_line_targets = []
        self.associative_line_text = {}
        self.save()
        
        # 删除 AssociativeLine 表中的记录
        from django.apps import apps
        try:
            AssociativeLineModel = apps.get_model('mindmaps', 'AssociativeLine')
            AssociativeLineModel.objects.filter(source_node=self).delete()
        except Exception as e:
            # 如果AssociativeLine模型不存在，忽略错误
            print(f"AssociativeLine模型不存在或发生错误: {e}")
    
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
        

class NodeImage(models.Model):
    """思维导图节点图片模型（一对一关系）"""
    node = models.OneToOneField(
        MindMapNode, 
        on_delete=models.CASCADE, 
        related_name='node_image',
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


class NodeAttachment(models.Model):
    """思维导图节点附件模型（一对一关系）"""
    node = models.OneToOneField(
        MindMapNode, 
        on_delete=models.CASCADE, 
        related_name='node_attachment',
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
        indexes = [
            models.Index(fields=['node', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        user_name = getattr(self.user, 'real_name', None) or self.user.username
        return f'{user_name} {self.get_action_display()} {self.node.text[:20]}'


class AssociativeLine(models.Model):
    """关联线模型 - 用于存储节点间的关联关系"""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='associative_lines',
        verbose_name='所属项目'
    )
    source_node = models.ForeignKey(
        MindMapNode,
        on_delete=models.CASCADE,
        related_name='outgoing_lines',
        verbose_name='源节点'
    )
    target_node = models.ForeignKey(
        MindMapNode,
        on_delete=models.CASCADE,
        related_name='incoming_lines',
        verbose_name='目标节点'
    )
    text = models.CharField(max_length=255, blank=True, verbose_name='关联线文本')
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '节点关联线'
        verbose_name_plural = '节点关联线'
        unique_together = ('source_node', 'target_node')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'source_node']),
            models.Index(fields=['project', 'target_node']),
            models.Index(fields=['creator', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.source_node.text[:20]} -> {self.target_node.text[:20]}'


class NodeTag(models.Model):
    """节点标签模型"""
    node = models.ForeignKey(
        MindMapNode,
        on_delete=models.CASCADE,
        related_name='tag_objects',
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
        indexes = [
            models.Index(fields=['node', 'sort_order']),
        ]
    
    def __str__(self):
        return f'{self.node.text[:20]} - {self.text}'


class NodeGeneralization(models.Model):
    """节点概要模型"""
    node = models.ForeignKey(
        MindMapNode,
        on_delete=models.CASCADE,
        related_name='generalization_objects',
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
        indexes = [
            models.Index(fields=['node', 'sort_order']),
        ]
    
    def __str__(self):
        return f'{self.node.text[:20]} - {self.text[:20]}'


