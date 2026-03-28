<template>
  <div class="result-page">
    <!-- 顶部搜索栏 -->
    <div class="search-header">
      <div class="header-bg"></div>
      <div class="header-container">
        <router-link to="/" class="logo">
          <span class="logo-icon">🔍</span>
          <span class="logo-text">语义搜索</span>
        </router-link>

        <div class="search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="输入自然语言查询，例如：关于机器学习的内容"
            @keyup.enter="handleSearch"
          />
          <el-icon class="clear-icon" v-if="searchQuery" @click="searchQuery = ''"><Close /></el-icon>
        </div>
      </div>
    </div>

    <!-- 搜索结果区域 -->
    <div class="results-section">
      <div v-if="loading" class="loading">
        <div class="skeleton-item" v-for="i in 3" :key="i">
          <el-skeleton :rows="3" animated />
        </div>
      </div>

      <el-empty v-else-if="results.length === 0 && hasSearched" description="未找到相关文档" />

      <div v-else-if="results.length > 0" class="result-list">
        <div class="results-header">
          <div class="results-count">
            搜索 "<span class="query-text">{{ query }}</span>" 找到 <strong>{{ results.length }}</strong> 条相关结果
          </div>
        </div>

        <div
          v-for="result in results"
          :key="result.id"
          class="result-item"
        >
          <div class="result-header">
            <div class="result-title-wrap">
              <span class="result-id">#{{ result.id }}</span>
              <span class="result-title">{{ result.title || '无标题' }}</span>
            </div>
            <el-tag type="success" effect="dark" class="similarity-tag">
              {{ (result.similarity * 100).toFixed(1) }}%
            </el-tag>
          </div>
          <div class="result-text" v-html="highlightText(result.text, query)"></div>
        </div>
      </div>

      <!-- 未搜索状态 -->
      <div v-else class="empty-state">
        <div class="empty-icon">🔎</div>
        <p class="empty-text">输入关键词开始搜索</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Close } from '@element-plus/icons-vue'
import { searchDocuments } from '../api'

const route = useRoute()
const router = useRouter()

const searchQuery = ref('')
const query = ref('')
const results = ref([])
const loading = ref(false)
const hasSearched = ref(false)

// 从 URL 获取查询参数并搜索
onMounted(() => {
  const q = route.query.q
  if (q) {
    searchQuery.value = q
    query.value = q
    handleSearch()
  }
})

// 监听路由变化
watch(() => route.query.q, (newQuery) => {
  if (newQuery && newQuery !== query.value) {
    searchQuery.value = newQuery
    query.value = newQuery
    handleSearch()
  }
})

// 搜索处理
const handleSearch = async () => {
  const q = searchQuery.value.trim()
  if (!q) {
    results.value = []
    hasSearched.value = false
    return
  }

  // 更新 URL
  router.replace({ query: { q } })
  query.value = q
  hasSearched.value = true
  loading.value = true

  try {
    const res = await searchDocuments(q)
    results.value = res.data.results || []
  } catch (error) {
    ElMessage.error('搜索失败')
    results.value = []
  } finally {
    loading.value = false
  }
}

// 高亮与搜索词相关的文本
const highlightText = (text, queryStr) => {
  if (!text || !queryStr) return text

  // 转义HTML特殊字符
  let safeText = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // 分词查询词
  const queryWords = queryStr.toLowerCase().split(/[\s,，、。.!！?？]+/).filter(w => w.length > 0)

  if (queryWords.length === 0) return safeText

  // 高亮所有匹配的关键词
  queryWords.forEach(word => {
    if (word.length >= 1) {
      const regex = new RegExp(`(${escapeRegex(word)})`, 'gi')
      safeText = safeText.replace(regex, '<mark class="highlight">$1</mark>')
    }
  })

  return safeText
}

// 转义正则表达式特殊字符
const escapeRegex = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
</script>

<style scoped>
.result-page {
  min-height: 100vh;
  background: #1a1429;
}

.search-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: linear-gradient(135deg, #2b1e3e 0%, #1a1429 100%);
  border-bottom: 1px solid rgba(164, 144, 194, 0.15);
}

.header-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(ellipse at 30% 50%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 50%, rgba(74, 78, 143, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.header-container {
  position: relative;
  max-width: 900px;
  margin: 0 auto;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  flex-shrink: 0;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: #e6e6fa;
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  background: rgba(26, 20, 41, 0.8);
  border: 1px solid rgba(164, 144, 194, 0.3);
  border-radius: 24px;
  padding: 12px 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.search-box:focus-within {
  border-color: #8b5cf6;
  box-shadow: 0 0 30px rgba(139, 92, 246, 0.2);
}

.search-icon {
  color: #a490c2;
  font-size: 18px;
  margin-right: 12px;
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 15px;
  color: #e6e6fa;
  background: transparent;
}

.search-box input::placeholder {
  color: rgba(164, 144, 194, 0.6);
}

.clear-icon {
  color: #a490c2;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  transition: all 0.2s;
}

.clear-icon:hover {
  color: #e6e6fa;
  background: rgba(164, 144, 194, 0.2);
}

.results-section {
  max-width: 850px;
  margin: 0 auto;
  padding: 40px 20px;
  min-height: calc(100vh - 80px);
}

.results-header {
  margin-bottom: 24px;
}

.results-count {
  color: #a490c2;
  font-size: 15px;
}

.query-text {
  color: #8b5cf6;
  font-weight: 600;
}

.results-count strong {
  color: #8b5cf6;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.result-item {
  background: linear-gradient(135deg, rgba(43, 30, 62, 0.8), rgba(26, 20, 41, 0.9));
  border: 1px solid rgba(164, 144, 194, 0.15);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  transition: all 0.25s ease;
}

.result-item:hover {
  border-color: #8b5cf6;
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.15);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.result-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-id {
  background: linear-gradient(135deg, #8b5cf6, #4a4e8f);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

.result-title {
  font-weight: 600;
  font-size: 17px;
  color: #e6e6fa;
}

.similarity-tag {
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 16px;
}

.result-text {
  color: rgba(230, 230, 250, 0.8);
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 180px;
  overflow-y: auto;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border-left: 3px solid #8b5cf6;
}

.result-text::-webkit-scrollbar {
  width: 6px;
}

.result-text::-webkit-scrollbar-track {
  background: rgba(164, 144, 194, 0.1);
  border-radius: 3px;
}

.result-text::-webkit-scrollbar-thumb {
  background: #4a4e8f;
  border-radius: 3px;
}

/* 高亮样式 */
:deep(.highlight) {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(74, 78, 143, 0.4));
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.3);
}

.loading {
  background: rgba(43, 30, 62, 0.5);
  border-radius: 16px;
  padding: 24px;
}

.skeleton-item {
  padding: 16px 0;
  border-bottom: 1px solid rgba(164, 144, 194, 0.1);
}

.skeleton-item:last-child {
  border-bottom: none;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-text {
  color: #a490c2;
  font-size: 16px;
}

:deep(.el-empty__description p) {
  color: #a490c2;
}
</style>
