import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'

// 获取专栏列表
export const getColumns = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/columns`)
    return response.data
  } catch (error) {
    console.error('获取专栏列表失败:', error)
    return []
  }
}

// 获取单个专栏信息
export const getColumnById = async (id) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/columns/${id}`)
    return response.data
  } catch (error) {
    console.error(`获取专栏${id}信息失败:`, error)
    return null
  }
}

// 更新专栏信息
export const updateColumn = async (id, columnData) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/columns/${id}`, columnData)
    return response.data
  } catch (error) {
    console.error(`更新专栏${id}信息失败:`, error)
    return null
  }
}

// 添加专栏
export const addColumn = async (columnData) => {
  try {
    // 检查是否有图片文件需要上传
    const hasFiles = columnData.imageFiles && columnData.imageFiles.length > 0;
    
    if (hasFiles) {
      // 创建FormData对象
      const formData = new FormData();
      
      // 添加普通字段
      formData.append('name', columnData.name);
      formData.append('teacherId', columnData.teacherId || 1);
      
      // 添加图片文件
      columnData.imageFiles.forEach((file, index) => {
        formData.append(`image${index + 1}`, file);
      });
      
      // 发送FormData请求
      const response = await axios.post(`${API_BASE_URL}/columns`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return response.data;
    } else {
      // 如果没有图片，发送普通JSON请求
      const response = await axios.post(`${API_BASE_URL}/columns`, columnData);
      return response.data;
    }
  } catch (error) {
    console.error('添加专栏失败:', error);
    return null;
  }
}

// 删除专栏
export const deleteColumn = async (id) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/columns/${id}`)
    return response.data
  } catch (error) {
    console.error(`删除专栏${id}失败:`, error)
    return null
  }
}
