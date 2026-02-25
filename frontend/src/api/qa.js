import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

// 创建会话
export const createConversation = async (studentId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/qa/conversations`, {
      student_id: studentId
    })
    return response.data
  } catch (error) {
    console.error('创建会话失败:', error)
    throw error
  }
}

// 获取会话列表
export const getConversations = async (studentId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/qa/conversations/${studentId}`)
    return response.data
  } catch (error) {
    console.error('获取会话列表失败:', error)
    throw error
  }
}

// 获取会话消息
export const getConversationMessages = async (conversationId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/qa/conversations/${conversationId}/messages`)
    return response.data
  } catch (error) {
    console.error('获取会话消息失败:', error)
    throw error
  }
}

// 发送问题
export const askQuestion = async (question, studentId, conversationId = null) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/qa/ask`, {
      question,
      student_id: studentId,
      conversation_id: conversationId
    })
    return response.data
  } catch (error) {
    console.error('发送问题失败:', error)
    throw error
  }
}

// 删除会话
export const deleteConversation = async (conversationId) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/qa/conversations/${conversationId}`)
    return response.data
  } catch (error) {
    console.error('删除会话失败:', error)
    throw error
  }
}

// 重命名会话
export const renameConversation = async (conversationId, name, studentId, autoGenerate = false) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/qa/conversations/${conversationId}/name`, {
      name,
      auto_generate: autoGenerate,
      student_id: studentId
    })
    return response.data
  } catch (error) {
    console.error('重命名会话失败:', error)
    throw error
  }
}