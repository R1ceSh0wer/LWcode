import axios from 'axios'

// 创建axios实例
const imageApi = axios.create({
  baseURL: '/api',
  timeout: 30000, // 上传可能需要较长时间，设置30秒超时
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})

// 请求拦截器
imageApi.interceptors.request.use(
  config => {
    // 从本地存储获取token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
imageApi.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('图片API请求错误:', error)
    return Promise.reject(error)
  }
)

// API函数

/**
 * 上传图片
 * @param {FormData} formData - 包含图片文件的表单数据
 * @returns {Promise} - 上传结果
 */
export const uploadImage = async (formData) => {
  try {
    return await imageApi.post('/upload', formData, {
      onUploadProgress: progressEvent => {
        // 可以在这里处理上传进度
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        console.log('上传进度:', percentCompleted)
      }
    })
  } catch (error) {
    console.error('上传图片失败:', error)
    throw error
  }
}

/**
 * 获取所有已上传图片
 * @returns {Promise} - 图片列表
 */
export const getUploadedImages = async () => {
  try {
    return await imageApi.get('/images')
  } catch (error) {
    console.error('获取图片列表失败:', error)
    throw error
  }
}

/**
 * 获取单张图片详情
 * @param {string} id - 图片ID
 * @returns {Promise} - 图片详情
 */
export const getImageById = async (id) => {
  try {
    return await imageApi.get(`/images/${id}`)
  } catch (error) {
    console.error('获取图片详情失败:', error)
    throw error
  }
}

/**
 * 删除图片
 * @param {string} id - 图片ID
 * @returns {Promise} - 删除结果
 */
export const deleteImage = async (id) => {
  try {
    return await imageApi.delete(`/images/${id}`)
  } catch (error) {
    console.error('删除图片失败:', error)
    throw error
  }
}

/**
 * 批量删除图片
 * @param {Array} ids - 图片ID数组
 * @returns {Promise} - 删除结果
 */
export const deleteImagesBatch = async (ids) => {
  try {
    return await imageApi.delete('/images/batch', { data: { ids } })
  } catch (error) {
    console.error('批量删除图片失败:', error)
    throw error
  }
}

/**
 * 更新图片信息
 * @param {string} id - 图片ID
 * @param {Object} data - 更新数据
 * @returns {Promise} - 更新结果
 */
export const updateImage = async (id, data) => {
  try {
    return await imageApi.put(`/images/${id}`, data)
  } catch (error) {
    console.error('更新图片信息失败:', error)
    throw error
  }
}

/**
 * 获取图片统计信息
 * @returns {Promise} - 统计信息
 */
export const getImageStats = async () => {
  try {
    return await imageApi.get('/images/stats')
  } catch (error) {
    console.error('获取图片统计信息失败:', error)
    throw error
  }
}
