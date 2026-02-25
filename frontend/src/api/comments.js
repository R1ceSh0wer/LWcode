import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

// 获取学生评语列表
export const getStudentComments = async (studentId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/comments?studentId=${studentId}`)
    return response.data
  } catch (error) {
    console.error(`获取学生${studentId}评语列表失败:`, error)
    return []
  }
}

// 获取单个评语
export const getCommentById = async (id) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/comments/${id}`)
    return response.data
  } catch (error) {
    console.error(`获取评语${id}信息失败:`, error)
    return null
  }
}

// 生成评语
export const generateComment = async (commentData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/comments/generate`, commentData)
    return response.data
  } catch (error) {
    console.error('生成评语失败:', error)
    return null
  }
}

// 生成总结评语
export const generateSummaryComment = async (studentId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/comments/summary/${studentId}`)
    return response.data
  } catch (error) {
    console.error(`生成学生${studentId}总结评语失败:`, error)
    return null
  }
}

// 获取学生总结评语
export const getSummaryComment = async (studentId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/comments/summary/${studentId}`)
    return response.data
  } catch (error) {
    console.error(`获取学生${studentId}总结评语失败:`, error)
    return null
  }
}

// 创建评语记录
export const createComment = async (commentData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/comments`, commentData)
    return response.data
  } catch (error) {
    console.error('创建评语记录失败:', error)
    return null
  }
}

// 提交学生反馈
export const submitFeedback = async (commentId, feedback) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/comments/${commentId}/feedback`, { feedback })
    return response.data
  } catch (error) {
    console.error(`提交评语${commentId}反馈失败:`, error)
    return null
  }
}

// 删除评语
export const deleteComment = async (commentId) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/comments/${commentId}`)
    return response.data
  } catch (error) {
    console.error(`删除评语${commentId}失败:`, error)
    return null
  }
}
