<template>
  <div class="resource-panel-container">
    <div class="panel-header">
      <h2>资源面板</h2>
      <div class="search-filter">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索资源名称..."
          class="search-input"
          @input="scheduleReload"
        >
        <select v-model="resourceType" class="filter-select" @change="loadResources">
          <option value="all">全部类型</option>
          <option value="文档">文档</option>
          <option value="视频">视频</option>
          <option value="练习题">练习题</option>
          <option value="PPT">PPT</option>
          <option value="其它">其它</option>
        </select>
      </div>
    </div>

    <div class="resources-grid">
      <div
        v-for="resource in resources"
        :key="resource.id"
        class="resource-card"
      >
        <div class="resource-icon">
          {{ getResourceIcon(resource.type) }}
        </div>
        <div class="resource-info">
          <h3 class="resource-title">{{ resource.name }}</h3>
          <p class="resource-description">
            来自教师：{{ resource.teacherName || '—' }} · 发放时间 {{ formatDateTime(resource.distributedAt) }}
          </p>
          <div class="resource-meta">
            <span class="resource-type">{{ resource.type }}</span>
            <span v-if="resource.readStatus" class="resource-date">已读</span>
            <span v-else class="resource-views">未读</span>
          </div>
        </div>
        <div class="resource-actions">
          <button type="button" @click="downloadResource(resource)" class="action-button download-button">
            <span class="download-icon">↓</span> 下载
          </button>
          <button type="button" @click="previewResource(resource)" class="action-button preview-button">
            <span class="preview-icon">👁️</span> 预览
          </button>
        </div>
      </div>

      <div v-if="!loading && resources.length === 0" class="no-resources">
        <div class="no-resources-icon">📚</div>
        <p>暂无匹配的资源</p>
        <small>尝试调整搜索条件或筛选器</small>
      </div>
      <div v-if="loading" class="no-resources">
        <p>加载中...</p>
      </div>
    </div>

    <div v-if="isPreviewVisible" class="modal-overlay" @click.self="closePreview">
      <div class="preview-modal" @click.stop>
        <div class="preview-header">
          <h3>{{ previewResourceData?.name }}</h3>
          <button type="button" @click="closePreview" class="modal-close">×</button>
        </div>
        <div class="preview-body">
          <div v-if="previewResourceData" class="preview-content">
            <div class="preview-info">
              <p><strong>类型:</strong> {{ previewResourceData.type }}</p>
              <p><strong>发放时间:</strong> {{ formatDateTime(previewResourceData.distributedAt) }}</p>
              <p><strong>教师:</strong> {{ previewResourceData.teacherName || '—' }}</p>
            </div>
            <div class="preview-actions">
              <button type="button" @click="downloadResource(previewResourceData)" class="preview-download-button">
                <span class="download-icon">↓</span> 下载资源
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '../store/auth'
import { getStudentResources } from '../api/resources'

const authStore = useAuthStore()
const { user } = storeToRefs(authStore)
const searchQuery = ref('')
const resourceType = ref('all')
const isPreviewVisible = ref(false)
const previewResourceData = ref(null)
const resources = ref([])
const loading = ref(false)

let searchTimer = null
const scheduleReload = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadResources()
  }, 300)
}

const getResourceIcon = (type) => {
  const icons = {
    文档: '📄',
    视频: '🎥',
    练习题: '📝',
    PPT: '📊',
    其它: '📦',
  }
  return icons[type] || '📦'
}

const formatDateTime = (s) => {
  if (!s) return '—'
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return s
  return d.toLocaleString('zh-CN')
}

const fileUrl = (resource) => {
  const p = resource.filePath || ''
  if (!p) return ''
  const path = String(p).replace(/^\//, '')
  return `http://localhost:5000/${path}`
}

const downloadResource = (resource) => {
  const url = fileUrl(resource)
  if (!url) {
    alert('文件路径无效')
    return
  }
  window.open(url, '_blank')
}

const previewResource = (resource) => {
  previewResourceData.value = resource
  isPreviewVisible.value = true
}

const closePreview = () => {
  isPreviewVisible.value = false
  previewResourceData.value = null
}

const loadResources = async () => {
  const sid = user.value?.id
  if (!sid) {
    resources.value = []
    return
  }
  loading.value = true
  try {
    const typeParam = resourceType.value === 'all' ? '' : resourceType.value
    const resp = await getStudentResources(sid, typeParam, searchQuery.value.trim())
    if (resp?.success) {
      resources.value = Array.isArray(resp.data) ? resp.data : []
    } else {
      resources.value = []
    }
  } catch (e) {
    console.error(e)
    resources.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadResources()
})

watch(
  () => user.value?.id,
  () => {
    loadResources()
  }
)
</script>

<style scoped>
.resource-panel-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.panel-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.search-filter {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  width: 250px;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.filter-select {
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.filter-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.resources-grid {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.resource-card {
  background: #f5f7fa;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.resource-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.resource-icon {
  font-size: 48px;
  margin-bottom: 16px;
  text-align: center;
}

.resource-info {
  flex: 1;
  margin-bottom: 16px;
}

.resource-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #333;
}

.resource-description {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.resource-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: #999;
}

.resource-type {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 4px 8px;
  border-radius: 4px;
}

.resource-date {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
  padding: 4px 8px;
  border-radius: 4px;
}

.resource-views {
  background: rgba(255, 193, 7, 0.1);
  color: #ff9800;
  padding: 4px 8px;
  border-radius: 4px;
}

.resource-actions {
  display: flex;
  gap: 8px;
}

.action-button {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.download-button {
  background: #4caf50;
  color: white;
}

.download-button:hover {
  background: #388e3c;
}

.preview-button {
  background: #667eea;
  color: white;
}

.preview-button:hover {
  background: #5568d3;
}

.download-icon, .preview-icon {
  font-size: 12px;
}

.no-resources {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.no-resources-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-resources p {
  font-size: 18px;
  margin: 0 0 8px 0;
}

.no-resources small {
  font-size: 14px;
  opacity: 0.8;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.preview-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.preview-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 24px;
  height: 24px;
}

.modal-close:hover {
  color: #333;
}

.preview-body {
  padding: 20px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-info {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
}

.preview-info p {
  margin: 8px 0;
  font-size: 14px;
  color: #333;
}

.preview-info strong {
  color: #666;
}

.preview-actions {
  display: flex;
  justify-content: flex-end;
}

.preview-download-button {
  background: #4caf50;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.preview-download-button:hover {
  background: #388e3c;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .search-filter {
    flex-direction: column;
  }

  .search-input, .filter-select {
    width: 100%;
  }

  .resources-grid {
    grid-template-columns: 1fr;
  }
}
</style>
