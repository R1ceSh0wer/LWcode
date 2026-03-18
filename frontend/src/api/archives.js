import axios from 'axios'

const API_BASE = 'http://localhost:5000/api/archives'

/**
 * 获取所有存档
 */
export function getArchives(teacherId) {
  return axios
    .get(API_BASE, { params: { teacher_id: teacherId } })
    .then(r => r.data)
    .catch(() => ({ success: false, data: [], message: '获取存档失败' }))
}

/**
 * 创建新存档
 */
export function createArchive(name, teacherId) {
  const formData = new FormData()
  formData.append('name', name)
  formData.append('teacher_id', String(teacherId))
  return axios
    .post(API_BASE, formData)
    .then(r => r.data)
    .catch(() => ({ success: false, data: null, message: '创建存档失败' }))
}

/**
 * 创建存档并上传文件（支持两种模式：选择已有模型或上传训练文件）
 */
export function createArchiveWithFiles(formData) {
  return axios
    .post(`${API_BASE}/create-with-files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    .then(r => r.data)
    .catch(() => ({ success: false, data: null, message: '创建存档失败' }))
}

/**
 * 上传存档文件并开始训练
 */
export function uploadArchiveFiles(archiveId, formData) {
  return axios
    .post(`${API_BASE}/${archiveId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    .then(r => r.data)
    .catch(() => ({ success: false, data: null, message: '上传训练文件失败' }))
}

/**
 * 获取存档详情
 */
export function getArchiveDetail(archiveId) {
  return axios
    .get(`${API_BASE}/${archiveId}`)
    .then(r => r.data)
    .catch(() => ({ success: false, data: null, message: '获取存档详情失败' }))
}

/**
 * 删除存档
 */
export function deleteArchive(archiveId) {
  return axios
    .delete(`${API_BASE}/${archiveId}`)
    .then(r => r.data)
    .catch(() => ({ success: false, data: null, message: '删除存档失败' }))
}
