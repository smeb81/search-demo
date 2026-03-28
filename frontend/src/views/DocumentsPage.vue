<template>
  <div class="documents-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="hero-bg"></div>
      <div class="header-content">
        <el-button class="back-btn" @click="$router.push('/')">
          <el-icon><ArrowLeft /></el-icon>
          返回搜索
        </el-button>
        <h1 class="page-title">
          <span class="title-icon">📚</span>
          文档库
        </h1>
        <div class="header-actions">
          <el-button class="action-btn" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加文档
          </el-button>
          <el-upload
            class="upload-btn"
            :action="uploadUrl"
            :before-upload="handleBeforeUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :show-file-list="false"
            accept=".txt,.md,.pdf,.docx"
          >
            <el-button class="action-btn">
              <el-icon><Upload /></el-icon>
              上传文档
            </el-button>
          </el-upload>
          <el-button class="action-btn" @click="showImportDialog = true">
            <el-icon><FolderOpened /></el-icon>
            批量导入
          </el-button>
          <el-button class="action-btn" @click="loadDocuments">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="documents-container">
      <el-empty v-if="totalDocs === 0" description="暂无文档，请添加或导入" />

      <div v-else class="doc-list">
        <div
          v-for="doc in paginatedDocs"
          :key="doc.id"
          class="doc-card"
        >
          <div class="doc-header">
            <div class="doc-id-badge">
              <span class="doc-id">ID</span>
              <span class="doc-id-num">{{ doc.id }}</span>
            </div>
            <div class="doc-title">{{ doc.title || '无标题' }}</div>
            <el-button type="danger" size="small" class="delete-btn" @click="handleDelete(doc.id)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
          <div class="doc-content">
            {{ getPreviewText(doc.text) }}
          </div>
          <div class="doc-meta">
            <span class="meta-item">
              <el-icon><Clock /></el-icon>
              {{ formatDate(doc.created_at) }}
            </span>
            <span class="meta-item" v-if="doc.source_file">
              <el-icon><Document /></el-icon>
              {{ doc.source_file }}
            </span>
            <span class="meta-item">
              <el-icon><Files /></el-icon>
              {{ doc.text?.length || 0 }} 字符
            </span>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-container" v-if="totalDocs > 0">
        <div class="pagination-info">
          第 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, totalDocs) }} 条，
          共 {{ totalDocs }} 条
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="totalDocs"
          layout="prev, pager, next"
          background
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 添加文档对话框 -->
    <el-dialog v-model="showAddDialog" title="添加文档" width="500px" class="custom-dialog">
      <el-form :model="newDoc" label-width="60px">
        <el-form-item label="标题">
          <el-input v-model="newDoc.title" placeholder="可选标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="newDoc.text"
            type="textarea"
            :rows="6"
            placeholder="输入文档内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitDocument">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="showImportDialog" title="批量导入文档" width="500px" class="custom-dialog">
      <el-form label-width="80px">
        <el-form-item label="文件夹">
          <el-input v-model="folderPath" placeholder="输入文件夹路径，如：D:/documents" />
        </el-form-item>
        <el-alert
          title="支持格式"
          type="info"
          :closable="false"
          description="支持 .txt、.md、.pdf、.docx 文件"
        />
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="submitImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, FolderOpened, Refresh, Delete, Clock, Document, Files, Upload } from '@element-plus/icons-vue'
import { getDocuments, deleteDocument, addDocument, importFolder } from '../api'

const documents = ref([])
const currentPage = ref(1)
const pageSize = 10
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const newDoc = ref({ title: '', text: '' })
const folderPath = ref('')
const uploadUrl = '/api/documents/upload'

const totalDocs = computed(() => documents.value.length)

const paginatedDocs = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return documents.value.slice(start, end)
})

const loadDocuments = async () => {
  try {
    const res = await getDocuments()
    documents.value = res.data
    currentPage.value = 1
  } catch (error) {
    ElMessage.error('加载文档列表失败')
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
}

const getPreviewText = (text) => {
  if (!text) return ''
  return text.length > 180 ? text.substring(0, 180) + '...' : text
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定要删除这篇文档吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteDocument(id)
      ElMessage.success('文档删除成功')
      await loadDocuments()
    } catch (error) {
      ElMessage.error('删除文档失败')
    }
  }).catch(() => {})
}

const submitDocument = () => {
  if (!newDoc.value.text.trim()) {
    return
  }
  addDocument(newDoc.value).then(() => {
    ElMessage.success('文档添加成功')
    newDoc.value = { title: '', text: '' }
    showAddDialog.value = false
    loadDocuments()
  }).catch(() => {
    ElMessage.error('添加文档失败')
  })
}

const submitImport = () => {
  if (!folderPath.value.trim()) {
    return
  }
  importFolder(folderPath.value).then((res) => {
    ElMessage.success(`成功导入 ${res.data.count} 个文档`)
    folderPath.value = ''
    showImportDialog.value = false
    loadDocuments()
  }).catch((error) => {
    ElMessage.error('导入失败: ' + (error.response?.data?.error || '未知错误'))
  })
}

const handleBeforeUpload = (file) => {
  const allowedTypes = ['.txt', '.md', '.pdf', '.docx']
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  if (!allowedTypes.includes(ext)) {
    ElMessage.error('不支持的文件格式，仅支持 .txt, .md, .pdf, .docx')
    return false
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

const handleUploadSuccess = (response) => {
  ElMessage.success('文件上传成功')
  loadDocuments()
}

const handleUploadError = (error) => {
  ElMessage.error('文件上传失败: ' + (error.response?.data?.error || '未知错误'))
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.documents-page {
  min-height: 100vh;
  /* Midnight Galaxy 主题 */
  --deep-purple: #2b1e3e;
  --cosmic-blue: #4a4e8f;
  --lavender: #a490c2;
  --silver: #e6e6fa;
  --glow-purple: #8b5cf6;
  --dark-bg: #1a1429;
  background: var(--dark-bg);
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: linear-gradient(135deg, var(--deep-purple) 0%, #1a1429 50%, var(--cosmic-blue) 100%);
  border-bottom: 1px solid rgba(164, 144, 194, 0.15);
}

.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 50%, rgba(74, 78, 143, 0.15) 0%, transparent 50%);
  pointer-events: none;
}

.header-content {
  position: relative;
  max-width: 1000px;
  margin: 0 auto;
  padding: 18px 24px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 16px;
  border-radius: 12px;
  font-weight: 500;
  background: rgba(164, 144, 194, 0.15) !important;
  border: 1px solid rgba(164, 144, 194, 0.3) !important;
  color: var(--silver) !important;
}

.back-btn:hover {
  background: rgba(164, 144, 194, 0.25) !important;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--silver);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  text-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
}

.title-icon {
  font-size: 28px;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 10px;
}

.header-actions .action-btn {
  padding: 10px 18px;
  border-radius: 12px;
  font-weight: 500;
  background: rgba(164, 144, 194, 0.15) !important;
  border: 1px solid rgba(164, 144, 194, 0.3) !important;
  color: var(--silver) !important;
}

.header-actions .action-btn:hover {
  background: rgba(164, 144, 194, 0.25) !important;
  border-color: var(--glow-purple) !important;
}

.upload-btn {
  display: inline-block;
}

.documents-container {
  position: relative;
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px 24px;
}

.doc-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.doc-card {
  background: linear-gradient(135deg, rgba(43, 30, 62, 0.8), rgba(26, 20, 41, 0.9));
  border: 1px solid rgba(164, 144, 194, 0.15);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  transition: all 0.25s ease;
  backdrop-filter: blur(10px);
}

.doc-card:hover {
  border-color: var(--glow-purple);
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.15);
  transform: translateY(-2px);
}

.doc-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.doc-id-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(135deg, var(--glow-purple), var(--cosmic-blue));
  color: white;
  padding: 8px 12px;
  border-radius: 12px;
  min-width: 48px;
}

.doc-id {
  font-size: 10px;
  opacity: 0.85;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.doc-id-num {
  font-size: 18px;
  font-weight: 700;
}

.doc-title {
  flex: 1;
  font-size: 17px;
  font-weight: 600;
  color: var(--silver);
}

.delete-btn {
  border-radius: 10px;
  padding: 8px 14px;
}

.doc-content {
  color: rgba(230, 230, 250, 0.8);
  line-height: 1.8;
  font-size: 14px;
  background: rgba(0, 0, 0, 0.2);
  padding: 18px 20px;
  border-radius: 14px;
  margin-bottom: 16px;
  white-space: pre-wrap;
  word-break: break-word;
  border-left: 4px solid var(--glow-purple);
}

.doc-meta {
  display: flex;
  gap: 24px;
  color: var(--lavender);
  font-size: 13px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pagination-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 36px;
  gap: 16px;
}

.pagination-info {
  color: var(--lavender);
  font-size: 14px;
}

:deep(.el-pagination) {
  --el-pagination-bg-color: rgba(43, 30, 62, 0.8);
  --el-pagination-hover-color: var(--glow-purple);
  --el-pagination-text-color: var(--silver);
  --el-pagination-button-bg-color: rgba(164, 144, 194, 0.15);
}

:deep(.el-pagination.is-background .el-pager li) {
  border-radius: 10px;
  margin: 0 4px;
  background: rgba(164, 144, 194, 0.15);
  color: var(--silver);
}

:deep(.el-pagination.is-background .el-pager li:hover) {
  color: var(--glow-purple);
}

:deep(.el-pagination.is-background .el-pager li.is-active) {
  background: linear-gradient(135deg, var(--glow-purple), var(--cosmic-blue));
  color: white;
}

:deep(.el-pagination.is-background .btn-prev),
:deep(.el-pagination.is-background .btn-next) {
  background: rgba(164, 144, 194, 0.15);
  color: var(--silver);
}

:deep(.el-empty__description p) {
  color: var(--lavender);
}

:deep(.custom-dialog) {
  border-radius: 16px;
}

:deep(.el-dialog) {
  background: var(--deep-purple) !important;
  border: 1px solid rgba(164, 144, 194, 0.2);
  border-radius: 16px;
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(164, 144, 194, 0.15);
  padding-bottom: 16px;
}

:deep(.el-dialog__title) {
  font-weight: 600;
  color: var(--silver);
}

:deep(.el-dialog__body) {
  color: var(--silver);
}

:deep(.el-input__wrapper) {
  background: rgba(26, 20, 41, 0.8) !important;
  border: 1px solid rgba(164, 144, 194, 0.3) !important;
  box-shadow: none !important;
}

:deep(.el-input__inner) {
  color: var(--silver) !important;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(164, 144, 194, 0.6) !important;
}

:deep(.el-textarea__inner) {
  background: rgba(26, 20, 41, 0.8) !important;
  border: 1px solid rgba(164, 144, 194, 0.3) !important;
  color: var(--silver) !important;
}

:deep(.el-textarea__inner::placeholder) {
  color: rgba(164, 144, 194, 0.6) !important;
}

:deep(.el-form-item__label) {
  color: var(--lavender) !important;
}

:deep(.el-alert) {
  background: rgba(74, 78, 143, 0.3);
  border: 1px solid rgba(164, 144, 194, 0.2);
}

:deep(.el-alert__title) {
  color: var(--silver);
}

:deep(.el-alert__description) {
  color: var(--lavender);
}
</style>
