import axios from 'axios'

const API_BASE = 'http://localhost:5000/api/archives'

/**
 * 获取所有存档
 */
export function getArchives(teacherId) {
  return axios.get(API_BASE, {
    params: { teacher_id: teacherId }
  })
}

/**
 * 创建新存档
 */
export function createArchive(name, teacherId) {
  return axios.post(API_BASE, null, {
    params: { name, teacher_id: teacherId }
  })
}

/**
 * 创建存档并上传文件（支持两种模式：选择已有模型或上传训练文件）
 */
export function createArchiveWithFiles(formData) {
  return axios.post(`${API_BASE}/create-with-files`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 上传存档文件并开始训练
 */
export function uploadArchiveFiles(archiveId, formData) {
  return axios.post(`${API_BASE}/${archiveId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取存档详情
 */
export function getArchiveDetail(archiveId) {
  return axios.get(`${API_BASE}/${archiveId}`)
}

/**
 * 删除存档
 */
export function deleteArchive(archiveId) {
  return axios.delete(`${API_BASE}/${archiveId}`)
}
