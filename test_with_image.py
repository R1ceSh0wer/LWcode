import requests
import os
import base64

# 测试创建专栏（使用Base64编码的简单图片）
url = 'http://localhost:5000/api/columns'

# 准备表单数据
data = {
    'name': '测试专栏带图片',
    'teacherId': '1'
}

# 创建一个简单的测试图片（包含题号）
# 使用一个简单的文本图片
# 这里我们使用一个现有的图片或创建一个

# 检查是否有任何图片文件可用
test_image_path = None
uploads_dir = 'e:\\桌面\\毕业论文\\LWcode\\backend\\uploads'

if os.path.exists(uploads_dir):
    # 查找第一个jpg或png文件
    for file in os.listdir(uploads_dir):
        if file.endswith('.jpg') or file.endswith('.png'):
            test_image_path = os.path.join(uploads_dir, file)
            break

files = {}

if test_image_path:
    print(f'使用测试图片: {test_image_path}')
    files['image1'] = open(test_image_path, 'rb')
else:
    print('没有找到测试图片，创建一个简单的测试')
    # 注意：没有图片时不会触发知识点预测

try:
    print('发送创建专栏请求...')
    response = requests.post(url, data=data, files=files)
    print(f'响应状态码: {response.status_code}')
    print(f'响应内容: {response.text}')
except Exception as e:
    print(f'请求失败: {str(e)}')
finally:
    if files.get('image1'):
        files['image1'].close()
