<template>
  <div class="search-page">
    <!-- 搜索区域 -->
    <div class="search-hero">
      <div class="hero-bg"></div>
      <div class="stars"></div>

      <div class="search-container">
        <h1 class="logo">
          <span class="logo-icon">🔍</span>
          语义搜索
        </h1>
        <p class="logo-subtitle">基于 BERT + FAISS 的智能语义检索</p>

        <div class="google-search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="输入自然语言查询，例如：关于机器学习的内容"
            @keyup.enter="handleSearch"
          />
          <el-icon class="clear-icon" v-if="searchQuery" @click="searchQuery = ''"><Close /></el-icon>
        </div>

        <div class="search-actions">
          <el-button type="primary" size="large" @click="handleSearch" class="search-btn">
            搜索
          </el-button>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button class="action-btn" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加文档
        </el-button>
        <el-button class="action-btn" @click="showImportDialog = true">
          <el-icon><FolderOpened /></el-icon>
          批量导入
        </el-button>
        <el-button class="action-btn primary" @click="$router.push('/documents')">
          <el-icon><Document /></el-icon>
          文档库
        </el-button>
        <el-button class="action-btn warning" @click="handleRebuildIndex" :loading="rebuilding">
          <el-icon><Refresh /></el-icon>
          重建索引
        </el-button>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Plus, FolderOpened, Close, Document, Refresh } from '@element-plus/icons-vue'
import { addDocument, importFolder, rebuildIndex } from '../api'

const router = useRouter()
const searchQuery = ref('')
const loading = ref(false)
const rebuilding = ref(false)
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const newDoc = ref({ title: '', text: '' })
const folderPath = ref('')

// 重建索引
const handleRebuildIndex = async () => {
  rebuilding.value = true
  try {
    await rebuildIndex()
    ElMessage.success('索引重建成功，现在可以搜索文档的所有段落')
    // 重新执行搜索
    if (searchQuery.value) {
      handleSearch()
    }
  } catch (error) {
    ElMessage.error('索引重建失败')
  } finally {
    rebuilding.value = false
  }
}

const handleSearch = () => {
  const query = searchQuery.value.trim()
  if (!query) {
    return
  }
  // 跳转到搜索结果页面
  router.push({ path: '/search', query: { q: query } })
}

const submitDocument = () => {
  if (!newDoc.value.text.trim()) {
    return
  }
  addDocument(newDoc.value).then(() => {
    ElMessage.success('文档添加成功')
    newDoc.value = { title: '', text: '' }
    showAddDialog.value = false
  }).catch(() => {
    ElMessage.error('添加文档失败')
  })
}

const submitImport = () => {
  if (!folderPath.value.trim()) {
    return
  }
  loading.value = true
  importFolder(folderPath.value).then((res) => {
    ElMessage.success(`成功导入 ${res.data.count} 个文档`)
    folderPath.value = ''
    showImportDialog.value = false
  }).catch((error) => {
    ElMessage.error('导入失败: ' + (error.response?.data?.error || '未知错误'))
  }).finally(() => {
    loading.value = false
  })
}
</script>

<style scoped>
.search-page {
  min-height: 100vh;
  /* Midnight Galaxy 主题 */
  --deep-purple: #2b1e3e;
  --cosmic-blue: #4a4e8f;
  --lavender: #a490c2;
  --silver: #e6e6fa;
  --glow-purple: #8b5cf6;
  --dark-bg: #1a1429;
}

.search-hero {
  position: relative;
  background: linear-gradient(135deg, var(--deep-purple) 0%, #1a1429 50%, var(--cosmic-blue) 100%);
  padding: 80px 20px 60px;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(74, 78, 143, 0.2) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(164, 144, 194, 0.05) 0%, transparent 40%);
  pointer-events: none;
}

/* 星空动画 */
.stars {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    radial-gradient(2px 2px at 20px 30px, var(--silver), transparent),
    radial-gradient(2px 2px at 40px 70px, rgba(230, 230, 250, 0.8), transparent),
    radial-gradient(1px 1px at 90px 40px, var(--silver), transparent),
    radial-gradient(2px 2px at 130px 80px, rgba(164, 144, 194, 0.9), transparent),
    radial-gradient(1px 1px at 160px 120px, var(--silver), transparent);
  background-size: 200px 200px;
  animation: twinkle 4s ease-in-out infinite;
  opacity: 0.6;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 0.9; }
}

.search-container {
  position: relative;
  max-width: 720px;
  margin: 0 auto;
  text-align: center;
  z-index: 1;
}

.logo {
  color: var(--silver);
  font-size: 52px;
  font-weight: 700;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  text-shadow: 0 0 30px rgba(139, 92, 246, 0.5);
}

.logo-icon {
  font-size: 48px;
  filter: drop-shadow(0 0 15px rgba(164, 144, 194, 0.8));
}

.logo-subtitle {
  color: var(--lavender);
  font-size: 18px;
  margin-bottom: 40px;
  font-weight: 400;
  letter-spacing: 1px;
}

.google-search-box {
  display: flex;
  align-items: center;
  background: rgba(26, 20, 41, 0.8);
  border: 1px solid rgba(164, 144, 194, 0.3);
  border-radius: 28px;
  padding: 16px 24px;
  box-shadow:
    0 4px 30px rgba(0, 0, 0, 0.3),
    0 0 40px rgba(139, 92, 246, 0.1),
    inset 0 0 20px rgba(139, 92, 246, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  max-width: 680px;
  margin: 0 auto;
  backdrop-filter: blur(10px);
}

.google-search-box:focus-within {
  border-color: var(--glow-purple);
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.4),
    0 0 60px rgba(139, 92, 246, 0.25),
    inset 0 0 30px rgba(139, 92, 246, 0.1);
  transform: translateY(-2px);
}

.search-icon {
  color: var(--lavender);
  font-size: 22px;
  margin-right: 16px;
}

.google-search-box input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 17px;
  color: var(--silver);
  background: transparent;
  letter-spacing: 0.3px;
}

.google-search-box input::placeholder {
  color: rgba(164, 144, 194, 0.6);
}

.clear-icon {
  color: var(--lavender);
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  transition: all 0.2s;
}

.clear-icon:hover {
  color: var(--silver);
  background: rgba(164, 144, 194, 0.2);
}

.search-actions {
  margin-top: 28px;
}

.search-btn {
  background: linear-gradient(135deg, var(--glow-purple), var(--cosmic-blue)) !important;
  color: white !important;
  border: none !important;
  padding: 14px 40px !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  border-radius: 24px !important;
  transition: all 0.3s !important;
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4) !important;
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.5) !important;
}

.action-buttons {
  position: relative;
  margin-top: 36px;
  display: flex;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
  z-index: 1;
}

.action-btn {
  background: rgba(164, 144, 194, 0.15) !important;
  border: 1px solid rgba(164, 144, 194, 0.3) !important;
  color: var(--silver) !important;
  padding: 10px 20px !important;
  border-radius: 20px !important;
  font-weight: 500 !important;
  backdrop-filter: blur(10px);
  transition: all 0.2s !important;
}

.action-btn:hover {
  background: rgba(164, 144, 194, 0.25) !important;
  border-color: var(--glow-purple) !important;
  transform: translateY(-1px);
}

.action-btn.primary {
  background: linear-gradient(135deg, var(--glow-purple), var(--cosmic-blue)) !important;
  border: none !important;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
}

.action-btn.primary:hover {
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5) !important;
}

.action-btn.warning {
  background: rgba(245, 158, 11, 0.2) !important;
  border: 1px solid rgba(245, 158, 11, 0.5) !important;
  color: #fbbf24 !important;
}

.action-btn.warning:hover {
  background: rgba(245, 158, 11, 0.3) !important;
  border-color: #f59e0b !important;
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

:deep(.el-button) {
  border-radius: 8px;
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

:deep(.el-empty__description p) {
  color: var(--lavender);
}
</style>
