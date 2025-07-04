from django.core.management.base import BaseCommand
from projects.models import Project
from mindmaps.models import MindMapNode


class Command(BaseCommand):
    help = '为现有项目创建默认思维导图'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='为指定项目ID创建思维导图'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制为已有思维导图的项目重新创建默认思维导图'
        )

    def handle(self, *args, **options):
        project_id = options.get('project_id')
        force = options.get('force', False)

        if project_id:
            # 为指定项目创建思维导图
            try:
                project = Project.objects.get(id=project_id)
                self.create_mindmap_for_project(project, force)
            except Project.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'项目 ID {project_id} 不存在')
                )
        else:
            # 为所有没有思维导图的项目创建
            if force:
                projects = Project.objects.all()
                self.stdout.write(
                    self.style.WARNING('强制模式：将为所有项目重新创建思维导图')
                )
            else:
                projects = Project.objects.filter(nodes__isnull=True).distinct()
                self.stdout.write(
                    f'找到 {projects.count()} 个没有思维导图的项目'
                )

            created_count = 0
            for project in projects:
                if self.create_mindmap_for_project(project, force):
                    created_count += 1

            self.stdout.write(
                self.style.SUCCESS(f'成功创建了 {created_count} 个默认思维导图')
            )

    def create_mindmap_for_project(self, project, force=False):
        """为单个项目创建思维导图"""
        existing_nodes = MindMapNode.objects.filter(project=project)
        
        if existing_nodes.exists() and not force:
            self.stdout.write(
                self.style.WARNING(f'项目 "{project.name}" 已有思维导图，跳过')
            )
            return False

        if force and existing_nodes.exists():
            # 删除现有节点
            existing_nodes.delete()
            self.stdout.write(
                self.style.WARNING(f'已删除项目 "{project.name}" 的现有思维导图')
            )

        try:
            MindMapNode.create_default_mindmap(project)
            self.stdout.write(
                self.style.SUCCESS(f'成功为项目 "{project.name}" 创建默认思维导图')
            )
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'为项目 "{project.name}" 创建思维导图失败: {str(e)}')
            )
            return False
