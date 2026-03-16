<template>
  <div class="document-list">
    <el-card>
      <template #header>
        <div class="list-header">
          <span>文档库 ({{ documents.length }})</span>
          <el-button size="small" @click="$emit('refresh')">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-empty v-if="documents.length === 0" description="暂无文档，请添加或导入" />

      <el-table v-else :data="documents" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" width="200" />
        <el-table-column label="内容预览">
          <template #default="{ row }">
            <span class="text-preview">{{ row.text.substring(0, 100) }}{{ row.text.length > 100 ? '...' : '' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="handleDelete(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { Refresh } from '@element-plus/icons-vue'

defineProps({
  documents: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['delete', 'refresh'])

const handleDelete = (id) => {
  emit('delete', id)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.document-list {
  margin-top: 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-preview {
  color: #909399;
  font-size: 13px;
}
</style>
