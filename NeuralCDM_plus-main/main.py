'''
NeuralCDM+ (CNCD-Q)
@ Fei Wang
'''

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import json
import pickle


gpu_n = 0    # the device to be run on
device = torch.device(('cuda:'+str(gpu_n)) if torch.cuda.is_available() else 'cpu')
# information about the dataset
exer_n = 3790         # the total number of exercises in the dataset (题库)
knowledge_n = 197     # the total number of knowledge concepts in the dataset
student_n = 190       # the total number of students in the dataset
# hyper parameter
sequence_len = 600    # maximum number of tokens in the text of an exercises


# the NeuralCDM+ (CNCD-Q) model
class Net(nn.Module):
    def __init__(self):
        self.knowledge_dim = knowledge_n
        self.exer_n = exer_n
        self.emb_num = student_n
        self.stu_dim = self.knowledge_dim
        self.prednet_input_len = self.knowledge_dim
        self.prednet_len1, self.prednet_len2 = 512, 256  # changeable hyper parameter

        super(Net, self).__init__()

        # prediction sub-net
        self.student_emb = nn.Embedding(self.emb_num, self.stu_dim)
        self.k_difficulty = nn.Embedding(self.exer_n, self.knowledge_dim)
        self.e_discrimination = nn.Embedding(self.exer_n, 1)
        self.e_k_prob = nn.Embedding(self.exer_n, self.knowledge_dim)   # the embeddings relevant to knowledge relevancy vectors
        self.prednet_full1 = nn.Linear(self.prednet_input_len, self.prednet_len1)
        self.drop_1 = nn.Dropout(p=0.5)
        self.prednet_full2 = nn.Linear(self.prednet_len1, self.prednet_len2)
        self.drop_2 = nn.Dropout(p=0.5)
        self.prednet_full3 = nn.Linear(self.prednet_len2, 1)

        # initialize
        for name, param in self.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)

    def forward(self, stu_id, input_exercise, knowledge_masks):
        # before prednet
        stu_emb = self.student_emb(stu_id)
        stat_emb = F.sigmoid(stu_emb)      # knowledge proficiency vector of the input students
        k_difficulty = F.sigmoid(self.k_difficulty(input_exercise))
        e_discrimination = F.sigmoid(self.e_discrimination(input_exercise)) * 10
        e_k_prob = self.e_k_prob(input_exercise)
        e_k_prob_2 = F.sigmoid(e_k_prob)    # knowledge relevancy vectors of the exercises
        # prednet
        input_x = e_discrimination * (stat_emb - k_difficulty) * (knowledge_masks * e_k_prob_2)
        input_x = self.drop_1(F.sigmoid(self.prednet_full1(input_x)))
        input_x = self.drop_2(F.sigmoid(self.prednet_full2(input_x)))
        output_1 = F.sigmoid(self.prednet_full3(input_x))
        output_0 = torch.ones_like(output_1) - output_1
        output = torch.cat((output_0, output_1), 1)

        return output, e_k_prob

    def apply_clipper(self):
        clipper = NoneNegClipper()
        self.prednet_full1.apply(clipper)
        self.prednet_full2.apply(clipper)
        self.prednet_full3.apply(clipper)

    def get_knowledge_status(self, stat_idx):
        stat_emb = torch.sigmoid(self.student_emb(stat_idx))
        return stat_emb.data

    def get_knowledge_difficulty(self, exer_idx):
        k_difficulty = F.sigmoid(self.k_difficulty(exer_idx))
        return k_difficulty.data

    def get_e_k_prob(self, exer_idx):
        e_k_prob = self.e_k_prob(exer_idx)
        e_k_prob = F.sigmoid(e_k_prob)
        return e_k_prob.data


class DataLoader(object):
    def __init__(self):
        self.batch_size = 32
        self.ptr = 0
        self.data = []
        self.knowledge_dim = knowledge_n
        self.max_sequence_len = sequence_len

        with open('data/train_set.json', encoding='utf8') as input_file:
            self.data = json.load(input_file)
        with open('data/word2id.FastRBTree', 'rb') as i_f:
            self.word2id = pickle.load(i_f)
        with open('data/netknowledge_pred_topk_knowledge_pairs.FastRBTree', 'rb') as i_f:
            self.exer_id2pairs = pickle.load(i_f)

    def next_batch(self):
        if self.is_end():
            return None, None, None, None, None, None
        input_x1s, input_x2s, knowledge_labels, knowledge_pairs, knowledge_masks, ys = [], [], [], [], [], []
        for count in range(self.batch_size):
            log = self.data[self.ptr + count]
            
            # 调试：打印当前处理的日志
            print(f"\n处理第 {count+1} 个样本:")
            print(f"user_id: {log['user_id']}, exer_id: {log['exer_id']}")
            print(f"原始knowledge_code: {log['knowledge_code']}")
            
            # 构建knowledge_label
            knowledge_label = [0.] * self.knowledge_dim
            for knowledge_code in log['knowledge_code']:
                print(f"处理knowledge_code: {knowledge_code}")
                if 1 <= knowledge_code <= self.knowledge_dim:
                    knowledge_label[knowledge_code - 1] = 1.0
                    print(f"  有效，索引: {knowledge_code - 1}")
                else:
                    print(f"  无效，超出范围: 1-{self.knowledge_dim}")
            
            y = log['score']
            input_x1s.append(log['user_id'] - 1)
            input_x2s.append(log['exer_id'] - 1)
            knowledge_labels.append(knowledge_label)
            
            # 处理知识点对不存在的情况
            kn_pairs = self.exer_id2pairs.get(log['exer_id'])
            if kn_pairs:
                kn_tags, kn_topks = kn_pairs
                print(f"从exer_id2pairs获取的kn_tags: {kn_tags}")
                print(f"从exer_id2pairs获取的kn_topks: {kn_topks}")
            else:
                # 如果知识点对不存在，使用该题目的知识点作为替代
                kn_tags = log.get('knowledge_code', [])
                kn_topks = []
                print(f"使用题目知识点作为替代: {kn_tags}")
            
            knowledge_pairs.append((kn_tags, kn_topks))
            
            # 构建knowledge_masks
            mask = [0.] * self.knowledge_dim
            print(f"构建mask，长度: {len(mask)}")
            
            for kn in kn_tags:
                print(f"处理kn_tags中的 {kn}")
                if 1 <= kn <= self.knowledge_dim:
                    mask[kn-1] = 1.0
                    print(f"  有效，索引: {kn-1}")
                else:
                    print(f"  无效，超出范围: 1-{self.knowledge_dim}")
            
            for kn in kn_topks:
                print(f"处理kn_topks中的 {kn}")
                if 1 <= kn <= self.knowledge_dim:
                    mask[kn-1] = 1.0
                    print(f"  有效，索引: {kn-1}")
                else:
                    print(f"  无效，超出范围: 1-{self.knowledge_dim}")
            
            knowledge_masks.append(mask)
            ys.append(y)

        self.ptr += self.batch_size
        # return student id, exercise id, knowledge labels, scores, knowledge pairs, knowledge mask
        return torch.LongTensor(input_x1s), torch.LongTensor(input_x2s), torch.Tensor(knowledge_labels), torch.LongTensor(ys), knowledge_pairs, torch.Tensor(knowledge_masks)

    def is_end(self):
        if self.ptr + self.batch_size > len(self.data):
            return True
        else:
            return False

    def reset(self):
        self.ptr = 0


class ValTestDataLoader(object):
    def __init__(self, d_type='validation'):
        self.ptr = 0
        self.data = []
        self.knowledge_dim = knowledge_n
        self.d_type = d_type
        self.max_sequence_len = sequence_len

        if d_type == 'validation':
            file_name = 'data/val_set.json'
        else:
            file_name = 'data/test_set.json'
        with open(file_name, encoding='utf8') as input_file:
            self.data = json.load(input_file)
        with open('data/word2id.FastRBTree', 'rb') as i_f:
            self.word2id = pickle.load(i_f)
        with open('data/netknowledge_pred_topk_knowledge_pairs.FastRBTree', 'rb') as i_f:
            self.exer_id2pairs = pickle.load(i_f)

    def next_batch(self):
        if self.is_end():
            return None, None, None, None, None, None
        logs = self.data[self.ptr]['logs']
        user_id = self.data[self.ptr]['user_id']
        input_x1s, input_x2s, knowledge_labels, knowledge_pairs, knowledge_masks, ys = [], [], [], [], [], []
        for log in logs:
            input_x1s.append(user_id - 1)
            input_x2s.append(log['exer_id'] - 1)
            knowledge_label = [0.] * self.knowledge_dim
            for knowledge_code in log['knowledge_code']:
                knowledge_label[knowledge_code - 1] = 1.0
            knowledge_labels.append(knowledge_label)
            # 处理知识点对不存在的情况
            kn_pairs = self.exer_id2pairs.get(log['exer_id'])
            if kn_pairs:
                kn_tags, kn_topks = kn_pairs
            else:
                # 如果知识点对不存在，使用该题目的知识点作为替代
                kn_tags = log.get('knowledge_code', [])
                kn_topks = []
            knowledge_pairs.append((kn_tags, kn_topks))
            mask = [0.] * self.knowledge_dim
            for kn in kn_tags:
                mask[kn - 1] = 1.0
            for kn in kn_topks:
                mask[kn - 1] = 1.0
            knowledge_masks.append(mask)
            # y = 1 if log['score'] > 0.8 else 0
            y = log['score']
            ys.append(y)
        self.ptr += 1
        return torch.LongTensor(input_x1s), torch.LongTensor(input_x2s), torch.Tensor(knowledge_labels), torch.LongTensor(ys), knowledge_pairs, torch.Tensor(knowledge_masks)

    def is_end(self):
        if self.ptr >= len(self.data):
            return True
        else:
            return False

    def reset(self):
        self.ptr = 0


class NoneNegClipper(object):
    def __init__(self):
        super(NoneNegClipper, self).__init__()

    def __call__(self, module):
        if hasattr(module, 'weight'):
            w = module.weight.data
            a = F.relu(torch.neg(w))
            w.add_(a)


def save_snapshot(model, filename):
    f = open(filename, 'wb')
    torch.save(model.state_dict(), f)
    f.close()


def load_snapshot(model, filename):
    f = open(filename, 'rb')
    model.load_state_dict(torch.load(f, map_location=lambda s, loc: s, weights_only=True))
    f.close()


def train(epoch_n=1):
    data_loader = DataLoader()
    net = Net().to(device)
    normal_mean, normal_C = 0, 2
    means = torch.ones(knowledge_n) * normal_mean  # the mean of the multidimensional gaussian distribution
    means.require_grad = False
    means = means.to(device)
    C = torch.ones(knowledge_n) * normal_C     # the diagonal of the covariance matrix
    C.require_grad = False
    C = C.to(device)
    optimizer = optim.Adam(net.parameters(), lr=0.0005)
    print('training model...')

    loss2_function = nn.NLLLoss()

    for epoch in range(epoch_n):
        data_loader.reset()
        running_loss = 0.0
        batch_count = 0
        while not data_loader.is_end():
            batch_count += 1
            input_x1s, input_x2s, knowledge_labels, labels, knowledge_pairs, knowledge_masks = data_loader.next_batch()
            input_x1s, input_x2s, knowledge_labels, labels, knowledge_masks = input_x1s.to(device), input_x2s.to(device), knowledge_labels.to(device), labels.to(device), knowledge_masks.to(device)
            optimizer.zero_grad()
            out_put, exer_knowledge_prob = net.forward(input_x1s, input_x2s, knowledge_masks)

            loss_1 = loss2_function(torch.log(out_put), labels)
            loss_2 = 0
            print(f"\n处理batch {batch_count}:")
            print(f"knowledge_pairs长度: {len(knowledge_pairs)}")
            print(f"exer_knowledge_prob形状: {exer_knowledge_prob.shape}")
            
            for pair_i in range(len(knowledge_pairs)):
                print(f"\n处理第 {pair_i+1} 个知识点对:")
                kn_tags, kn_topks = knowledge_pairs[pair_i]
                print(f"原始kn_tags: {kn_tags}")
                print(f"原始kn_topks: {kn_topks}")
                
                # 添加边界检查，确保知识点索引在有效范围内
                kn_tags = [k for k in kn_tags if 1 <= k <= knowledge_n]
                kn_topks = [k for k in kn_topks if 1 <= k <= knowledge_n]
                print(f"过滤后kn_tags: {kn_tags}")
                print(f"过滤后kn_topks: {kn_topks}")
                
                if not kn_tags or not kn_topks:
                    print(f"跳过无效的知识点对")
                    continue
                    
                kn_tags, kn_topks = np.array(kn_tags) - 1, np.array(kn_topks) - 1
                print(f"转换后kn_tags索引: {kn_tags}")
                print(f"转换后kn_topks索引: {kn_topks}")
                
                # 检查索引范围
                if len(kn_tags) > 0:
                    max_tag = max(kn_tags)
                    min_tag = min(kn_tags)
                    print(f"kn_tags索引范围: {min_tag} - {max_tag}")
                    if max_tag >= knowledge_n or min_tag < 0:
                        print(f"警告：kn_tags索引超出范围！")
                
                if len(kn_topks) > 0:
                    max_topk = max(kn_topks)
                    min_topk = min(kn_topks)
                    print(f"kn_topks索引范围: {min_topk} - {max_topk}")
                    if max_topk >= knowledge_n or min_topk < 0:
                        print(f"警告：kn_topks索引超出范围！")
                
                kn_tag_n = len(kn_tags)
                print(f"kn_tag_n: {kn_tag_n}")
                print(f"访问exer_knowledge_prob[{pair_i}]，形状: {exer_knowledge_prob[pair_i].shape}")
                
                try:
                    # 检查exer_knowledge_prob[pair_i]的维度
                    prob_shape = exer_knowledge_prob[pair_i].shape
                    print(f"exer_knowledge_prob[{pair_i}]形状: {prob_shape}")
                    
                    # 确保kn_tags和kn_topks中的索引在有效范围内
                    if len(prob_shape) > 0:
                        max_index = prob_shape[0] - 1
                        print(f"最大有效索引: {max_index}")
                        print(f"knowledge_n: {knowledge_n}")
                        print(f"prob_shape[0]: {prob_shape[0]}")
                        
                        # 检查索引是否超出范围
                        if kn_tags.size > 0:
                            max_kn_tag = kn_tags.max()
                            min_kn_tag = kn_tags.min()
                            print(f"kn_tags最大值: {max_kn_tag}, 最小值: {min_kn_tag}")
                            if max_kn_tag > max_index:
                                print(f"错误：kn_tags中的索引 {max_kn_tag} 超出范围！")
                            if min_kn_tag < 0:
                                print(f"错误：kn_tags中的索引 {min_kn_tag} 超出范围！")
                        
                        if kn_topks.size > 0:
                            max_kn_topk = kn_topks.max()
                            min_kn_topk = kn_topks.min()
                            print(f"kn_topks最大值: {max_kn_topk}, 最小值: {min_kn_topk}")
                            if max_kn_topk > max_index:
                                print(f"错误：kn_topks中的索引 {max_kn_topk} 超出范围！")
                            if min_kn_topk < 0:
                                print(f"错误：kn_topks中的索引 {min_kn_topk} 超出范围！")
                        
                        # 过滤超出范围的索引
                        valid_kn_tags = [idx for idx in kn_tags if 0 <= idx <= max_index]
                        valid_kn_topks = [idx for idx in kn_topks if 0 <= idx <= max_index]
                        
                        print(f"过滤后kn_tags: {valid_kn_tags}")
                        print(f"过滤后kn_topks: {valid_kn_topks}")
                        
                        if not valid_kn_tags or not valid_kn_topks:
                            print(f"跳过无效的索引")
                            continue
                        
                        kn_tag_tensor = exer_knowledge_prob[pair_i][valid_kn_tags].view(-1, 1)
                        print(f"kn_tag_tensor形状: {kn_tag_tensor.shape}")
                        
                        kn_prob_tensor = exer_knowledge_prob[pair_i][valid_kn_topks].repeat(len(valid_kn_tags), 1)
                        print(f"kn_prob_tensor形状: {kn_prob_tensor.shape}")
                        
                        loss_2 = loss_2 - (torch.log(torch.sigmoid((kn_tag_tensor - kn_prob_tensor) * 0.1))).sum()
                        print(f"loss_2更新后: {loss_2.item()}")
                    else:
                        print(f"跳过空的exer_knowledge_prob[{pair_i}]")
                except Exception as e:
                    print(f"错误：{e}")
                    print(f"pair_i: {pair_i}")
                    print(f"kn_tags: {kn_tags}")
                    print(f"kn_topks: {kn_topks}")
                    print(f"exer_knowledge_prob形状: {exer_knowledge_prob.shape}")
                    print(f"exer_knowledge_prob[{pair_i}]形状: {exer_knowledge_prob[pair_i].shape}")
                    raise
            for kn_prob in exer_knowledge_prob:
                a = kn_prob - means
                loss_2 = loss_2 + 0.5 * (a * a / C).sum()

            loss = loss_1 + loss_2
            loss.backward()
            optimizer.step()
            net.apply_clipper()

            running_loss += loss.item()
            if batch_count % 200 == 199:
                print('[%d, %5d] loss: %.3f' % (epoch, batch_count + 1, running_loss / 200))
                running_loss = 0.0

        rmse, auc = validate(net)
        save_snapshot(net, 'model/model_epoch' + str(epoch))


def validate(model):
    data_loader = ValTestDataLoader('validation')
    net = Net()
    print('validating model...')
    data_loader.reset()
    # load model parameters
    net.load_state_dict(model.state_dict())
    net = net.to(device)
    net.eval()

    batch_count, batch_avg_loss = 0, 0.0
    pred_all, label_all = [], []
    while not data_loader.is_end():
        batch_count += 1
        input_x1s, input_x2s, knowledge_labels, labels, knowledge_pairs, knowledge_masks = data_loader.next_batch()
        input_x1s, input_x2s, knowledge_labels, labels, knowledge_masks = input_x1s.to(device), input_x2s.to(
            device), knowledge_labels.to(device), labels.to(device), knowledge_masks.to(device)

        out_put, _ = net.forward(input_x1s, input_x2s, knowledge_masks)
        # compute accuracy
        pred_all += out_put[:, 1].to(torch.device('cpu')).tolist()
        label_all += labels.to(torch.device('cpu')).tolist()

    pred_all = np.array(pred_all)
    label_all = np.array(label_all)
    # compute accuracy of model
    accuracy = np.mean(label_all == (pred_all > 0.5))
    # compute RMSE of model
    rmse = np.sqrt(np.mean((label_all - pred_all) ** 2))
    # compute AUC of model
    # 简单的AUC计算实现
    sorted_indices = np.argsort(pred_all)[::-1]
    sorted_labels = label_all[sorted_indices]
    tp = 0
    fp = 0
    tpr = []
    fpr = []
    for l in sorted_labels:
        if l == 1:
            tp += 1
        else:
            fp += 1
        tpr.append(tp / np.sum(label_all))
        fpr.append(fp / (len(label_all) - np.sum(label_all)))
    # 计算梯形面积
    auc = 0
    for i in range(1, len(tpr)):
        auc += (fpr[i] - fpr[i-1]) * (tpr[i] + tpr[i-1]) / 2
    print('accuracy= %f, rmse= %f, auc= %f' % (accuracy, rmse, auc))
    with open('result/model_val.txt', 'a', encoding='utf8') as f:
        f.write('accuracy= %f, rmse= %f, auc= %f\n' % (accuracy, rmse, auc))

    return rmse, auc


def test(epoch_n=30):
    data_loader = ValTestDataLoader('test')
    net = Net()
    print('testing model...')
    for epoch in range(epoch_n):
        data_loader.reset()
        # load model parameter
        load_snapshot(net, 'model/model_epoch' + str(epoch))
        net = net.to(device)
        net.eval()

        batch_count, batch_avg_loss = 0, 0.0
        pred_all, label_all = [], []
        while not data_loader.is_end():
            batch_count += 1
            input_x1s, input_x2s, knowledge_labels, labels, knowledge_pairs, knowledge_masks = data_loader.next_batch()
            input_x1s, input_x2s, knowledge_labels, labels, knowledge_masks = input_x1s.to(device), input_x2s.to(
                device), knowledge_labels.to(device), labels.to(device), knowledge_masks.to(device)

            out_put, _ = net.forward(input_x1s, input_x2s, knowledge_masks)
            # compute accuracy
            pred_all += out_put[:, 1].to(torch.device('cpu')).tolist()
            label_all += labels.to(torch.device('cpu')).tolist()

        pred_all = np.array(pred_all)
        label_all = np.array(label_all)
        # compute accuracy of model
        accuracy = np.mean(label_all == (pred_all > 0.5))
        # compute RMSE of model
        rmse = np.sqrt(np.mean((label_all - pred_all) ** 2))
        # compute AUC of model
        # 简单的AUC计算实现
        sorted_indices = np.argsort(pred_all)[::-1]
        sorted_labels = label_all[sorted_indices]
        tp = 0
        fp = 0
        tpr = []
        fpr = []
        for l in sorted_labels:
            if l == 1:
                tp += 1
            else:
                fp += 1
            tpr.append(tp / np.sum(label_all))
            fpr.append(fp / (len(label_all) - np.sum(label_all)))
        # 计算梯形面积
        auc = 0
        for i in range(1, len(tpr)):
            auc += (fpr[i] - fpr[i-1]) * (tpr[i] + tpr[i-1]) / 2
        print('accuracy= %f, rmse= %f, auc= %f' % (accuracy, rmse, auc))
        with open('result/model_test.txt', 'a', encoding='utf8') as f:
            f.write('epoch= %d, accuracy= %f, rmse= %f, auc= %f\n' % (epoch, accuracy, rmse, auc))


if __name__ == '__main__':
    train()
    test()

