from django.contrib.auth.models import AbstractUser
from django.db import models
import json

class CustomUser(AbstractUser):
    # 基本信息
    real_name = models.CharField(max_length=50, verbose_name="姓名", help_text="真实姓名", default="", blank=True)
    police_number = models.CharField(max_length=20, unique=True, verbose_name="警号", help_text="警员编号", db_index=True, null=True, blank=True)
    phone_number = models.CharField(max_length=11, verbose_name="手机号码", help_text="联系手机号", default="", blank=True)
    
    # 单位选择
    DEPARTMENT_CHOICES = [
        ('direct', '市局直属部门'),
        ('tianyuan', '天元分局'),
        ('lusong', '芦淞分局'),
        ('hetang', '荷塘分局'),
        ('shifeng', '石峰分局'),
        ('dongjiabai', '董家塅分局'),
        ('kaifaqu', '经开区分局'),
        ('lukou', '渌口分局'),
        ('liling', '醴陵市公安局'),
        ('youxian', '攸县公安局'),
        ('chaling', '茶陵县公安局'),
        ('yanling', '炎陵县公安局'),
    ]
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, verbose_name="所属单位", default='direct')
    
    # 审核状态
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已审核'),
        ('rejected', '已拒绝'),
        ('suspended', '已停用'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="审核状态")
    rejection_reason = models.TextField(blank=True, verbose_name="拒绝原因", help_text="审核拒绝时的原因说明")
    approved_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="审核人")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")
    
    # 人脸识别相关
    face_encodings = models.TextField(blank=True, help_text="存储人脸特征编码数据，JSON格式，支持多个128维特征向量")
    is_face_registered = models.BooleanField(default=False, help_text="是否已注册人脸")
    
    def set_face_encodings(self, encodings_list):
        """
        设置人脸编码数据
        encodings_list: list of face descriptors from face-api.js
        每个descriptor是128维的浮点数数组
        """
        if encodings_list and len(encodings_list) > 0:
            # 确保所有编码都是有效的128维向量
            valid_encodings = []
            for encoding in encodings_list:
                if isinstance(encoding, (list, tuple)) and len(encoding) == 128:
                    # 转换为Python list并确保是浮点数
                    valid_encoding = [float(x) for x in encoding]
                    valid_encodings.append(valid_encoding)
            
            if valid_encodings:
                self.face_encodings = json.dumps(valid_encodings)
                self.is_face_registered = True
            else:
                self.face_encodings = ''
                self.is_face_registered = False
        else:
            self.face_encodings = ''
            self.is_face_registered = False
        
    def get_face_encodings(self):
        """
        获取人脸编码数据
        返回: list of 128-dimensional face descriptors
        """
        if self.face_encodings:
            try:
                encodings = json.loads(self.face_encodings)
                # 验证数据格式
                if isinstance(encodings, list):
                    return encodings
            except json.JSONDecodeError:
                pass
        return []
    
    def get_primary_face_encoding(self):
        """
        获取主要的人脸编码（第一个）
        返回: 128-dimensional face descriptor or None
        """
        encodings = self.get_face_encodings()
        return encodings[0] if encodings else None
    
    def add_face_encoding(self, new_encoding):
        """
        添加新的人脸编码
        new_encoding: 128-dimensional face descriptor from face-api.js
        """
        if isinstance(new_encoding, (list, tuple)) and len(new_encoding) == 128:
            current_encodings = self.get_face_encodings()
            current_encodings.append([float(x) for x in new_encoding])
            self.set_face_encodings(current_encodings)
            return True
        return False
    
    @property
    def face_registered(self):
        """获取人脸注册状态（别名）"""
        return self.is_face_registered
    
    def get_department_display_name(self):
        """获取部门显示名称"""
        return dict(self.DEPARTMENT_CHOICES).get(self.department, self.department)
    
    def get_status_display_name(self):
        """获取状态显示名称"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def is_approved(self):
        """检查用户是否已审核通过"""
        return self.status == 'approved'
    
    def __str__(self):
        if self.real_name and self.police_number:
            return f"{self.real_name}({self.police_number})"
        elif self.real_name:
            return f"{self.real_name}({self.username})"
        else:
            return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}的个人资料"

class LoginAttempt(models.Model):
    """登录尝试记录模型"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_attempts', null=True, blank=True)
    police_number = models.CharField(max_length=20, verbose_name="警号")
    
    ATTEMPT_TYPE_CHOICES = [
        ('password', '密码登录'),
        ('face', '人脸识别'),
        ('combined', '密码+人脸'),
    ]
    attempt_type = models.CharField(max_length=20, choices=ATTEMPT_TYPE_CHOICES, verbose_name="登录方式")
    
    RESULT_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
    ]
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, verbose_name="登录结果")
    
    ip_address = models.GenericIPAddressField(verbose_name="IP地址")
    user_agent = models.TextField(blank=True, verbose_name="用户代理")
    failure_reason = models.CharField(max_length=200, blank=True, verbose_name="失败原因")
    face_confidence = models.FloatField(null=True, blank=True, verbose_name="人脸识别置信度")
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name="尝试时间")
    
    class Meta:
        ordering = ['-attempted_at']
        verbose_name = "登录尝试"
        verbose_name_plural = "登录尝试记录"
    
    def __str__(self):
        return f"{self.police_number} - {self.get_attempt_type_display()} - {self.get_result_display()}"
