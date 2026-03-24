import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

export const getColumnKnowledgeGraph = async (columnId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/columns/${columnId}/knowledge-graph`)
    return response.data
  } catch (error) {
    console.error('获取教师知识图谱失败:', error)
    return { success: false, data: null, message: '获取教师知识图谱失败' }
  }
}

export const saveColumnKnowledgeGraph = async (columnId, payload) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/columns/${columnId}/knowledge-graph`, payload)
    return response.data
  } catch (error) {
    console.error('保存教师知识图谱失败:', error)
    return { success: false, message: '保存教师知识图谱失败' }
  }
}
