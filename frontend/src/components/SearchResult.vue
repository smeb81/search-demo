<template>
  <div class="search-result">
    <el-card v-if="loading" class="loading-card">
      <el-skeleton :rows="3" animated />
    </el-card>

    <el-empty v-else-if="results.length === 0" description="暂无搜索结果" />

    <el-card v-else v-for="(result, index) in results" :key="result.id" class="result-card">
      <template #header>
        <div class="result-header">
          <span class="result-title">
            <el-tag type="primary" size="small">文档 {{ result.id }}</el-tag>
            {{ result.title || '无标题' }}
          </span>
          <el-tag type="success" effect="dark">
            相似度: {{ (result.similarity * 100).toFixed(1) }}%
          </el-tag>
        </div>
      </template>
      <div class="result-text">
        {{ result.text }}
      </div>
    </el-card>
  </div>
</template>

<script setup>
defineProps({
  results: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.search-result {
  margin-bottom: 20px;
}

.loading-card,
.result-card {
  margin-bottom: 15px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-title {
  font-weight: bold;
}

.result-text {
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}
</style>
