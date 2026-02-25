<template>
  <div class="image-upload-container">
    <div class="upload-header">
      <h2>图片上传</h2>
      <div class="upload-stats">
        <span>{{ previewImages.length }} / {{ maxImages }} 张已选择</span>
      </div>
    </div>
    
    <div v-if="studentId" class="upload-tip">
      <span class="tip-icon">💡</span>
      <span class="tip-text">请在答错题目的题号上画圈</span>
    </div>

    <div class="upload-area" @dragover.prevent="handleDragOver" @drop.prevent="handleDrop">
      <input 
        ref="fileInput" 
        type="file" 
        accept="image/*" 
        multiple 
        class="file-input"
        @change="handleFileChange"
      >
      <div class="upload-content">
        <div class="upload-icon">📸</div>
        <h3>拖拽图片到这里，或</h3>
        <button @click="openFileDialog" class="browse-button">
          <i class="browse-icon">📂</i> 浏览文件
        </button>
        <p class="upload-hint">支持 JPG, PNG, GIF 格式，单张不超过 5MB</p>
      </div>
    </div>

    <div v-if="previewImages.length > 0" class="image-preview-section">
      <h3 class="preview-title">图片预览</h3>
      <div class="image-grid">
        <div 
          v-for="(image, index) in previewImages" 
          :key="index"
          class="preview-item"
        >
          <div class="preview-container">
            <img :src="image.url" alt="Preview" class="preview-image">
            <button @click="removePreviewImage(index)" class="remove-button">
              <i class="remove-icon">×</i>
            </button>
          </div>
          <div class="image-info">
            <span class="image-name">{{ image.name }}</span>
            <span class="image-size">{{ formatFileSize(image.size) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="upload-actions">
      <button @click="clearAll" class="clear-button" :disabled="previewImages.length === 0">
        清空预览
      </button>
    </div>

    <!-- 上传进度条 -->
    <div v-if="isUploading" class="upload-progress">
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: uploadProgress + '%' }"
        ></div>
      </div>
      <div class="progress-text">
        上传进度: {{ uploadProgress }}%
      </div>
    </div>


  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { uploadImage, getUploadedImages } from '../api/images'
import { createComment, generateComment } from '../api/comments'

// 定义组件接收的props
const props = defineProps({
  studentId: {
    type: String,
    required: false
  },
  columnId: {
    type: String,
    required: false
  }
})

// 组件配置
const maxImages = 6
const maxFileSize = 5 * 1024 * 1024 // 5MB

// 组件状态
const isUploading = ref(false)
const uploadProgress = ref(0)
const previewImages = ref([])
const uploadedImages = ref([])
const fileInput = ref(null)

// 辅助函数
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 文件选择处理
const openFileDialog = () => {
  fileInput.value?.click()
}

const handleFileChange = (event) => {
  const files = Array.from(event.target.files)
  processFiles(files)
}

// 拖拽处理
const handleDragOver = (event) => {
  event.preventDefault()
}

const handleDrop = (event) => {
  event.preventDefault()
  const files = Array.from(event.dataTransfer.files)
  processFiles(files)
}

// 处理文件
const processFiles = (files) => {
  const remainingSlots = maxImages - previewImages.value.length
  if (remainingSlots <= 0) {
    alert(`最多只能上传 ${maxImages} 张图片`)
    return
  }

  const validFiles = files.filter(file => {
    // 检查文件类型
    if (!file.type.startsWith('image/')) {
      alert(`文件 ${file.name} 不是图片格式`)
      return false
    }
    
    // 检查文件大小
    if (file.size > maxFileSize) {
      alert(`文件 ${file.name} 超过 5MB 限制`)
      return false
    }
    
    return true
  })

  // 限制最多可上传数量
  const filesToAdd = validFiles.slice(0, remainingSlots)
  
  // 创建预览
  filesToAdd.forEach(file => {
    const reader = new FileReader()
    reader.onload = (e) => {
      previewImages.value.push({
        name: file.name,
        size: file.size,
        url: e.target.result,
        file: file
      })
    }
    reader.readAsDataURL(file)
  })
}

// 移除预览图片
const removePreviewImage = (index) => {
  previewImages.value.splice(index, 1)
}

// 清空所有预览图片
const clearAll = () => {
  previewImages.value = []
  uploadedImages.value = []
}

// 上传图片
const uploadImages = async (skipCreateComment = false) => {
  // 如果没有预览图片，直接返回
  if (previewImages.value.length === 0) return []
  
  try {
    isUploading.value = true
    uploadProgress.value = 0
    
    let uploadedCount = 0
    const uploadedResults = []
    const imagePaths = []
    
    // 只上传用户选择的新图片（带有file属性的图片）
    const newImages = previewImages.value.filter(image => image.file)
    
    for (const image of newImages) {
      const formData = new FormData()
      formData.append('file', image.file)
      
      const result = await uploadImage(formData)
      
      if (result && result.success) {
        if (result.fileUrl) {
          // 构建图片信息对象
          const uploadedImage = {
            name: result.filename,
            url: result.fileUrl
          };
          // 确保图片URL是完整的
          if (uploadedImage.url && !uploadedImage.url.startsWith('http')) {
            uploadedImage.url = `http://localhost:5000/${uploadedImage.url}`;
          }
          uploadedImages.value.push(uploadedImage)
          uploadedResults.push(uploadedImage)
          imagePaths.push(uploadedImage.url)
          uploadedCount++
        }
      }
    }
    
    // 清空预览
    previewImages.value = []
    
    // 处理评语记录的创建和更新
    if (props.studentId && props.columnId) {
      // 只有在没有跳过创建评语记录时才创建或更新评语记录
      if (!skipCreateComment) {
        // 准备要发送到后端的图片路径（去掉完整URL前缀，只保留相对路径）
        const relativeImagePaths = imagePaths.map(path => {
          if (path && path.startsWith('http://localhost:5000/')) {
            return path.replace('http://localhost:5000/', '');
          }
          return path;
        });
        
        // 调用generateComment来处理记录的创建和更新，它会自动检查是否存在对应记录
        const commentData = {
          studentId: props.studentId,
          columnId: props.columnId,
          style: 'encouraging',
          imagePaths: relativeImagePaths
        };
        await generateComment(commentData);
      }
    }
    
    // 返回本次新上传的图片路径
    const newImagesWithPaths = uploadedResults.map(image => ({
      ...image,
      path: image.url
    }))
    
    return newImagesWithPaths
  } catch (error) {
    console.error('处理图片失败:', error)
    alert('处理失败，请重试')
    throw error
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
  }
}



// 加载已上传图片
const loadUploadedImages = async () => {
  try {
    const images = await getUploadedImages()
    
    // 确保所有图片URL都是完整的
    const processedImages = images.map(image => {
      if (image.url && !image.url.startsWith('http')) {
        return {...image, url: `http://localhost:5000/${image.url}`};
      }
      return image;
    });
    
    uploadedImages.value = processedImages
  } catch (error) {
    console.error('获取已上传图片失败:', error)
  }
}

// 清空所有图片
const clearImages = () => {
  uploadedImages.value = []
  previewImages.value = []
}

// 初始化
onMounted(() => {
  loadUploadedImages()
})

// 加载已有图片用于修改


// 获取预览图片的文件对象
const getPreviewFiles = () => {
  return previewImages.value.map(image => image.file);
}

// 暴露公共方法
defineExpose({
  uploadImages,
  getPreviewFiles,
  previewImages,
  clearAll,
  clearImages
})
</script>

<style scoped>
.image-upload-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.upload-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.upload-stats {
  font-size: 14px;
  color: #666;
}

.upload-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
  border-left: 4px solid #ff9800;
  margin: 0 20px;
  border-radius: 0 8px 8px 0;
}

.tip-icon {
  font-size: 18px;
}

.tip-text {
  font-size: 14px;
  color: #e65100;
  font-weight: 500;
}

.upload-area {
  background: #f5f7fa;
  border: 2px dashed #e0e0e0;
  border-radius: 12px;
  margin: 20px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-area:hover {
  background: #e8ecf4;
  border-color: #667eea;
}

.file-input {
  display: none;
}

.upload-content {
  max-width: 400px;
  margin: 0 auto;
}

.upload-icon {
  font-size: 80px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.upload-content h3 {
  font-size: 20px;
  margin: 0 0 16px 0;
  color: #333;
}

.browse-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  margin-bottom: 12px;
}

.browse-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.browse-icon {
  font-size: 18px;
}

.upload-hint {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.image-preview-section {
  padding: 0 20px 20px;
}

.preview-title {
  font-size: 18px;
  color: #333;
  margin: 0 0 16px 0;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.preview-item {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
}

.preview-container {
  position: relative;
  margin-bottom: 8px;
}

.preview-image {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 6px;
  display: block;
}

.remove-button {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #ff6b6b;
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.3s ease;
}

.remove-button:hover {
  background: #ee5a52;
  transform: scale(1.1);
}

.remove-icon {
  line-height: 1;
}

.image-info {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  color: #666;
}

.image-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.image-size {
  font-size: 11px;
  color: #999;
}

.upload-actions {
  display: flex;
  gap: 12px;
  padding: 0 20px 20px;
  justify-content: flex-end;
}

.upload-button {
  background: #4caf50;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-button:hover:not(:disabled) {
  background: #388e3c;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.upload-button:disabled {
  background: #bdbdbd;
  cursor: not-allowed;
  opacity: 0.6;
}

.clear-button {
  background: #ff9800;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.clear-button:hover:not(:disabled) {
  background: #f57c00;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
}

.clear-button:disabled {
  background: #bdbdbd;
  cursor: not-allowed;
  opacity: 0.6;
}

.upload-progress {
  padding: 0 20px 20px;
}

.progress-bar {
  background: #e0e0e0;
  border-radius: 10px;
  height: 8px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  background: linear-gradient(90deg, #667eea 0%, #4caf50 100%);
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: #666;
  text-align: center;
}

.uploaded-images-section {
  padding: 0 20px 20px;
}

.uploaded-title {
  font-size: 18px;
  color: #333;
  margin: 0 0 16px 0;
}

.uploaded-item {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
}

.uploaded-container {
  position: relative;
  margin-bottom: 8px;
}

.uploaded-image {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 6px;
  display: block;
}

.delete-button {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #ff6b6b;
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.3s ease;
}

.delete-button:hover {
  background: #ee5a52;
  transform: scale(1.1);
}

.delete-icon {
  line-height: 1;
}

.image-date {
  font-size: 11px;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .upload-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .upload-area {
    margin: 10px;
    padding: 30px 15px;
  }
  
  .upload-icon {
    font-size: 60px;
  }
  
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
  }
  
  .upload-actions {
    flex-direction: column;
    padding: 0 10px 15px;
  }
  
  .image-preview-section,
  .uploaded-images-section {
    padding: 0 10px 15px;
  }
}
</style>
