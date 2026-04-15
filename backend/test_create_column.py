from app import create_app
from flask import json

app = create_app()

with app.test_client() as client:
    # 测试添加专栏
    response = client.post('/api/columns', json={
        'name': '测试专栏',
        'teacherId': 1,
        'archiveId': 2,
        'questionText': '1：测试题目1；2：测试题目2',
        'commentGenerationMethod': 'text'
    })
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.data.decode('utf-8')}")
