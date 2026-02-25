<template>
  <div class="dashboard-container">
    <!-- 顶部导航栏 -->
    <nav class="top-navigation">
      <div class="nav-left">
        <div class="logo">
          <span class="logo-icon">🎓</span>
          <h1 class="logo-text">智能教育系统</h1>
        </div>
      </div>
      <div class="nav-right">
        <div class="user-info">
          <span class="user-name">{{ currentUser.name }}</span>
          <button @click="logout" class="logout-button">
            <i class="logout-icon">🚪</i> 退出登录
          </button>
        </div>
      </div>
    </nav>

    <!-- 侧边导航栏 -->
    <aside class="side-navigation">
      <div class="nav-section">
        <h3 class="section-title">学习功能</h3>
        <ul class="nav-items">
          <li 
            :class="['nav-item', { active: activeSection === 'knowledge-graph' }]"
            @click="showSection('knowledge-graph')"
          >
            <i class="nav-icon">🧠</i>
            <span class="nav-text">知识图谱</span>
          </li>
          <li 
            :class="['nav-item', { active: activeSection === 'my-comments' }]"
            @click="showSection('my-comments')"
          >
            <i class="nav-icon">💬</i>
            <span class="nav-text">我的评语</span>
          </li>
          <li 
            :class="['nav-item', { active: activeSection === 'learning-resources' }]"
            @click="showSection('learning-resources')"
          >
            <i class="nav-icon">📚</i>
            <span class="nav-text">学习资源</span>
          </li>
          <li 
            :class="['nav-item', { active: activeSection === 'learning-progress' }]"
            @click="showSection('learning-progress')"
          >
            <i class="nav-icon">📊</i>
            <span class="nav-text">学习进度</span>
          </li>
          <li 
            :class="['nav-item', { active: activeSection === 'practice-exercises' }]"
            @click="showSection('practice-exercises')"
          >
            <i class="nav-icon">✏️</i>
            <span class="nav-text">练习题库</span>
          </li>
          <li 
            :class="['nav-item', { active: activeSection === 'smart-qa' }]"
            @click="showSection('smart-qa')"
          >
            <i class="nav-icon">🤖</i>
            <span class="nav-text">智能问答</span>
          </li>
        </ul>
      </div>

      <div class="nav-section">
        <h3 class="section-title">个人中心</h3>
        <ul class="nav-items">
          <li 
            :class="['nav-item', { active: activeSection === 'profile' }]"
            @click="showSection('profile')"
          >
            <i class="nav-icon">👤</i>
            <span class="nav-text">个人资料</span>
          </li>
          <li 
            :class="['nav-item', { active: activeSection === 'feedback' }]"
            @click="showSection('feedback')"
          >
            <i class="nav-icon">✉️</i>
            <span class="nav-text">反馈建议</span>
          </li>
        </ul>
      </div>
    </aside>

    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 知识图谱区域 -->
      <div 
        v-if="activeSection === 'knowledge-graph'" 
        class="section-container"
      >
        <div class="section-header">
          <h2>知识图谱</h2>
          <p class="section-description">探索知识之间的关联与结构</p>
        </div>
        <KnowledgeGraph />
      </div>

      <!-- 我的评语区域 -->
      <div 
        v-if="activeSection === 'my-comments'" 
        class="section-container"
      >
        <div class="section-header">
          <h2>我的评语</h2>
          <div class="header-actions">
            <button 
              @click="generateSummary" 
              class="generate-summary-button"
              :disabled="myComments.length === 0 || isGeneratingSummary"
            >
              {{ isGeneratingSummary ? '生成中...' : '生成总评' }}
            </button>
            <p class="section-description">查看教师对我的评价</p>
          </div>
        </div>
        <div class="comments-container">
          <div 
            v-for="comment in myComments" 
            :key="comment.id"
            class="comment-card"
          >
            <div class="comment-header">
              <h3 class="comment-column">{{ getColumnById(comment.columnId)?.name }}</h3>
              <span class="comment-date">{{ formatDate(comment.createdAt) }}</span>
            </div>
            <div class="comment-content">
              {{ comment.content }}
            </div>
            <div class="comment-actions">
              <button 
                @click="showCommentDetails(comment)" 
                class="view-details-button"
              >
                📋 查看详情
              </button>
            </div>
            <div v-if="!comment.feedback || comment.feedback.trim() === ''" class="comment-feedback-section">
              <h4 class="feedback-title">提交反馈</h4>
              <textarea 
                v-model="commentFeedback[comment.id]" 
                placeholder="请输入您的反馈意见..."
                class="feedback-input"
                rows="3"
              ></textarea>
              <button 
                @click="submitFeedback(comment.id)" 
                class="submit-feedback-button"
                :disabled="!commentFeedback[comment.id]"
              >
                提交反馈
              </button>
            </div>
            <div v-else class="feedback-display">
              <div v-if="editingFeedback[comment.id]">
                <h4 class="feedback-title">修改反馈</h4>
                <textarea 
                  v-model="commentFeedback[comment.id]" 
                  placeholder="请输入您的反馈意见..."
                  class="feedback-input"
                  rows="3"
                ></textarea>
                <div class="feedback-buttons">
                  <button 
                    @click="updateFeedback(comment.id)" 
                    class="submit-feedback-button"
                    :disabled="!commentFeedback[comment.id]"
                  >
                    保存修改
                  </button>
                  <button 
                    @click="cancelEditFeedback(comment.id)" 
                    class="submit-feedback-button"
                  >
                    取消
                  </button>
                </div>
              </div>
              <div v-else>
                <h4 class="feedback-title">我的反馈</h4>
                <div class="user-feedback-content">
                  {{ comment.feedback }}
                </div>
                <button 
                  @click="startEditFeedback(comment.id)" 
                  class="submit-feedback-button"
                >
                  修改反馈
                </button>
              </div>
            </div>
          </div>
          
          <div v-if="myComments.length === 0" class="no-comments">
            <div class="no-comments-icon">💬</div>
            <h3>暂无评语</h3>
            <p>教师还没有给您生成评语，请耐心等待</p>
          </div>
        </div>
        
        <!-- 总结评语区域 -->
        <div v-if="summaryComment" class="summary-comment-container">
          <div class="section-header">
            <h2>总结评语</h2>
            <p class="section-description">基于所有评语的综合评价</p>
          </div>
          <div class="summary-comment-card">
            <div class="summary-header">
              <h3 class="summary-title">学习阶段总结</h3>
              <span class="summary-date">{{ formatDate(summaryComment.createdAt) }}</span>
            </div>
            <div class="summary-content">
              {{ summaryComment.content }}
            </div>
          </div>
        </div>
      </div>

      <!-- 学习资源区域 -->
      <div 
        v-if="activeSection === 'learning-resources'" 
        class="section-container"
      >
        <div class="section-header">
          <h2>学习资源</h2>
          <p class="section-description">浏览和下载学习资源</p>
        </div>
        <ResourcePanel />
      </div>

      <!-- 学习进度区域 -->
      <div 
        v-if="activeSection === 'learning-progress'" 
        class="section-container"
      >
        <div class="section-header">
          <h2>学习进度</h2>
          <p class="section-description">查看您的学习进度和统计数据</p>
        </div>
      </div>

      <!-- 练习题库区域 -->
      <div 
        v-if="activeSection === 'practice-exercises'" 
        class="section-container"
      >
        <div class="section-header">
          <h2>练习题库</h2>
          <p class="section-description">练习题目，巩固学习成果</p>
        </div>
      </div>

      <!-- 智能问答区域 -->
      <div 
        v-if="activeSection === 'smart-qa'" 
        class="section-container"
      >
        <div class="section-header">
          <h2>智能问答</h2>
          <p class="section-description">向AI提问，获取学习帮助</p>
        </div>
        <!-- 智能问答内容区域 -->
        <div class="smart-qa-container">
          <!-- 会话列表 -->
          <div class="conversation-list">
            <div 
              v-for="conversation in conversations" 
              :key="conversation.id"
              :class="['conversation-item', { active: currentConversationId === conversation.id }]"
              @click="selectConversation(conversation.id)"
            >
              <!-- 重命名输入框 -->
              <div v-if="isRenaming && editingConversationId === conversation.id" class="rename-input-container">
                <input 
                  v-model="editConversationName"
                  @keyup.enter="finishRenameConversation"
                  @blur="finishRenameConversation"
                  class="rename-input"
                  ref="renameInput"
                >
              </div>
              <!-- 会话标题 -->
              <div 
                v-else 
                class="conversation-title"
                @dblclick="startRenameConversation(conversation.id, conversation.title)"
              >
                {{ conversation.title }}
              </div>
              
              <div class="conversation-preview">{{ conversation.preview }}</div>
              <div class="conversation-time">{{ conversation.updated_at }}</div>
              
              <!-- 操作按钮 -->
              <div class="conversation-actions">
                <button 
                  @click.stop="startRenameConversation(conversation.id, conversation.title)"
                  class="action-btn rename-btn"
                  title="重命名"
                >
                  ✏️
                </button>
                <button 
                  @click.stop="removeConversation(conversation.id)"
                  class="action-btn delete-btn"
                  title="删除"
                >
                  🗑️
                </button>
              </div>
            </div>
            <button @click="createNewConversation" class="new-conversation-btn">
              + 新建会话
            </button>
          </div>
          
          <!-- 聊天界面 -->
          <div class="chat-interface">
            <!-- 聊天消息 -->
            <div class="chat-messages">
              <div 
                v-for="message in chatHistory" 
                :key="message.id"
                :class="['message', message.role]"
              >
                <div class="message-name">{{ message.name }}</div>
                <div class="message-content">{{ message.content }}</div>
              </div>
              <div v-if="isLoading" class="message assistant">
                <div class="message-content loading">AI正在思考...</div>
              </div>
            </div>
            
            <!-- 输入区域 -->
            <div class="input-area">
              <textarea 
                v-model="inputMessage"
                placeholder="请输入您的问题..."
                @keyup.enter.exact="sendMessage"
              ></textarea>
              <button 
                @click="sendMessage" 
                class="send-btn"
                :disabled="!inputMessage.trim() || isLoading"
              >
                发送
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 个人资料区域 -->
      <div 
        v-if="activeSection === 'profile'" 
        class="section-container"
      >
        <div class="section-header">
          <h2>个人资料</h2>
          <p class="section-description">查看和修改个人信息</p>
        </div>
        <div class="profile-container">
          <div class="profile-info">
            <div class="profile-avatar">
              <div class="avatar-icon">👤</div>
            </div>
            <div class="profile-details">
              <div class="profile-item">
                <label class="profile-label">姓名:</label>
                <span class="profile-value">{{ currentUser.name }}</span>
              </div>
              <div class="profile-item">
                <label class="profile-label">学号:</label>
                <span class="profile-value">{{ studentProfile.studentId }}</span>
              </div>
              <div class="profile-item">
                <label class="profile-label">班级:</label>
                <span class="profile-value">{{ studentProfile.className }}</span>
              </div>
              <div class="profile-item">
                <label class="profile-label">邮箱:</label>
                <span class="profile-value">{{ currentUser.email }}</span>
              </div>
              <div class="profile-item">
                <label class="profile-label">注册时间:</label>
                <span class="profile-value">{{ formatDate(currentUser.createdAt) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 反馈建议区域 -->
      <div 
        v-if="activeSection === 'feedback'" 
        class="section-container"
      >
        <div class="section-header">
          <h2>反馈建议</h2>
          <p class="section-description">为系统改进提供您的建议</p>
        </div>
        <div class="feedback-form-container">
          <form @submit.prevent="submitFeedbackForm">
            <div class="form-group">
              <label class="form-label">反馈类型</label>
              <select v-model="feedbackForm.type" class="form-select">
                <option value="suggestion">功能建议</option>
                <option value="bug">问题反馈</option>
                <option value="other">其他</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">反馈内容</label>
              <textarea 
                v-model="feedbackForm.content" 
                placeholder="请输入您的反馈内容..."
                class="form-textarea"
                rows="6"
              ></textarea>
            </div>
            <div class="form-actions">
              <button 
                type="submit" 
                class="submit-button"
                :disabled="!feedbackForm.content"
              >
                提交反馈
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
  <!-- 查看详情模态框 -->
  <div v-if="showDetailsModal" class="modal-overlay">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>评语详情</h3>
        <button @click="closeDetailsModal" class="modal-close">×</button>
      </div>
      <div class="modal-body">
        <div class="column-info">
          <h4>{{ selectedCommentColumn }}</h4>
          <p>生成时间: {{ formatDate(selectedComment.createdAt) }}</p>
        </div>
        <!-- 只有当有实际图片时才显示图片容器 -->
        <div v-if="selectedColumnImages && selectedColumnImages.length > 0" class="images-container">
          <!-- 只显示实际有效的图片，排除包含'无'的情况 -->
          <div 
            v-for="(image, index) in selectedColumnImages.filter(img => 
              img && 
              typeof img === 'string' && 
              img.trim() !== '' &&
              !img.includes('无') &&
              !img.includes('null') &&
              !img.includes('undefined')
            )" 
            :key="index" 
            class="image-item"
          >
            <img :src="image" :alt="`试题图片 ${index + 1}`" class="column-image">
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import KnowledgeGraph from '../components/KnowledgeGraph.vue'
import ResourcePanel from '../components/ResourcePanel.vue'
import { getStudentById } from '../api/students'
import { getStudentComments } from '../api/comments'
import { getColumns } from '../api/columns'
import { submitFeedback as apiSubmitFeedback } from '../api/comments'
import { generateSummaryComment } from '../api/comments'
import { createConversation, getConversations, getConversationMessages, askQuestion, renameConversation, deleteConversation } from '../api/qa'

// 路由和状态管理
const router = useRouter()
const authStore = useAuthStore()

// 组件状态
const activeSection = ref('knowledge-graph')
const feedbackForm = ref({
  type: 'suggestion',
  content: ''
})
const commentFeedback = ref({})

// 数据
const columns = ref([])
const myComments = ref([])
const studentProfile = ref({
  studentId: '',
  className: ''
})
const summaryComment = ref(null)
const isGeneratingSummary = ref(false)
// 跟踪每个评语的反馈编辑状态
const editingFeedback = ref({})

// 查看详情模态框相关变量
const showDetailsModal = ref(false)
const selectedComment = ref(null)
const selectedCommentColumn = ref('')
const selectedColumnImages = ref([])

// 智能问答相关变量
const conversations = ref([])
const currentConversationId = ref(null)
const chatHistory = ref([])
const inputMessage = ref('')
const isLoading = ref(false)

// 会话管理相关变量
const isRenaming = ref(false)
const editingConversationId = ref(null)
const editConversationName = ref('')

// 当前用户信息
const currentUser = computed(() => authStore.user)

// 辅助函数
const getColumnById = (id) => {
  return columns.value.find(column => column.id === id)
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

// 切换显示区域
const showSection = (section) => {
  console.log('切换到区域:', section)
  activeSection.value = section
  
  // 当切换到我的评语区域时，重新加载评语数据以确保反馈状态正确
  if (section === 'my-comments') {
    loadMyComments()
  }
}

// 退出登录
const logout = () => {
  console.log('退出登录')
  authStore.logout()
  router.push('/login')
}

// 加载学生评语
const loadMyComments = async () => {
  if (!currentUser.value || !currentUser.value.id) return
  
  try {
    const comments = await getStudentComments(currentUser.value.id)
    myComments.value = comments
    
    // 初始化反馈表单
    comments.forEach(comment => {
      // 检查feedback是否存在或为空，而不是依赖hasFeedback字段
      if (!comment.feedback || comment.feedback.trim() === '') {
        commentFeedback.value[comment.id] = ''
        // 确保hasFeedback字段正确
        comment.hasFeedback = false
      } else {
        // 确保hasFeedback字段正确
        comment.hasFeedback = true
      }
    })
  } catch (error) {
    console.error('获取评语失败:', error)
  }
}

// 加载学生资料
const loadStudentProfile = async () => {
  if (!currentUser.value || !currentUser.value.id) return
  
  try {
    const student = await getStudentById(currentUser.value.id)
    if (student) {
      studentProfile.value = {
        studentId: student.studentId,
        className: student.className
      }
    }
  } catch (error) {
    console.error('获取学生资料失败:', error)
  }
}

// 加载专栏数据
const loadColumns = async () => {
  try {
    const data = await getColumns()
    columns.value = data
  } catch (error) {
    console.error('获取专栏失败:', error)
  }
}

// 生成总评
const generateSummary = async () => {
  if (!currentUser.value || !currentUser.value.id) return
  
  isGeneratingSummary.value = true
  
  try {
    const result = await generateSummaryComment(currentUser.value.id)
    if (result) {
      summaryComment.value = result
      alert('总评生成成功！')
    }
  } catch (error) {
    console.error('生成总评失败:', error)
    alert('生成总评失败，请重试')
  } finally {
    isGeneratingSummary.value = false
  }
}

// 提交评语反馈
const submitFeedback = async (commentId) => {
  if (!commentFeedback.value[commentId]) return
  
  try {
    const result = await apiSubmitFeedback(commentId, commentFeedback.value[commentId])
    if (result) {
      // 更新本地评语状态
      const comment = myComments.value.find(c => c.id === commentId)
      if (comment) {
        comment.hasFeedback = true
        comment.feedback = commentFeedback.value[commentId]
      }
      
      // 清空反馈表单
      delete commentFeedback.value[commentId]
      
      alert('反馈提交成功！')
    }
  } catch (error) {
    console.error('提交反馈失败:', error)
  }
}

// 开始编辑反馈
const startEditFeedback = (commentId) => {
  const comment = myComments.value.find(c => c.id === commentId)
  if (comment) {
    // 将当前反馈内容加载到编辑表单
    commentFeedback.value[commentId] = comment.feedback
    editingFeedback.value[commentId] = true
  }
}

// 更新反馈
const updateFeedback = async (commentId) => {
  if (!commentFeedback.value[commentId]) return
  
  try {
    const result = await apiSubmitFeedback(commentId, commentFeedback.value[commentId])
    if (result) {
      // 更新本地评语状态
      const comment = myComments.value.find(c => c.id === commentId)
      if (comment) {
        comment.feedback = commentFeedback.value[commentId]
      }
      
      // 退出编辑状态
      editingFeedback.value[commentId] = false
      delete commentFeedback.value[commentId]
      
      alert('反馈修改成功！')
    }
  } catch (error) {
    console.error('修改反馈失败:', error)
  }
}

// 取消编辑反馈
const cancelEditFeedback = (commentId) => {
  editingFeedback.value[commentId] = false
  delete commentFeedback.value[commentId]
}

// 显示评语详情
const  showCommentDetails = (comment) => {
  selectedComment.value = comment
  const column = getColumnById(comment.columnId)
  selectedCommentColumn.value = column?.name || '未知专栏'
  
  // 提取评语的所有图片
  selectedColumnImages.value = []
  if (comment) {
    // 查找所有图片路径字段（最多6张）
    for (let i = 1; i <= 6; i++) {
      const imagePath = comment[`answerImagePath${i}`]
      // 确保图片路径存在、是字符串类型、不是空字符串、不是'null'、'undefined'或'无'
      if (
        imagePath !== null && 
        imagePath !== undefined && 
        typeof imagePath === 'string' && 
        imagePath.trim() !== '' &&
        imagePath.toLowerCase() !== 'null' &&
        imagePath.toLowerCase() !== 'undefined' &&
        imagePath.toLowerCase() !== '无'
      ) {
        // 确保图片路径是完整的URL，添加缺少的斜杠
        const imageUrl = imagePath.startsWith('http') ? imagePath : `http://localhost:5000/${imagePath}`
        selectedColumnImages.value.push(imageUrl)
      }
    }
  }
  // 确保数组是安全的
  if (!selectedColumnImages.value) {
    selectedColumnImages.value = []
  }
  
  showDetailsModal.value = true
}

// 关闭详情模态框
const closeDetailsModal = () => {
  showDetailsModal.value = false
  selectedComment.value = null
  selectedCommentColumn.value = ''
  selectedColumnImages.value = []
}

// 提交反馈表单
const submitFeedbackForm = async () => {
  if (!feedbackForm.value.content) return
  
  try {
    // 这里可以添加实际的反馈提交逻辑
    // 暂时使用模拟数据
    console.log('提交反馈:', feedbackForm.value)
    feedbackForm.value = {
      type: 'suggestion',
      content: ''
    }
    alert('反馈提交成功！感谢您的建议。')
  } catch (error) {
    console.error('提交反馈失败:', error)
  }
}

// 智能问答相关函数
// 创建新会话
const createNewConversation = async () => {
  try {
    const response = await createConversation(currentUser.value.id)
    if (response.success) {
      currentConversationId.value = response.conversation_id
      chatHistory.value = []
      await loadConversations()
    }
  } catch (error) {
    console.error('创建会话失败:', error)
  }
}

// 选择会话
const selectConversation = async (conversationId) => {
  currentConversationId.value = conversationId
  await loadConversationMessages(conversationId)
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  isLoading.value = true
  const question = inputMessage.value.trim()
  inputMessage.value = ''
  
  try {
    const response = await askQuestion(question, currentUser.value.id, currentConversationId.value)
    if (response.success) {
      // 更新会话ID（如果是新会话）
      if (!currentConversationId.value) {
        currentConversationId.value = response.conversation_id
      }
      
      // 更新聊天历史
      chatHistory.value.push(...response.messages)
      
      // 重新加载会话列表
      await loadConversations()
    }
  } catch (error) {
    console.error('发送消息失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 加载会话列表
const loadConversations = async () => {
  try {
    const response = await getConversations(currentUser.value.id)
    if (response.success) {
      conversations.value = response.conversations
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

// 加载会话消息
const loadConversationMessages = async (conversationId) => {
  try {
    const response = await getConversationMessages(conversationId)
    if (response.success) {
      chatHistory.value = response.messages
    }
  } catch (error) {
    console.error('加载会话消息失败:', error)
  }
}

// 开始重命名会话
const startRenameConversation = (conversationId, currentName) => {
  editingConversationId.value = conversationId
  editConversationName.value = currentName
  isRenaming.value = true
}

// 完成重命名会话
const finishRenameConversation = async () => {
  if (!editConversationName.value.trim() || !editingConversationId.value) return
  
  try {
    const response = await renameConversation(
      editingConversationId.value,
      editConversationName.value.trim(),
      currentUser.value.id
    )
    
    if (response.success) {
      // 更新会话列表
      await loadConversations()
    }
  } catch (error) {
    console.error('重命名会话失败:', error)
  } finally {
    cancelRenameConversation()
  }
}

// 取消重命名会话
const cancelRenameConversation = () => {
  isRenaming.value = false
  editingConversationId.value = null
  editConversationName.value = ''
}

// 删除会话
const removeConversation = async (conversationId) => {
  if (!confirm('确定要删除这个会话吗？')) return
  
  try {
    const response = await deleteConversation(conversationId)
    if (response.success) {
      // 更新会话列表
      await loadConversations()
      
      // 如果删除的是当前会话，选择第一个会话或创建新会话
      if (currentConversationId.value === conversationId) {
        if (conversations.value.length > 0) {
          currentConversationId.value = conversations.value[0].id
          await loadConversationMessages(conversations.value[0].id)
        } else {
          await createNewConversation()
        }
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error)
  }
}

// 初始化
onMounted(async () => {
  loadMyComments()
  loadStudentProfile()
  loadColumns()
  
  // 智能问答初始化
  if (currentUser.value) {
    await loadConversations()
    
    // 如果有会话，选择第一个
    if (conversations.value.length > 0) {
      currentConversationId.value = conversations.value[0].id
      await loadConversationMessages(conversations.value[0].id)
    } else {
      // 创建新会话
      await createNewConversation()
    }
  }
})
</script>

<style scoped>
.dashboard-container {
  display: grid;
  grid-template-columns: 250px 1fr;
  grid-template-rows: 60px 1fr;
  grid-template-areas: 
    "header header"
    "sidebar main";
  height: 100vh;
  overflow: hidden;
}

/* 顶部导航栏样式 */
.top-navigation {
  grid-area: header;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 15;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 32px;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.logout-button {
  background: #ff6b6b;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.logout-button:hover {
  background: #ee5a52;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.logout-icon {
  font-size: 14px;
}

/* 侧边导航栏样式 */
.side-navigation {
  grid-area: sidebar;
  background: #333;
  color: white;
  display: flex;
  flex-direction: column;
  padding: 20px 0;
  overflow-y: auto;
  z-index: 10;
  position: relative;
}

.nav-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #999;
  padding: 0 20px;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.nav-items {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  border-left: 4px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  border-left-color: #667eea;
  font-weight: 600;
}

.nav-icon {
  font-size: 18px;
}

.nav-text {
  flex: 1;
}

/* 主内容区域样式 */
.main-content {
  grid-area: main;
  background: #f5f7fa;
  overflow-y: auto;
  padding: 20px;
  z-index: 5;
  position: relative;
  overflow-x: hidden;
}

.section-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.section-header {
  margin-bottom: 24px;
}

.section-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #333;
}

.section-description {
  margin: 0;
  font-size: 14px;
  color: #666;
}

/* 评语列表样式 */
.comments-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.generate-summary-button {
  background: #4ecdc4;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.generate-summary-button:hover {
  background: #45b7aa;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(78, 205, 196, 0.3);
}

.generate-summary-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 智能问答容器样式 */
.smart-qa-container {
  display: flex;
  width: 100%;
  min-height: 700px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* 会话列表样式 */
.conversation-list {
  width: 240px;
  border-right: 1px solid #eee;
  overflow-y: auto;
  background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.03);
}

/* 会话操作按钮样式 */
.conversation-actions {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .conversation-actions {
  opacity: 1;
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  margin-left: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.rename-btn:hover {
  background-color: rgba(34, 139, 34, 0.1);
}

.delete-btn:hover {
  background-color: rgba(220, 53, 69, 0.1);
}

/* 重命名输入框样式 */
.rename-input-container {
  margin-bottom: 5px;
}

.rename-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #667eea;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

/* 会话项样式调整 */
.conversation-item {
  position: relative;
  padding: 14px 18px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
  transition: all 0.3s ease;
  background-color: rgba(255, 255, 255, 0.8);
}

.conversation-item:hover {
  background-color: #f0f4ff;
  transform: translateX(3px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.conversation-item.active {
  background-color: #e8f4ff;
  border-left: 4px solid #667eea;
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.15);
}

.conversation-title {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 600;
  font-size: 15px;
  color: #333;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.2s;
}

.conversation-item:hover .conversation-title {
  color: #667eea;
}

.conversation-preview {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.conversation-time {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 12px;
  color: #999;
  text-align: right;
  opacity: 0.7;
  transition: opacity 0.2s, color 0.2s;
}

.conversation-item:hover .conversation-time {
  opacity: 1;
  color: #667eea;
}

.new-conversation-btn {
  width: 100%;
  padding: 15px;
  background: none;
  border: none;
  cursor: pointer;
  border-top: 1px solid #eee;
  transition: background-color 0.2s;
  font-size: 14px;
}

.new-conversation-btn:hover {
  background-color: #f5f5f5;
}

/* 聊天界面样式 */
.chat-interface {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f8f9fa;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
}

/* 消息动画 */
.message {
  margin-bottom: 20px;
  max-width: 80%;
  min-width: 80px; /* 设置最小宽度，避免过于窄小 */
  opacity: 0;
  transform: translateY(10px);
  animation: messageFadeIn 0.3s ease forwards;
  word-wrap: break-word; /* 确保长单词能自动换行 */
  display: flex; /* 使用flex布局确保正确对齐 */
}

@keyframes messageFadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  justify-content: flex-end; /* 右对齐用户消息 */
  margin-left: auto; /* 将消息推到右侧 */
  animation-delay: 0.1s;
}

.message.assistant {
  justify-content: flex-start; /* 左对齐AI消息 */
  margin-right: auto; /* 将消息推到左侧 */
  animation-delay: 0.2s;
}

/* 调整消息内容容器 */
.message .message-content {
  max-width: 100%; /* 确保消息内容不会超过消息容器 */
}

.message-content {
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.message-content:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
}

.message.user .message-content {
  background-color: #667eea;
  color: #fff;
  border-bottom-right-radius: 5px;
}

.message.assistant .message-content {
  background-color: #fff;
  color: #333;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 5px;
}

/* 消息名称样式 */
.message-name {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
  font-weight: 500;
}

.message.user .message-name {
  color: rgba(255, 255, 255, 0.8);
}

.message.assistant .message-name {
  color: #667eea;
}

.message-content.loading {
  font-style: italic;
  color: #999;
  position: relative;
}

/* 输入状态指示器 */
.message-content.loading::after {
  content: '';
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-radius: 50%;
  border-top-color: #667eea;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 消息美化增强 */
.message-content {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  padding: 14px 18px;
  border-radius: 20px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
}

/* 用户消息美化 */
.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-bottom-right-radius: 6px;
}

/* AI消息美化 */
.message.assistant .message-content {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  color: #333;
  border: none;
  border-bottom-left-radius: 6px;
}

/* 输入区域样式 */
.input-area {
  padding: 20px;
  border-top: 1px solid #eee;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  align-items: flex-end;
  box-shadow: 0 -3px 15px rgba(0, 0, 0, 0.08);
  border-radius: 0 0 8px 8px;
}

.input-area textarea {
  flex: 1;
  min-height: 40px;
  max-height: 120px;
  padding: 14px 18px;
  border: none;
  border-radius: 25px;
  resize: none;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 15px;
  outline: none;
  transition: box-shadow 0.2s, transform 0.2s;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.input-area textarea:focus {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2), 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.input-area .send-btn {
  width: 80px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  margin-left: 12px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 15px;
  font-weight: 500;
  transition: box-shadow 0.2s, transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.input-area .send-btn:hover:not(:disabled) {
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.5);
  transform: translateY(-2px);
}

.input-area .send-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.input-area .send-btn:disabled {
  background: linear-gradient(135deg, #cccccc 0%, #999999 100%);
  cursor: not-allowed;
  opacity: 0.7;
  box-shadow: none;
}

/* 新会话按钮样式 */
.new-conversation-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  cursor: pointer;
  border-top: 1px solid #eee;
  transition: background-color 0.2s, transform 0.2s, box-shadow 0.2s;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 15px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.new-conversation-btn:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6b479a 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.new-conversation-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar,
.conversation-list::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track,
.conversation-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb,
.conversation-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover,
.conversation-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 智能问答容器阴影效果 */
.smart-qa-container {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.3s;
}

.smart-qa-container:hover {
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.12);
}

/* 总结评语样式 */
.summary-comment-container {
  margin-top: 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.summary-comment-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 24px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.summary-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.summary-date {
  font-size: 14px;
  opacity: 0.8;
}

.summary-content {
  font-size: 16px;
  line-height: 1.8;
  opacity: 0.9;
}

.comment-card {
  background: #f5f7fa;
  border-radius: 12px;
  padding: 20px;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.comment-column {
  font-size: 18px;
  font-weight: 600;
  color: #667eea;
  margin: 0;
}

.comment-date {
  font-size: 14px;
  color: #999;
}

.comment-content {
  font-size: 16px;
  color: #333;
  line-height: 1.8;
  margin-bottom: 20px;
  padding: 15px;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* 反馈区域样式 */
.comment-feedback-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.feedback-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.feedback-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 12px;
  font-family: inherit;
}

.feedback-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.submit-feedback-button {
  background: #667eea;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submit-feedback-button:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.submit-feedback-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 用户反馈内容样式 */
.user-feedback-content {
  font-size: 16px;
  color: #333;
  line-height: 1.8;
  margin-bottom: 15px;
  padding: 15px;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* 评语操作按钮 */
.comment-actions {
  margin: 15px 0;
}

.view-details-button {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.view-details-button:hover {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
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
  font-size: 20px;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.modal-close:hover {
  background: #f5f7fa;
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  max-height: calc(90vh - 70px);
}

.column-info {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.column-info h4 {
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #667eea;
}

.column-info p {
  margin: 0;
  font-size: 14px;
  color: #999;
}

.images-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-top: 20px;
}

.image-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease;
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.column-image {
  width: 100%;
  height: auto;
  display: block;
}

.no-images {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.no-images-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-images p {
  font-size: 16px;
  margin: 0;
}

/* 反馈按钮容器样式 */
.feedback-buttons {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

/* 个人资料样式 */
.profile-container {
  display: flex;
  justify-content: center;
}

.profile-info {
  display: flex;
  gap: 32px;
  align-items: center;
  max-width: 600px;
  width: 100%;
}

.profile-avatar {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  font-size: 64px;
}

.profile-details {
  flex: 1;
}

.profile-item {
  display: flex;
  margin-bottom: 16px;
  align-items: center;
}

.profile-label {
  width: 80px;
  font-size: 16px;
  font-weight: 500;
  color: #666;
}

.profile-value {
  font-size: 16px;
  color: #333;
  font-weight: 500;
}

/* 反馈表单样式 */
.feedback-form-container {
  max-width: 600px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.form-select {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
}

.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.submit-button {
  background: #667eea;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submit-button:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.submit-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 无数据样式 */
.no-comments {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.no-comments-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-comments h3 {
  font-size: 24px;
  margin: 0 0 8px 0;
  color: #666;
}

.no-comments p {
  font-size: 16px;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-container {
    grid-template-columns: 1fr;
    grid-template-rows: 60px 1fr;
    grid-template-areas: 
      "header"
      "main";
  }

  .side-navigation {
    display: none;
  }

  .top-navigation {
    padding: 0 10px;
  }

  .logo-text {
    font-size: 16px;
  }

  .user-name {
    display: none;
  }

  .main-content {
    padding: 10px;
  }

  .section-container {
    padding: 15px;
  }

  .profile-info {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .profile-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .profile-label {
    width: 100%;
    margin-bottom: 4px;
  }
}
</style>
