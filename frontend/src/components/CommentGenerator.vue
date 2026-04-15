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
        <div class="comment-content" v-html="formatContent(comment.content)"></div>
        <div v-if="comment.feedback" class="comment-feedback">
          <div class="feedback-label">学生反馈:</div>
          <div class="feedback-content" v-html="formatContent(comment.feedback)"></div>
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

          <!-- 答题结果输入（仅文本上传的专栏） -->
          <div v-if="isTextColumn" class="form-group">
            <label class="form-label">学生答题结果</label>
            <div class="answer-results">
              <div v-for="(result, index) in answerResults" :key="index" class="answer-item">
                <span class="question-number">第{{ index + 1 }}题：</span>
                <div class="answer-options">
                  <label
                      :class="['answer-option', { active: result === true }]"
                  >
                    <input
                        type="radio"
                        :name="`answer-${index}`"
                        :value="true"
                        v-model="answerResults[index]"
                        style="display: none;"
                    >
                    <span>正确</span>
                  </label>
                  <label
                      :class="['answer-option', { active: result === false }]"
                  >
                    <input
                        type="radio"
                        :name="`answer-${index}`"
                        :value="false"
                        v-model="answerResults[index]"
                        style="display: none;"
                    >
                    <span>错误</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeModal" class="cancel-button" :disabled="isGenerating">取消</button>
          <div class="submit-container" v-if="isGenerating">
            <div class="loading-spinner"></div>
            <span>生成中，请稍候...</span>
          </div>
          <button
              v-else
              @click="generateComment"
              class="submit-button"
              :disabled="!selectedStudentId || !selectedColumnId"
          >
            确认生成
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
const answerResults = ref([]) // 存储直接输入的对错结果
const isTextColumn = ref(false) // 是否为文本上传的专栏

// 数据
const students = ref([])
const columns = ref([])
const comments = ref([])

// 计算属性
const selectedStudent = computed(() => {
  return students.value.find(s => s.id === selectedStudentId.value)
})

const selectedColumn = computed(() => {
  return columns.value.find(c => c.id === selectedColumnId.value)
})

// 方法
const openModal = () => {
  isModalVisible.value = true
}

const closeModal = () => {
  isModalVisible.value = false
  // 重置表单
  selectedStudentId.value = ''
  selectedColumnId.value = ''
  selectedStyle.value = 'encouraging'
  focusAreas.value = {
    academic: true,
    behavior: false,
    attitude: true,
    social: false
  }
  // 重置答题结果
  answerResults.value = []
  isTextColumn.value = false
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getColumnById = (columnId) => {
  return columns.value.find(c => c.id === columnId)
}

// 格式化内容，将换行符转换为<br>标签
const formatContent = (content) => {
  if (!content) return ''
  // 将换行符转换为<br>标签，并转义HTML特殊字符
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
}

const generateComment = async () => {
  if (!selectedStudentId.value || !selectedColumnId.value) {
    alert('请选择学生和专栏')
    return
  }

  // 检查文本专栏的答题结果是否都已填写
  if (isTextColumn.value) {
    const allAnswered = answerResults.value.every(result => result !== null)
    if (!allAnswered) {
      alert('请填写所有题目的答题结果')
      return
    }
  }

  isGenerating.value = true
  try {
    const focusAreasList = Object.entries(focusAreas.value)
      .filter(([_, value]) => value)
      .map(([key, _]) => key)

    const commentData = {
      studentId: selectedStudentId.value,
      columnId: selectedColumnId.value,
      style: selectedStyle.value,
      focusAreas: focusAreasList
    }

    // 如果是文本专栏，添加答题结果
    if (isTextColumn.value) {
      commentData.answerResults = answerResults.value
    }

    const result = await apiGenerateComment(commentData)

    if (!result?.success) throw new Error(result?.message || '后端未返回评语结果')
    alert('评语生成成功！')
    closeModal()
    // 刷新评语列表
    await loadComments()
  } catch (error) {
    console.error('生成评语失败:', error)
    alert('生成评语失败: ' + error.message)
  } finally {
    isGenerating.value = false
  }
}

const loadStudents = async () => {
  try {
    const result = await getStudents()
    students.value = result?.success ? (result.data || []) : []
  } catch (error) {
    console.error('加载学生列表失败:', error)
  }
}

const loadColumns = async () => {
  try {
    const result = await getColumns()
    columns.value = result?.success ? (result.data || []) : []
  } catch (error) {
    console.error('加载专栏列表失败:', error)
  }
}

const loadComments = async () => {
  try {
    const result = await getStudentComments(selectedStudentId.value || undefined)
    comments.value = result?.success ? (result.data || []) : []
  } catch (error) {
    console.error('加载评语列表失败:', error)
  }
}

// 监听专栏选择变化
watch(selectedColumnId, (newColumnId) => {
  if (newColumnId) {
    const column = columns.value.find(c => c.id === newColumnId)
    if (column) {
      // 检查是否为文本上传的专栏（通过检查是否有题目文本但没有图片路径）
      isTextColumn.value = !!column.questionText && !column.questionImagePath1
      
      // 根据专栏的题目数量初始化答题结果数组
      if (isTextColumn.value) {
        // 解析题目文本，计算题目数量
        let questionCount = 0
        try {
          // 尝试解析JSON格式的questionText
          const questionText = column.questionText
          const parsedQuestions = JSON.parse(questionText)
          if (typeof parsedQuestions === 'object' && parsedQuestions !== null) {
            questionCount = Object.keys(parsedQuestions).length
          } else {
            // 如果不是JSON格式，尝试按分号分割
            const questions = questionText.split(';').filter(q => q.trim())
            questionCount = questions.length
          }
        } catch (error) {
          // 解析失败，使用默认值
          questionCount = 0
        }
        
        // 初始化答题结果数组
        answerResults.value = new Array(questionCount).fill(null)
      } else {
        answerResults.value = []
      }
    }
  } else {
    isTextColumn.value = false
    answerResults.value = []
  }
})

// 生命周期
onMounted(() => {
  loadStudents()
  loadColumns()
  loadComments()
})
</script>

<style scoped>
.comment-generator-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.generator-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.generator-header h2 {
  margin: 0;
  color: #333;
  font-size: 24px;
}

.generate-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.generate-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.comment-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.comment-date {
  color: #666;
  font-size: 12px;
}

.comment-column {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.comment-content {
  color: #333;
  line-height: 1.8;
  margin-bottom: 12px;
  word-wrap: break-word;
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
  line-height: 1.8;
  word-wrap: break-word;
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
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: #f5f5f5;
  color: #333;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

.form-select {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s ease;
}

.form-select:focus {
  outline: none;
  border-color: #667eea;
}

.style-options {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.style-option {
  flex: 1;
  min-width: 80px;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.style-option:hover {
  border-color: #667eea;
}

.style-option.active {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.focus-areas {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.focus-area {
  padding: 8px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.focus-area:hover {
  border-color: #667eea;
}

.focus-area.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 答题结果输入样式 */
.answer-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.answer-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.question-number {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  min-width: 80px;
}

.answer-options {
  display: flex;
  gap: 8px;
  flex: 1;
}

.answer-option {
  flex: 1;
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.answer-option:hover {
  border-color: #667eea;
}

.answer-option.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #eee;
}

.cancel-button {
  padding: 12px 24px;
  border: 2px solid #e0e0e0;
  background: white;
  color: #666;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.cancel-button:hover {
  border-color: #999;
  color: #333;
}

.submit-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 加载动画样式 */
.submit-container {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
