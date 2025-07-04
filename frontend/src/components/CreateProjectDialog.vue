<template>
  <el-dialog v-model="dialogVisible" title="创建新案件" width="600px" @close="handleClose">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="案件名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入案件名称" clearable />
      </el-form-item>

      <el-form-item label="案件编号" prop="case_number">
        <el-input v-model="form.case_number" placeholder="请输入案件编号" clearable />
      </el-form-item>

      <el-form-item label="立案单位" prop="filing_unit">
        <el-select v-model="form.filing_unit" placeholder="请选择立案单位" style="width: 100%">
          <el-option v-for="unit in filingUnits" :key="unit.value" :label="unit.label" :value="unit.value" />
        </el-select>
      </el-form-item>

      <el-form-item label="简要案情" prop="case_summary">
        <el-input v-model="form.case_summary" type="textarea" :rows="4" placeholder="请输入案件的简要情况" />
      </el-form-item>

      <el-form-item label="案件附件">
        <el-upload ref="uploadRef" :file-list="fileList" :auto-upload="false" :on-change="handleFileChange"
          :on-remove="handleFileRemove" multiple drag>
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 jpg/png/pdf/doc/docx 等格式，单个文件不超过 10MB
            </div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          创建案件
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useProjectStore } from '@/stores/project'
import { ElMessage, type FormInstance, type FormRules, type UploadFile, type UploadFiles } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'created'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const projectStore = useProjectStore()
const formRef = ref<FormInstance>()
const uploadRef = ref()
const loading = ref(false)

const dialogVisible = ref(false)
const fileList = ref<UploadFiles>([])

// 立案单位选项
const filingUnits = [
  { value: 'direct', label: '直属单位' },
  { value: 'tianyuan', label: '天元分局' },
  { value: 'lusong', label: '芦淞分局' },
  { value: 'hetang', label: '荷塘分局' },
  { value: 'shifeng', label: '石峰分局' },
  { value: 'dongjiaba', label: '董家塅分局' },
  { value: 'economic', label: '经开区分局' },
  { value: 'lukou', label: '渌口分局' },
  { value: 'liling', label: '醴陵市公安局' },
  { value: 'youxian', label: '攸县公安局' },
  { value: 'chaling', label: '茶陵县公安局' },
  { value: 'yanling', label: '炎陵县公安局' }
]

const form = reactive({
  name: '',
  case_number: '',
  filing_unit: '',
  case_summary: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入案件名称', trigger: 'blur' },
    { min: 2, max: 200, message: '案件名称长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  case_number: [
    { required: true, message: '请输入案件编号', trigger: 'blur' },
    { min: 5, max: 50, message: '案件编号长度在 5 到 50 个字符', trigger: 'blur' }
  ],
  filing_unit: [
    { required: true, message: '请选择立案单位', trigger: 'change' }
  ],
  case_summary: [
    { required: true, message: '请输入简要案情', trigger: 'blur' },
    { min: 10, message: '简要案情至少需要 10 个字符', trigger: 'blur' }
  ]
}

watch(() => props.modelValue, (val) => {
  dialogVisible.value = val
})

watch(dialogVisible, (val) => {
  emit('update:modelValue', val)
})

const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  // 文件大小限制 10MB
  const maxSize = 10 * 1024 * 1024
  if (file.size && file.size > maxSize) {
    ElMessage.error('文件大小不能超过 10MB')
    files.splice(files.indexOf(file), 1)
    return false
  }

  // 文件类型限制
  const allowedTypes = [
    'image/jpeg', 'image/png', 'image/gif',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ]

  if (file.raw && !allowedTypes.includes(file.raw.type)) {
    ElMessage.error('不支持的文件类型')
    files.splice(files.indexOf(file), 1)
    return false
  }

  fileList.value = files
}

const handleFileRemove = (file: UploadFile, files: UploadFiles) => {
  fileList.value = files
}

const handleClose = () => {
  dialogVisible.value = false
  resetForm()
}

const resetForm = () => {
  form.name = ''
  form.case_number = ''
  form.filing_unit = ''
  form.case_summary = ''
  fileList.value = []
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    // 创建FormData以支持文件上传
    const formData = new FormData()
    formData.append('name', form.name)
    formData.append('case_number', form.case_number)
    formData.append('filing_unit', form.filing_unit)
    formData.append('case_summary', form.case_summary)

    // 添加附件文件
    fileList.value.forEach((file) => {
      if (file.raw) {
        formData.append('attachments', file.raw)
      }
    })

    await projectStore.createProject(formData)

    ElMessage.success('案件创建成功')
    emit('created')
    handleClose()
  } catch (error: any) {
    console.error('Create project error:', error)

    if (error.response?.data?.case_number) {
      ElMessage.error('案件编号已存在')
    } else if (error.response?.data?.name) {
      ElMessage.error('案件名称已存在')
    } else {
      ElMessage.error(error.response?.data?.message || '创建案件失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  gap: 12px;
}
</style>
