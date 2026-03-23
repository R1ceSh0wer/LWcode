import axios from 'axios'

const API_BASE = 'http://localhost:5000/api/resources'

/**
 * 获取教师的学习资源列表
 * @param {number|string} teacherId
 * @returns {Promise<Object>}
 */
export function getTeacherResources(teacherId) {
  return axios
    .get(API_BASE, { params: { teacher_id: teacherId } })
    .then((response) => response.data)
    .catch((error) => {
      console.error('获取教师学习资源列表失败:', error)
      return {
        success: false,
        data: [],
        message: error.response?.data?.message || '获取教师学习资源列表失败',
      }
    })
}

/**
 * 创建学习资源（multipart）
 * @param {FormData} formData - 需包含 name, type, file, teacher_id
 */
export function createResource(formData) {
  return axios
    .post(API_BASE, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((response) => response.data)
    .catch((error) => {
      console.error('创建学习资源失败:', error)
      return {
        success: false,
        message: error.response?.data?.message || '创建学习资源失败',
      }
    })
}

/**
 * 更新学习资源
 * @param {number} resourceId
 * @param {FormData} formData - name, type, file(可选), teacher_id
 */
export function updateResource(resourceId, formData) {
  return axios
    .put(`${API_BASE}/${resourceId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((response) => response.data)
    .catch((error) => {
      console.error('更新学习资源失败:', error)
      return {
        success: false,
        message: error.response?.data?.message || '更新学习资源失败',
      }
    })
}

/**
 * 删除学习资源
 * @param {number} resourceId
 * @param {number|string} teacherId
 */
export function deleteResource(resourceId, teacherId) {
  return axios
    .delete(`${API_BASE}/${resourceId}`, { params: { teacher_id: teacherId } })
    .then((response) => response.data)
    .catch((error) => {
      console.error('删除学习资源失败:', error)
      return {
        success: false,
        message: error.response?.data?.message || '删除学习资源失败',
      }
    })
}

/**
 * 发放学习资源给学生
 * @param {number} resourceId
 * @param {number|string} teacherId
 * @param {Array<number|string>} studentIds
 */
export function distributeResource(resourceId, teacherId, studentIds) {
  return axios
    .post(`${API_BASE}/${resourceId}/distribute`, {
      teacher_id: Number(teacherId),
      student_ids: studentIds.map((id) => Number(id)),
    })
    .then((response) => response.data)
    .catch((error) => {
      console.error('发放学习资源失败:', error)
      return {
        success: false,
        message: error.response?.data?.message || '发放学习资源失败',
      }
    })
}

/**
 * 获取学生收到的学习资源列表
 * @param {number|string} studentId
 * @param {string} type - 资源类型，空或 all 表示全部
 * @param {string} search - 搜索关键词
 */
export function getStudentResources(studentId, type = '', search = '') {
  const params = { student_id: studentId }
  if (type && type !== 'all') params.type = type
  if (search) params.search = search
  return axios
    .get(`${API_BASE}/student`, { params })
    .then((response) => response.data)
    .catch((error) => {
      console.error('获取学生学习资源失败:', error)
      return {
        success: false,
        data: [],
        message: error.response?.data?.message || '获取学生学习资源失败',
      }
    })
}
