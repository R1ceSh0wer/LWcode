import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// 获取当前文件的目录路径
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 配置axios实例
const api = axios.create({
  baseURL: 'http://localhost:5174/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'multipart/form-data'
  }
});

// 创建一个简单的测试图片
const createTestImage = async () => {
  const testImagePath = path.join(__dirname, 'test_image.png');
  
  // 创建一个简单的PNG文件
  const pngHeader = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
  const pngFooter = Buffer.from([0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82]);
  const content = Buffer.concat([pngHeader, Buffer.alloc(100), pngFooter]);
  
  await fs.promises.writeFile(testImagePath, content);
  return testImagePath;
};

// 测试图片上传和删除流程
const testImageFlow = async () => {
  let testImagePath;
  let uploadedImageId;
  
  try {
    console.log('1. 创建测试图片...');
    testImagePath = await createTestImage();
    console.log(`测试图片创建成功: ${testImagePath}`);
    
    // 准备FormData
    const formData = new FormData();
    const file = fs.createReadStream(testImagePath);
    formData.append('file', file, 'test_image.png');
    
    console.log('\n2. 测试图片上传...');
    const uploadResponse = await api.post('/images/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    console.log('上传响应:', JSON.stringify(uploadResponse.data, null, 2));
    
    // 验证上传响应
    if (uploadResponse.data.success && uploadResponse.data.image) {
      uploadedImageId = uploadResponse.data.image.id;
      console.log(`\n3. 上传成功，获取到图片ID: ${uploadedImageId}`);
    } else {
      throw new Error('上传失败，响应格式不正确');
    }
    
    // 获取已上传图片列表
    console.log('\n4. 获取已上传图片列表...');
    const imagesResponse = await api.get('/images');
    console.log('图片列表:', JSON.stringify(imagesResponse.data, null, 2));
    
    // 验证图片是否在列表中
    const uploadedImage = imagesResponse.data.find(img => img.id === uploadedImageId);
    if (uploadedImage) {
      console.log('\n5. 验证成功：图片已在上传列表中');
    } else {
      throw new Error('验证失败：上传的图片不在列表中');
    }
    
    // 测试删除图片
    console.log('\n6. 测试删除图片...');
    const deleteResponse = await api.delete(`/images/${uploadedImageId}`);
    console.log('删除响应:', JSON.stringify(deleteResponse.data, null, 2));
    
    // 验证删除是否成功
    if (deleteResponse.data.success) {
      console.log('\n7. 删除成功！');
    } else {
      throw new Error('删除失败');
    }
    
    // 验证图片是否已删除
    console.log('\n8. 验证图片是否已删除...');
    const updatedImagesResponse = await api.get('/images');
    const stillExists = updatedImagesResponse.data.some(img => img.id === uploadedImageId);
    
    if (!stillExists) {
      console.log('\n✅ 所有测试通过！图片上传和删除流程正常工作');
    } else {
      throw new Error('验证失败：图片仍在列表中');
    }
    
  } catch (error) {
    console.error('\n❌ 测试失败:', error.message);
    if (error.response) {
      console.error('错误响应:', JSON.stringify(error.response.data, null, 2));
      console.error('状态码:', error.response.status);
    }
    process.exit(1);
  } finally {
    // 清理测试文件
    if (testImagePath && fs.existsSync(testImagePath)) {
      fs.unlinkSync(testImagePath);
      console.log('\n测试图片已清理');
    }
    
    process.exit(0);
  }
};

// 注意：这个脚本需要浏览器环境的FormData支持
// 在Node.js中运行需要安装form-data包
// npm install form-data
import FormData from 'form-data';

testImageFlow();
