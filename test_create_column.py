import requests
import os

# 测试创建专栏
url = 'http://localhost:5000/api/columns'

# 准备表单数据
data = {
    'name': '测试专栏',
    'teacherId': '1'
}

# 准备文件（使用一张测试图片）
# 注意：需要确保测试图片存在
image_path = 'e:\\桌面\\毕业论文\\LWcode\\backend\\uploads\\test.jpg'
files = {}

if os.path.exists(image_path):
    files['image1'] = open(image_path, 'rb')
    print(f'使用测试图片: {image_path}')
else:
    print('测试图片不存在，仅创建空专栏')

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
