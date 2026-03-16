<template>
  <div class="search-bar">
    <el-card class="search-card">
      <el-input
        v-model="searchQuery"
        placeholder="输入自然语言查询，例如：'关于机器学习的文档'"
        size="large"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button type="primary" @click="handleSearch" :loading="loading">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </template>
      </el-input>
    </el-card>

    <el-card class="action-card">
      <el-space wrap>
        <el-button type="success" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加文档
        </el-button>
        <el-button type="warning" @click="showImportDialog = true">
          <el-icon><FolderOpened /></el-icon>
          批量导入
        </el-button>
      </el-space>
    </el-card>

    <!-- 添加文档对话框 -->
    <el-dialog v-model="showAddDialog" title="添加文档" width="500px">
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
    <el-dialog v-model="showImportDialog" title="批量导入文档" width="500px">
      <el-form label-width="80px">
        <el-form-item label="文件夹">
          <el-input v-model="folderPath" placeholder="输入文件夹路径，如：D:/documents" />
        </el-form-item>
        <el-alert
          title="支持格式"
          type="info"
          :closable="false"
          description="支持 .txt 和 .md 文件"
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
import { Search, Plus, FolderOpened } from '@element-plus/icons-vue'

const emit = defineEmits(['search', 'add-document', 'import-folder'])

const searchQuery = ref('')
const loading = ref(false)
const showAddDialog = ref(false)
const showImportDialog = ref(false)
const newDoc = ref({ title: '', text: '' })
const folderPath = ref('')

const handleSearch = () => {
  emit('search', searchQuery.value)
}

const submitDocument = () => {
  if (!newDoc.value.text.trim()) {
    return
  }
  emit('add-document', newDoc.value)
  newDoc.value = { title: '', text: '' }
  showAddDialog.value = false
}

const submitImport = () => {
  if (!folderPath.value.trim()) {
    return
  }
  emit('import-folder', folderPath.value)
  folderPath.value = ''
  showImportDialog.value = false
}
</script>

<style scoped>
.search-bar {
  margin-bottom: 20px;
}

.search-card {
  margin-bottom: 15px;
}

.action-card {
  margin-bottom: 15px;
}
</style>
