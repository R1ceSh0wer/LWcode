import sys
import os

# 添加backend目录到Python路径
sys.path.append('e:\\桌面\\毕业论文\\LWcode\\backend')

from utils import get_knowledge_model, predict_knowledge_from_text, _check_netknowledge, load_netknowledge_model

print('开始测试知识点预测功能...')

# 测试1: 检查NetKnowledge是否可用
print('\n测试1: 检查NetKnowledge是否可用')
result = _check_netknowledge()
print(f'NetKnowledge可用: {result}')

# 测试2: 加载模型
print('\n测试2: 加载知识点模型')
model = get_knowledge_model()
print(f'模型加载成功: {model is not None}')

# 测试3: 测试预测功能
print('\n测试3: 测试知识点预测')
if model:
    test_text = '解方程 2x + 5 = 15'
    results = predict_knowledge_from_text(model, test_text)
    print(f'预测结果: {results}')
else:
    print('模型不可用，无法测试预测功能')

print('\n测试完成')
