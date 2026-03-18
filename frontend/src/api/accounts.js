import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

// 获取账号列表
export const getAccounts = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/accounts`)
    return response.data
  } catch (error) {
    console.error('获取账号列表失败:', error)
    return { success: false, data: [], message: '获取账号列表失败' }
  }
}

// 添加账号
export const addAccount = async (accountData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/accounts`, accountData)
    return response.data
  } catch (error) {
    console.error('添加账号失败:', error)
    return { success: false, data: null, message: '添加账号失败' }
  }
}

// 删除账号
export const deleteAccount = async (id) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/accounts/${id}`)
    return response.data
  } catch (error) {
    console.error(`删除账号${id}失败:`, error)
    return { success: false, data: null, message: '删除账号失败' }
  }
}

// 更新账号
export const updateAccount = async (accountData) => {
  try {
    const { id, ...data } = accountData
    const response = await axios.put(`${API_BASE_URL}/accounts/${id}`, data)
    return response.data
  } catch (error) {
    console.error(`更新账号${accountData.id}失败:`, error)
    return { success: false, data: null, message: '更新账号失败' }
  }
}

// 批量添加账号
export const batchAddAccounts = async (formData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/accounts/batch`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  } catch (error) {
    console.error('批量添加账号失败:', error)
    return { success: false, data: null, message: '批量添加账号失败' }
  }
}
