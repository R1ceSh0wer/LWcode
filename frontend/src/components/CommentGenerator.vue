<template>
  <div class="comment-generator-container">
    <div class="generator-header">
      <h2>AI评语生成器</h2>
      <button @click="openModal" class="generate-button">
        生成评语
      </button>
    </div>

    <!-- 评语列表 -->
    <div class="comments-list">
      <div
          v-for="comment in comments"
          :key="comment.id"
          class="comment-item"
      >
        <div class="comment-header">
          <span class="comment-date">{{ formatDate(comment.created) }}</span>
          <span class="comment-column">{{ getColumnById(comment.columnId)?.name }}</span>
        </div>
        <div class="comment-content">
          {{ comment.content }}
        </div>
        <div v-if="comment.feedback" class="comment-feedback">
          <div class="feedback-label">学生反馈:</div>
          <div class="feedback-content">{{ comment.feedback }}</div>
        </div>
      </div>

      <div v-if="comments.length === 0" class="no-comments">
        暂无评语记录
      </div>
    </div>

    <!-- 生成评语模态框 -->
    <div v-if="isModalVisible" class="modal-overlay">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>生成学生评语</h3>
          <button @click="closeModal" class="modal-close">×</button>
        </div>

        <div class="modal-body">
          <!-- 学生选择 -->
          <div class="form-group">
            <label class="form-label">选择学生</label>
            <select v-model="selectedStudentId" class="form-select">
              <option value="">请选择学生</option>
              <option
                  v-for="student in students"
                  :key="student.id"
                  :value="student.id"
              >
                {{ student.name }} ({{ student.studentId }})
              </option>
            </select>
          </div>

          <!-- 专栏选择 -->
          <div class="form-group">
            <label class="form-label">选择专栏</label>
            <select v-model="selectedColumnId" class="form-select">
              <option value="">请选择专栏</option>
              <option
                  v-for="column in columns"
                  :key="column.id"
                  :value="column.id"
              >
                {{ column.name }}
              </option>
            </select>
          </div>

          <!-- 评语风格选择 -->
          <div class="form-group">
            <label class="form-label">评语风格</label>
            <div class="style-options">
              <label
                  :class="['style-option', { active: selectedStyle === 'encouraging' }]"
              >
                <input
                    type="radio"
                    name="style"
                    value="encouraging"
                    v-model="selectedStyle"
                    style="display: none;"
                >
                <span>鼓励型</span>
              </label>
              <label
                  :class="['style-option', { active: selectedStyle === 'detailed' }]"
              >
                <input
                    type="radio"
                    name="style"
                    value="detailed"
                    v-model="selectedStyle"
                    style="display: none;"
                >
                <span>详细型</span>
              </label>
              <label
                  :class="['style-option', { active: selectedStyle === 'concise' }]"
              >
                <input
                    type="radio"
                    name="style"
                    value="concise"
                    v-model="selectedStyle"
                    style="display: none;"
                >
                <span>简洁型</span>
              </label>
            </div>
          </div>

          <!-- 关注领域 -->
          <div class="form-group">
            <label class="form-label">关注领域 (可选)</label>
            <div class="focus-areas">
              <label
                  :class="['focus-area', { active: focusAreas.academic }]"
              >
                <input
                    type="checkbox"
                    v-model="focusAreas.academic"
                    style="display: none;"
                >
                <span>学业表现</span>
              </label>
              <label
                  :class="['focus-area', { active: focusAreas.behavior }]"
              >
                <input
                    type="checkbox"
                    v-model="focusAreas.behavior"
                    style="display: none;"
                >
                <span>行为表现</span>
              </label>
              <label
                  :class="['focus-area', { active: focusAreas.attitude }]"
              >
                <input
                    type="checkbox"
                    v-model="focusAreas.attitude"
                    style="display: none;"
                >
                <span>学习态度</span>
              </label>
              <label
                  :class="['focus-area', { active: focusAreas.social }]"
              >
                <input
                    type="checkbox"
                    v-model="focusAreas.social"
                    style="display: none;"
                >
                <span>社交能力</span>
              </label>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeModal" class="cancel-button">取消</button>
          <button
              @click="generateComment"
              class="submit-button"
              :disabled="!selectedStudentId || !selectedColumnId || isGenerating"
          >
            {{ isGenerating ? '生成中...' : '确认生成' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { getStudents } from '../api/students'
import { getColumns } from '../api/columns'
import { generateComment as apiGenerateComment, getStudentComments } from '../api/comments'

// 组件状态
const isModalVisible = ref(false)
const isGenerating = ref(false)
const selectedStudentId = ref('')
const selectedColumnId = ref('')
const selectedStyle = ref('encouraging')
const focusAreas = ref({
  academic: true,
  behavior: false,
  attitude: true,
  social: false
})

// 数据
const students = ref([])
const columns = ref([])
const comments = ref([])

// 辅助函数
const getColumnById = (id) => {
  return columns.value.find(column => column.id === id)
}

// 日期格式化
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 模态框控制
const openModal = async () => {
  // 确保数据已加载
  if (students.value.length === 0) {
    await loadData()
  }

  // 设置默认选中第一个学生和专栏
  if (students.value.length > 0 && !selectedStudentId.value) {
    selectedStudentId.value = students.value[0].id
  }
  if (columns.value.length > 0 && !selectedColumnId.value) {
    selectedColumnId.value = columns.value[0].id
  }

  isModalVisible.value = true
}

const closeModal = () => {
  isModalVisible.value = false
}

// 生成评语
const generateComment = async () => {
  if (!selectedStudentId.value || !selectedColumnId.value) {
    console.warn('请选择学生和专栏')
    return
  }

  try {
    isGenerating.value = true

    // 获取选中的学生信息
    const selectedStudent = students.value.find(s => s.id === selectedStudentId.value)
    const selectedColumn = columns.value.find(c => c.id === selectedColumnId.value)

    // 构造请求数据
    const requestData = {
      studentId: selectedStudentId.value,
      studentName: selectedStudent?.name || '',
      studentNo: selectedStudent?.studentId || '',
      columnId: selectedColumnId.value,
      columnName: selectedColumn?.name || '',
      style: selectedStyle.value,
      focusAreas: focusAreas.value
    }

    console.log('发送请求数据:', requestData)

    const result = await apiGenerateComment(requestData)

    if (result) {
      console.log('收到响应:', result)

      // 添加到评语列表
      const newComment = {
        id: Date.now().toString(),
        studentId: selectedStudentId.value,
        columnId: selectedColumnId.value,
        content: result.content || '生成评语内容',
        created: new Date().toISOString(),
        feedback: result.feedback || ''
      }

      comments.value.unshift(newComment)

      // 关闭模态框
      closeModal()

      // 显示成功消息
      alert('评语生成成功！')
    }
  } catch (error) {
    console.error('生成评语失败:', error)
    alert('生成评语失败，请检查网络连接或稍后重试')
  } finally {
    isGenerating.value = false
  }
}

// 重置表单
const resetForm = () => {
  selectedStyle.value = 'encouraging'
  focusAreas.value = {
    academic: true,
    behavior: false,
    attitude: true,
    social: false
  }
}

// 加载数据
const loadData = async () => {
  try {
    console.log('开始加载数据...')

    const [studentsData, columnsData] = await Promise.all([
      getStudents(),
      getColumns()
    ])

    console.log('学生数据:', studentsData)
    console.log('专栏数据:', columnsData)

    students.value = studentsData || []
    columns.value = columnsData || []

  } catch (error) {
    console.error('加载数据失败:', error)
    // 设置默认数据用于测试
    students.value = [
      { id: '1', name: '张三', studentId: '2021001' },
      { id: '2', name: '李四', studentId: '2021002' }
    ]
    columns.value = [
      { id: '1', name: '期中评价' },
      { id: '2', name: '期末评价' },
      { id: '3', name: '思想品德鉴定' }
    ]
  }
}

// 加载评语
const loadComments = async () => {
  try {
    if (selectedStudentId.value) {
      const commentsData = await getStudentComments(selectedStudentId.value)
      comments.value = commentsData || []
    }
  } catch (error) {
    console.error('加载评语失败:', error)
  }
}

// 监听学生选择变化
watch(selectedStudentId, (newVal) => {
  if (newVal) {
    loadComments()
  } else {
    comments.value = []
  }
})

// 监听模态框显示/隐藏
watch(isModalVisible, (newVal) => {
  if (newVal) {
    console.log('模态框打开，当前选择:', {
      studentId: selectedStudentId.value,
      columnId: selectedColumnId.value,
      students: students.value.length,
      columns: columns.value.length
    })
  }
})

// 生命周期
onMounted(() => {
  console.log('组件挂载完成')
  loadData()
})

// 暴露给父组件的方法
defineExpose({
  openModal
})
</script>

<style scoped>
/* 样式保持不变，但确保所有样式都正确复制 */
.comment-generator-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.generator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.generator-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.generate-button {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.generate-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.comments-list {
  padding: 20px;
}

.comment-item {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #666;
}

.comment-date {
  font-weight: 500;
}

.comment-column {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.comment-content {
  color: #333;
  line-height: 1.6;
  margin-bottom: 12px;
}

.comment-feedback {
  background: rgba(76, 175, 80, 0.1);
  border-left: 4px solid #4caf50;
  padding: 12px;
  border-radius: 4px;
}

.feedback-label {
  font-weight: 600;
  color: #4caf50;
  margin-bottom: 4px;
}

.feedback-content {
  color: #333;
  line-height: 1.5;
}

.no-comments {
  text-align: center;
  color: #999;
  padding: 40px 0;
}

/* 模态框样式 */
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

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
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
  line-height: 1;
}

.modal-close:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.form-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: white;
  cursor: pointer;
}

.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.style-options {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.style-option {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
  min-width: 100px;
}

.style-option:hover {
  border-color: #667eea;
}

.style-option.active {
  border-color: #667eea;
  background-color: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.focus-areas {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.focus-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
  min-width: 120px;
}

.focus-area:hover {
  border-color: #667eea;
}

.focus-area.active {
  border-color: #667eea;
  background-color: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #e0e0e0;
}

.cancel-button {
  padding: 12px 24px;
  background: #f5f7fa;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-button:hover {
  background: #e0e0e0;
}

.submit-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.submit-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>