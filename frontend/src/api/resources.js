import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

// 获取资源列表
export const getResources = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/resources`)
    return response.data
  } catch (error) {
    console.error('获取资源列表失败:', error)
    return []
  }
}

// 获取单个资源信息
export const getResourceById = async (id) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/resources/${id}`)
    return response.data
  } catch (error) {
    console.error(`获取资源${id}信息失败:`, error)
    return null
  }
}

// 下载资源
export const downloadResource = async (id) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/resources/${id}/download`, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `resource_${id}.${response.headers['content-type'].split('/')[1]}`)
    document.body.appendChild(link)
    link.click()
    
    // 清理
    window.URL.revokeObjectURL(url)
    document.body.removeChild(link)
    
    return true
  } catch (error) {
    console.error(`下载资源${id}失败:`, error)
    return false
  }
}

// 预览资源
export const previewResource = async (id) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/resources/${id}/preview`)
    return response.data
  } catch (error) {
    console.error(`预览资源${id}失败:`, error)
    return null
  }
}

// 上传资源
export const uploadResource = async (formData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/resources/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  } catch (error) {
    console.error('上传资源失败:', error)
    return null
  }
}

// 删除资源
export const deleteResource = async (id) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/resources/${id}`)
    return response.data
  } catch (error) {
    console.error(`删除资源${id}失败:`, error)
    return null
  }
}
