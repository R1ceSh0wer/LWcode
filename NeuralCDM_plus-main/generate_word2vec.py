import json
import os
import gensim.models
from bintrees import FastRBTree

# 创建result目录（如果不存在）
os.makedirs('result', exist_ok=True)

# 加载训练数据
with open('data/net_knowledge_train.json', encoding='utf8') as i_f:
    exers = json.load(i_f)

# 准备训练语料
corpus = []
for exer in exers:
    corpus.append(exer['text'])

# 训练Word2Vec模型
print("开始训练Word2Vec模型...")
word2vec_model = gensim.models.Word2Vec(
    sentences=corpus,       # 训练语料
    vector_size=200,        # 向量维度
    window=5,               # 上下文窗口大小
    min_count=1,            # 最小词频
    workers=4,              # 并行线程数
    epochs=20               # 迭代次数
)

# 保存模型
word2vec_model.save('result/word2vec.model')
print("Word2Vec模型已保存到result/word2vec.model")

# 输出模型信息
print(f"词汇表大小: {len(word2vec_model.wv)}")
print(f"向量维度: {word2vec_model.vector_size}")
