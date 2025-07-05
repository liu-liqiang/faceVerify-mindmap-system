#!/usr/bin/env python
import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collaboration_system.settings')
django.setup()

from mindmaps.models import MindMapNode, NodeImage, NodeAttachment, AssociativeLine
from projects.models import Project
from users.models import CustomUser
from django.db import connection

def test_database():
    print("=== 数据库测试 ===")
    
    # 检查表是否创建成功
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\n数据库中的表:")
        for table in tables:
            print(f"  - {table[0]}")
    
    print("\n=== 模型测试 ===")
    print(f"MindMapNode 表名: {MindMapNode._meta.db_table}")
    print(f"NodeImage 表名: {NodeImage._meta.db_table}")
    print(f"NodeAttachment 表名: {NodeAttachment._meta.db_table}")
    print(f"AssociativeLine 表名: {AssociativeLine._meta.db_table}")
    print(f"Project 表名: {Project._meta.db_table}")
    print(f"CustomUser 表名: {CustomUser._meta.db_table}")
    
    # 测试模型计数
    print("\n=== 数据计数 ===")
    print(f"MindMapNode 数量: {MindMapNode.objects.count()}")
    print(f"NodeImage 数量: {NodeImage.objects.count()}")
    print(f"NodeAttachment 数量: {NodeAttachment.objects.count()}")
    print(f"Project 数量: {Project.objects.count()}")
    print(f"CustomUser 数量: {CustomUser.objects.count()}")
    
    print("\n=== 测试完成 ===")
    print("数据库迁移成功！所有模型都可以正常使用。")

if __name__ == "__main__":
    test_database()
