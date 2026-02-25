import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 10000
})

// 获取知识图谱数据
export const getKnowledgeGraph = async () => {
  try {
    const response = await api.get('/knowledge-graph')
    return response.data
  } catch (error) {
    console.error('Error fetching knowledge graph:', error)
    throw error
  }
}
