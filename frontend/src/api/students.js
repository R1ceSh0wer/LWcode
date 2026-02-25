import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

// 获取学生列表
export const getStudents = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/students`)
    return response.data
  } catch (error) {
    console.error('获取学生列表失败:', error)
    return []
  }
}

// 获取单个学生信息
export const getStudentById = async (id) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/students/${id}`)
    return response.data
  } catch (error) {
    console.error(`获取学生${id}信息失败:`, error)
    return null
  }
}

// 更新学生信息
export const updateStudent = async (id, studentData) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/students/${id}`, studentData)
    return response.data
  } catch (error) {
    console.error(`更新学生${id}信息失败:`, error)
    return null
  }
}

// 添加学生
export const addStudent = async (studentData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/students`, studentData)
    return response.data
  } catch (error) {
    console.error('添加学生失败:', error)
    return null
  }
}

// 删除学生
export const deleteStudent = async (id) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/students/${id}`)
    return response.data
  } catch (error) {
    console.error(`删除学生${id}失败:`, error)
    return null
  }
}
