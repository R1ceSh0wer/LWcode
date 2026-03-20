<template>
  <div class="dashboard-container">

    
    <!-- 查看评语模态框 -->
    <SimpleModal 
      :isVisible="isViewCommentModalVisible" 
      title="学生评语"
      @close="isViewCommentModalVisible = false"
    >
      <div class="comment-content">
        <h4>评语:</h4>
        <p>{{ viewCommentContent }}</p>
        <div class="comment-feedback">
          <h4>学生反馈:</h4>
          <p>{{ viewCommentFeedback || '无' }}</p>
        </div>
      </div>
      <div class="modal-footer">
        <button @click="isViewCommentModalVisible = false" class="cancel-button">关闭</button>
        <button @click="handleEditComment" class="submit-button">修改评语</button>
      </div>
    </SimpleModal>
    
    <!-- 确认删除模态框 -->
    <SimpleModal 
      :isVisible="isDeleteConfirmVisible" 
      title="确认删除"
      @close="isDeleteConfirmVisible = false"
    >
      <div class="delete-confirm-content">
        <div class="delete-icon">⚠️</div>
        <p>{{ deleteConfirmMessage }}</p>
      </div>
      <div class="modal-footer">
        <button @click="isDeleteConfirmVisible = false" class="cancel-button">取消</button>
        <button @click="confirmDelete" class="submit-button delete-button">确认删除</button>
      </div>
    </SimpleModal>

    <!-- 批量生成评语模态框 -->
    <SimpleModal 
      :isVisible="isBatchCommentModalVisible" 
      title="批量生成评语"
      @close="closeBatchCommentModal"
    >
      <!-- 导航箭头 -->
      <div class="batch-navigation">
        <button 
          @click="navigateBatchModal(-1)" 
          class="nav-button" 
          :disabled="currentBatchIndex === 0"
        >
          ← 上一个
        </button>
        <span class="batch-progress">{{ currentBatchIndex + 1 }} / {{ batchStudents.length }}</span>
        <button 
          @click="navigateBatchModal(1)" 
          class="nav-button" 
          :disabled="currentBatchIndex === batchStudents.length - 1"
        >
          下一个 →
        </button>
      </div>
      
      <div class="modal-body">
        <div v-if="currentBatchStudent" class="batch-student-info">
          <h4>{{ currentBatchStudent.name }} ({{ currentBatchStudent.studentId }})</h4>
          <p>班级: {{ currentBatchStudent.className }}</p>
        </div>
        
        <!-- 附加评语输入 -->
        <div class="form-group">
          <label class="form-label">附加评语（选填）</label>
          <textarea 
            v-model="batchAdditionComments[currentBatchIndex]" 
            placeholder="请输入附加评语（可选）"
            class="form-textarea"
            rows="4"
          ></textarea>
        </div>
        
        <!-- 图片上传 -->
        <div class="form-group">
          <label class="form-label">上传答案图片（最多6张）</label>
          <ImageUpload 
            ref="batchImageUploads" 
            :key="batchImageUploadKey"
            :max-files="6"
            :accepted-formats="['image/jpeg', 'image/png', 'image/jpg']"
          />
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="closeBatchCommentModal" class="cancel-button">取消</button>
        <button 
          @click="generateBatchComments" 
          class="submit-button"
          :disabled="isBatchGenerating"
        >
          {{ isBatchGenerating ? '生成中...' : '生成评语' }}
        </button>
      </div>
    </SimpleModal>

    <!-- 顶部导航栏 -->
    <nav class="top-navigation">
      <div class="nav-left">
        <div class="logo">
          <span class="logo-icon">🎓</span>
          <h1 class="logo-text">学生评语系统</h1>
        </div>
        <div class="nav-buttons">
          <button 
            :class="['nav-button', { active: activeTab === 'comment-management' }]"
            @click="switchTab('comment-management')"
          >
            学生评语管理
          </button>
          <button 
            :class="['nav-button', { active: activeTab === 'account-management' }]"
            @click="switchTab('account-management')"
          >
            账号管理
          </button>
          <button 
            :class="['nav-button', { active: activeTab === 'resource-recommendation' }]"
            @click="switchTab('resource-recommendation')"
          >
            学习资源推荐
          </button>
          <button 
            :class="['nav-button', { active: activeTab === 'model-archives' }]"
            @click="switchTab('model-archives')"
          >
            模型存档管理
          </button>
        </div>
      </div>
      <div class="nav-right">
        <div class="user-info">
          <span class="user-name">{{ currentUser.name }}</span>
          <button @click="logout" class="logout-button">
            <i class="logout-icon">🚪</i> 退出登录
          </button>
        </div>
      </div>
    </nav>

    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 学生评语管理界面 -->
      <div v-if="activeTab === 'comment-management'">
        <!-- 页面标题和操作区 -->
        <div class="page-header">
          <h2>学生评语管理</h2>
          <div class="header-actions">
            <button 
              @click="handleBatchGenerate" 
              class="batch-generate-button"
              :disabled="!selectedColumnId || selectedStudents.length === 0"
            >
              📋 批量生成评语
            </button>
            <button @click="isColumnModalVisible = true" class="create-column-button">
              📋 创建专栏
            </button>
          </div>
        </div>

        <!-- 筛选和搜索区 -->
        <div class="filter-section">
          <div class="filter-group">
            <label for="column-filter">选择专栏:</label>
            <div class="column-select-container">
              <select 
                id="column-filter" 
                v-model="selectedColumnId"
                class="filter-select"
              >
                <option 
                  v-for="column in columns" 
                  :key="column.id" 
                  :value="column.id"
                >
                  {{ column.name }}
                </option>
              </select>
              <button 
                v-if="selectedColumnId" 
                @click="deleteSelectedColumn"
                class="delete-column-button"
                title="删除当前专栏"
              >
                ×
              </button>
            </div>
          </div>
          
          <div class="filter-group">
            <label for="class-filter">选择班级:</label>
            <select 
              id="class-filter" 
              v-model="selectedClass"
              class="filter-select"
            >
              <option value="">所有班级</option>
              <option 
                v-for="className in classList" 
                :key="className" 
                :value="className"
              >
                {{ className }}
              </option>
            </select>
          </div>
          
          <div class="filter-group search-group">
            <label for="search-input">搜索学生:</label>
            <input 
              id="search-input" 
              v-model="searchKeyword"
              placeholder="输入学生姓名或学号"
              class="search-input"
            >
          </div>

          <div class="filter-group column-info-group">
            <button
              v-if="selectedColumnId"
              @click="openColumnInfoModal"
              class="column-info-text-button"
              type="button"
              title="查看/修改当前专栏信息"
            >
              查看专栏信息
            </button>
          </div>
        </div>

        <!-- 学生列表 -->
        <div class="students-container">
          <table class="students-table">
            <thead>
              <tr>
                <th width="40">
                  <input 
                    type="checkbox" 
                    v-model="selectAllStudents" 
                    @change="handleSelectAll"
                    class="select-all-checkbox"
                  >
                </th>
                <th>学生信息</th>
                <th>班级</th>
                <th>专栏</th>
                <th>评语状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="student in filteredStudents" 
                :key="student.id"
                class="student-row"
              >
                <td>
                  <input 
                    type="checkbox" 
                    v-model="selectedStudents" 
                    :value="student.id" 
                    class="student-checkbox"
                  >
                </td>
                <td class="student-info">
                  <div class="student-avatar">{{ student.name.charAt(0) }}</div>
                  <div class="student-details">
                    <div class="student-name">{{ student.name }}</div>
                    <div class="student-id">{{ student.studentId }}</div>
                  </div>
                </td>
                <td>{{ student.className }}</td>
                <td>
                  <div class="column-info">
                    <span v-if="getStudentColumnComment(student.id, selectedColumnId)">
                      {{ columns.find(c => c.id === selectedColumnId)?.name || '未选择专栏' }}
                    </span>
                    <span v-else class="no-column">未生成</span>
                  </div>
                </td>
                <td>
                  <div 
                    :class="['status-badge', getStudentColumnComment(student.id, selectedColumnId) ? 'completed' : 'pending']"
                  >
                    {{ getStudentColumnComment(student.id, selectedColumnId) ? '已生成' : '未生成' }}
                  </div>
                </td>
                <td>
                  <!-- 如果找到评语，显示查看评语按钮 -->
                  <button 
                    v-if="getStudentColumnComment(student.id, selectedColumnId)"
                    @click="handleViewComment(student, getStudentColumnComment(student.id, selectedColumnId))"
                    class="action-button"
                  >
                    查看评语
                  </button>
                  <!-- 如果未找到评语，显示生成评语按钮 -->
                  <button 
                    v-else
                    @click="handleStudentAction(student)"
                    class="action-button"
                  >
                    生成评语
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="filteredStudents.length === 0" class="no-students">
            <div class="no-students-icon">👨‍🎓</div>
            <h3>没有找到学生</h3>
            <p>请调整筛选条件后重试</p>
          </div>
        </div>
      </div>

      <!-- 账号管理界面 -->
      <div v-else-if="activeTab === 'account-management'">
        <!-- 页面标题和操作区 -->
        <div class="page-header">
          <h2>账号管理</h2>
          <div class="header-actions">
            <button @click="isBatchAddModalVisible = true" class="create-column-button">
              📋 批量添加
            </button>
            <button @click="isAddAccountModalVisible = true" class="create-column-button">
              📋 添加账号
            </button>
          </div>
        </div>

        <!-- 筛选和搜索区 -->
        <div class="filter-section">
          <div class="filter-group">
            <label for="role-filter">选择角色:</label>
            <select 
              id="role-filter" 
              v-model="selectedRole"
              class="filter-select"
            >
              <option value="">所有角色</option>
              <option value="student">学生</option>
              <option value="teacher">教师</option>
            </select>
          </div>
          
          <!-- 班级筛选下拉框（仅学生角色可见） -->
          <div class="filter-group" v-if="selectedRole === 'student'">
            <label for="account-class-filter">选择班级:</label>
            <select 
              id="account-class-filter" 
              v-model="selectedAccountClass"
              class="filter-select"
            >
              <option value="">所有班级</option>
              <option 
                v-for="className in accountClassList" 
                :key="className" 
                :value="className"
              >
                {{ className }}
              </option>
            </select>
          </div>
          
          <div class="filter-group search-group">
            <label for="account-search-input">搜索账号:</label>
            <input 
              id="account-search-input" 
              v-model="accountSearchKeyword"
              placeholder="输入用户名"
              class="search-input"
            >
          </div>
        </div>

        <!-- 账号列表 -->
        <div class="students-container">
          <table class="students-table">
            <thead>
              <tr>
                <th>用户名</th>
                <th>角色</th>
                <!-- 动态显示：仅学生角色可见 -->
                <th v-if="selectedRole === 'student'">学号</th>
                <th v-if="selectedRole === 'student'">班级</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="account in filteredAccounts" 
                :key="account.id"
                class="student-row"
              >
                <td>{{ account.username }}</td>
                <td>
                  <div :class="['status-badge', account.role === 'teacher' ? 'completed' : 'pending']">
                    {{ account.role === 'teacher' ? '教师' : '学生' }}
                  </div>
                </td>
                <!-- 动态显示：仅学生角色可见 -->
                <td v-if="selectedRole === 'student'">
                  {{ account.studentNumber || '-' }}
                </td>
                <td v-if="selectedRole === 'student'">
                  {{ account.grade || '-' }}
                </td>
                <td>{{ formatDate(account.created_at) }}</td>
                <td>
                  <button 
                    @click="handleEditAccount(account)"
                    class="action-button"
                  >
                    修改
                  </button>
                  <button 
                    @click="handleDeleteAccount(account.id)"
                    class="action-button delete-button"
                  >
                    删除
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="filteredAccounts.length === 0" class="no-students">
            <div class="no-students-icon">👥</div>
            <h3>没有找到账号</h3>
            <p>请调整筛选条件后重试</p>
          </div>
        </div>
      </div>

      <!-- 学习资源推荐界面 -->
      <div v-else-if="activeTab === 'resource-recommendation'" class="empty-interface">
        <h2>学习资源推荐</h2>
        <p>学习资源推荐功能界面（内容待定）</p>
      </div>
      
      <!-- 模型存档管理界面 -->
      <div v-else-if="activeTab === 'model-archives'" class="model-archives-interface">
        <!-- 页面标题和操作区 -->
        <div class="page-header">
          <h2>模型存档管理</h2>
          <div class="header-actions">
            <button @click="showCreateArchiveModal = true" class="create-archive-button">
              ➕ 创建新存档
            </button>
          </div>
        </div>

        <!-- 存档列表 -->
        <div class="archives-list">
          <div v-if="modelArchives.length === 0" class="empty-state">
            <p>暂无存档，请创建新存档</p>
          </div>
          
          <div 
            v-for="archive in modelArchives" 
            :key="archive.id" 
            class="archive-card"
            :class="{ 'training': archive.status === 'training' }"
          >
            <div class="archive-header">
              <h3>{{ archive.name }}</h3>
              <span :class="['status-badge', archive.status]">
                {{ getStatusText(archive.status) }}
              </span>
            </div>
            
            <div class="archive-info">
              <div class="info-item">
                <span class="label">创建时间:</span>
                <span class="value">{{ archive.created_at }}</span>
              </div>
              <div class="info-item">
                <span class="label">词嵌入模型:</span>
                <span :class="['value', archive.has_word_emb ? 'success' : '']">
                  {{ archive.has_word_emb ? '✓ 已生成' : '未生成' }}
                </span>
              </div>
              <div class="info-item">
                <span class="label">诊断模型:</span>
                <span :class="['value', archive.has_diagnosis_model ? 'success' : '']">
                  {{ archive.has_diagnosis_model ? '✓ 已生成' : '未生成' }}
                </span>
              </div>
              <div class="info-item">
                <span class="label">知识点映射:</span>
                <span :class="['value', archive.has_knowledge_mapping ? 'success' : '']">
                  {{ archive.has_knowledge_mapping ? '✓ 已上传' : '未上传' }}
                </span>
              </div>
            </div>
            
            <div class="archive-actions">
              <button 
                v-if="archive.status === 'pending'" 
                @click="showUploadModal(archive)" 
                class="action-button upload"
              >
                📤 上传数据并训练
              </button>
              <button 
                v-if="archive.status === 'completed'" 
                @click="showArchiveDetail(archive)" 
                class="action-button view"
              >
                👁️ 查看详情
              </button>
              <button 
                v-if="archive.status === 'training'" 
                disabled 
                class="action-button training"
              >
                ⏳ 训练中...
              </button>
              <button 
                v-if="archive.status !== 'training'" 
                @click="confirmDeleteArchive(archive)" 
                class="action-button delete"
              >
                🗑️ 删除
              </button>
            </div>
          </div>
        </div>

        <!-- 创建存档模态框 -->
        <div v-if="showCreateArchiveModal" class="modal-overlay" @click.self="showCreateArchiveModal = false">
          <div class="modal-content create-archive-modal">
            <h3>创建新存档</h3>
            
            <!-- 存档名称 -->
            <div class="form-group">
              <label>存档名称：</label>
              <input 
                v-model="newArchiveName" 
                type="text" 
                placeholder="请输入存档名称（如：2024 届模型）"
                class="form-input"
              />
            </div>
            
            <!-- 选项卡切换 -->
            <div class="create-mode-tabs">
              <button 
                :class="['tab-button', { active: createMode === 'existing' }]"
                @click="createMode = 'existing'"
              >
                选择已有模型
              </button>
              <button 
                :class="['tab-button', { active: createMode === 'train' }]"
                @click="createMode = 'train'"
              >
                上传训练文件（测试中）
              </button>
            </div>
            
            <!-- 选项卡内容 -->
            <div class="tab-content">
              <!-- 选择已有模型 -->
              <div v-if="createMode === 'existing'" class="existing-model-section">
                <div class="form-group">
                  <label>知识点推理模型：</label>
                  <input 
                    type="file" 
                    @change="handleWord2VecModelChange" 
                    class="file-input-visible"
                  />
                </div>
                <div class="form-group">
                  <label>认知诊断模型：</label>
                  <input 
                    type="file" 
                    @change="handleDiagnosisModelChange" 
                    class="file-input-visible"
                  />
                  <p class="hint">请选择模型文件</p>
                </div>
                <div class="form-group">
                  <label>知识点对照表：</label>
                  <input 
                    type="file" 
                    @change="handleKnowledgeMappingFileChange" 
                    class="file-input-visible"
                  />
                </div>
              </div>
              
              <!-- 上传训练文件 -->
              <div v-if="createMode === 'train'" class="train-model-section">
                <div class="form-group">
                  <label>知识点对照表：</label>
                  <input 
                    type="file" 
                    @change="handleKnowledgeMappingFileChange" 
                    class="file-input-visible"
                  />
                </div>
                <div class="form-group">
                  <label>训练数据文件：</label>
                  <input 
                    type="file" 
                    @change="handleTrainDataFilesChange" 
                    multiple
                    class="file-input-visible"
                  />
                  <p class="hint">请上传包含学生答题记录的训练数据文件</p>
                </div>
              </div>
            </div>
            
            <div class="modal-footer">
              <button @click="showCreateArchiveModal = false" class="cancel-button">取消</button>
              <button @click="handleCreateArchive" class="submit-button">创建</button>
            </div>
          </div>
        </div>

        <!-- 上传数据模态框 -->
        <div v-if="showUploadModalFlag" class="modal-overlay" @click.self="showUploadModalFlag = false">
          <div class="modal-content upload-modal">
            <h3>上传训练数据 - {{ currentArchive?.name }}</h3>
            <div class="upload-section">
              <div class="form-group">
                <label>知识点映射文件 (knowledge_mapping.txt)：</label>
                <input 
                  type="file" 
                  @change="handleKnowledgeMappingChange" 
                  accept=".txt"
                  class="file-input"
                />
              </div>
              
              <div class="form-group">
                <label>训练数据文件 (JSON 格式)：</label>
                <input 
                  type="file" 
                  @change="handleDataFilesChange" 
                  accept=".json"
                  multiple
                  class="file-input"
                />
                <p class="hint">可多选，支持 train_*.json, val_*.json, test_*.json 等格式</p>
              </div>
              
              <div v-if="uploadProgress > 0" class="progress-bar">
                <div class="progress" :style="{ width: uploadProgress + '%' }"></div>
                <span class="progress-text">{{ uploadProgress }}%</span>
              </div>
            </div>
            <div class="modal-footer">
              <button @click="showUploadModalFlag = false" class="cancel-button">取消</button>
              <button @click="handleUploadFiles" class="submit-button" :disabled="isUploading">
                {{ isUploading ? '上传中...' : '开始训练' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 存档详情模态框 -->
        <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
          <div class="modal-content detail-modal">
            <h3>存档详情 - {{ currentArchive?.name }}</h3>
            <div class="detail-content">
              <div class="info-row">
                <span class="label">状态：</span>
                <span :class="['status-badge', currentArchive?.status]">
                  {{ getStatusText(currentArchive?.status) }}
                </span>
              </div>
              <div class="info-row">
                <span class="label">创建时间：</span>
                <span>{{ currentArchive?.created_at }}</span>
              </div>
              <div class="info-row">
                <span class="label">词嵌入模型：</span>
                <span>{{ currentArchive?.word_emb_path || '未生成' }}</span>
              </div>
              <div class="info-row">
                <span class="label">诊断模型：</span>
                <span>{{ currentArchive?.diagnosis_model_path || '未生成' }}</span>
              </div>
              <div class="info-row">
                <span class="label">知识点映射：</span>
                <span>{{ currentArchive?.knowledge_mapping_path || '未上传' }}</span>
              </div>
              <div v-if="currentArchive?.training_log" class="training-log">
                <h4>训练日志：</h4>
                <pre>{{ currentArchive.training_log }}</pre>
              </div>
            </div>
            <div class="modal-footer">
              <button @click="showDetailModal = false" class="cancel-button">关闭</button>
            </div>
          </div>
        </div>

        <!-- 确认删除模态框 -->
        <div v-if="showDeleteArchiveConfirm" class="modal-overlay" @click.self="showDeleteArchiveConfirm = false">
          <div class="modal-content">
            <h3>确认删除</h3>
            <p>确定要删除存档 "{{ archiveToDelete?.name }}" 吗？此操作不可恢复。</p>
            <div class="modal-footer">
              <button @click="showDeleteArchiveConfirm = false" class="cancel-button">取消</button>
              <button @click="handleDeleteArchive" class="submit-button delete-button">确认删除</button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 创建专栏模态框 -->
    <div v-if="isColumnModalVisible" class="modal-overlay">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>创建新专栏</h3>
          <button @click="closeColumnModal" class="modal-close">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">专栏名称</label>
            <input 
              v-model="newColumn.name"
              placeholder="输入专栏名称（如：第一次月考）"
              class="form-input"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">选择模型存档 <span class="required">*</span></label>
            <select v-model="newColumn.archiveId" class="form-input">
              <option value="">请选择存档</option>
              <option 
                v-for="archive in completedArchives" 
                :key="archive.id" 
                :value="archive.id"
              >
                {{ archive.name }} ({{ archive.status }})
              </option>
            </select>
            <p class="form-hint">请选择已训练完成的模型存档</p>
          </div>
          
          <div class="form-group">
            <label class="form-label">上传试题图片</label>
            <ImageUpload ref="columnImageUpload" />
          </div>

          <div class="form-group">
            <label class="form-label">
              题目知识点标注文件（可选，txt）
            </label>
            <input
              ref="humanKnowledgeFileInput"
              type="file"
              accept=".txt"
              class="form-input"
              @change="handleHumanKnowledgeFileUpload"
            />
            <p class="form-hint">格式示例：{"1":[3,4],"2":[5]} 或 1: 3,4</p>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeColumnModal" class="cancel-button" :disabled="isCreatingColumn">取消</button>
          <div class="submit-container" v-if="isCreatingColumn">
            <div class="loading-spinner"></div>
            <span>创建中，请稍候...</span>
          </div>
          <button 
            v-else
            @click="createColumn"
            class="submit-button"
            :disabled="!newColumn.name || !newColumn.archiveId"
          >
            创建专栏
          </button>
        </div>
      </div>
    </div>

    <!-- 查看/修改专栏信息模态框（图片只读） -->
    <div v-if="isColumnInfoModalVisible" class="modal-overlay" @click.self="closeColumnInfoModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>专栏信息</h3>
          <button @click="closeColumnInfoModal" class="modal-close">×</button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">专栏名称</label>
            <input
              v-model="editingColumn.name"
              placeholder="输入专栏名称（如：第一次月考）"
              class="form-input"
            >
          </div>

          <div class="form-group">
            <label class="form-label">选择模型存档 <span class="required">*</span></label>
            <select v-model="editingColumn.archiveId" class="form-input">
              <option value="">请选择存档</option>
              <option
                v-for="archive in completedArchives"
                :key="archive.id"
                :value="archive.id"
              >
                {{ archive.name }} ({{ archive.status }})
              </option>
            </select>
            <p class="form-hint">可修改专栏使用的模型存档</p>
          </div>

          <div class="form-group">
            <label class="form-label">试题图片（仅查看）</label>
            <div v-if="editingColumn.imageUrls.length > 0" class="readonly-images-grid">
              <div
                v-for="(url, idx) in editingColumn.imageUrls"
                :key="url + idx"
                class="readonly-image-item"
              >
                <img
                  :src="url"
                  class="readonly-image"
                  :alt="`试题图片${idx + 1}`"
                  title="点击放大"
                  @click="openColumnImagePreview(url)"
                >
                <div class="readonly-image-index">第 {{ idx + 1 }} 张</div>
              </div>
            </div>
            <div v-else class="no-readonly-images">暂无已上传图片</div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeColumnInfoModal" class="cancel-button" :disabled="isUpdatingColumn">关闭</button>
          <div class="submit-container" v-if="isUpdatingColumn">
            <div class="loading-spinner"></div>
            <span>保存中...</span>
          </div>
          <button
            v-else
            @click="saveColumnInfo"
            class="submit-button"
            :disabled="!editingColumn.name || !editingColumn.archiveId"
          >
            保存修改
          </button>
        </div>
      </div>
    </div>

    <!-- 专栏图片放大预览（只读） -->
    <div
      v-if="isColumnImagePreviewVisible"
      class="image-preview-overlay"
      @click.self="closeColumnImagePreview"
    >
      <div class="image-preview-modal" @click.stop>
        <button class="image-preview-close" @click="closeColumnImagePreview" type="button">×</button>
        <img :src="columnImagePreviewUrl" class="image-preview-img" alt="专栏试题图片预览">
      </div>
    </div>
    
    <!-- 编辑账号模态框 -->
    <div v-if="isEditAccountModalVisible" class="modal-overlay">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>修改账号信息</h3>
          <button @click="closeEditAccountModal" class="modal-close">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input 
              v-model="editingAccount.username"
              placeholder="输入用户名"
              class="form-input"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">密码</label>
            <input 
              v-model="editingAccount.password"
              type="password"
              placeholder="输入密码（留空则不修改）"
              class="form-input"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">角色</label>
            <div class="role-options">
              <label 
                :class="['role-option', { active: editingAccount.role === 'student' }]"
                @click="editingAccount.role = 'student'"
              >
                <input 
                  type="radio" 
                  name="editAccountRole" 
                  value="student" 
                  v-model="editingAccount.role"
                >
                <span>学生</span>
              </label>
              <label 
                :class="['role-option', { active: editingAccount.role === 'teacher' }]"
                @click="editingAccount.role = 'teacher'"
              >
                <input 
                  type="radio" 
                  name="editAccountRole" 
                  value="teacher" 
                  v-model="editingAccount.role"
                >
                <span>教师</span>
              </label>
            </div>
          </div>
          
          <!-- 学生额外信息 -->
          <div v-if="editingAccount.role === 'student'" class="student-extra-info">
            <div class="form-group">
              <label class="form-label">姓名</label>
              <input 
                v-model="editingAccount.name"
                placeholder="输入学生姓名"
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">班级</label>
              <input 
                v-model="editingAccount.grade"
                placeholder="输入学生班级（如：高三(1)班）"
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">学号</label>
              <input 
                v-model="editingAccount.studentNumber"
                placeholder="输入学生学号"
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">特点（可选）</label>
              <textarea 
                v-model="editingAccount.features"
                placeholder="输入学生特点描述"
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeEditAccountModal" class="cancel-button">取消</button>
          <button 
            @click="updateAccount"
            class="submit-button"
            :disabled="!editingAccount.username || !editingAccount.role || (editingAccount.role === 'student' && (!editingAccount.name || !editingAccount.grade || !editingAccount.studentNumber))"
          >
            保存修改
          </button>
        </div>
      </div>
    </div>
    
    <!-- 批量添加账号模态框 -->
    <div v-if="isBatchAddModalVisible" class="modal-overlay">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>批量添加账号</h3>
          <div class="modal-header-actions">
            <button @click="downloadTemplate" class="download-template-button">
              📥 下载模板
            </button>
            <button @click="closeBatchAddModal" class="modal-close">×</button>
          </div>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">上传Excel文件</label>
            <div class="file-upload-area">
              <input 
                ref="fileInput"
                type="file"
                accept=".xlsx, .xls"
                class="file-input"
                @change="handleFileUpload"
              >
              <div class="upload-content">
                <div class="upload-icon">📁</div>
                <h3>拖拽文件到这里，或</h3>
                <button @click="openFileDialog" class="browse-button">
                  <i class="browse-icon">📂</i> 浏览文件
                </button>
                <p class="upload-hint">支持 .xlsx, .xls 格式</p>
              </div>
              <div v-if="selectedFile" class="file-info">
                <span class="file-name">{{ selectedFile.name }}</span>
                <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeBatchAddModal" class="cancel-button">取消</button>
          <button 
            @click="uploadBatchAccounts"
            class="submit-button"
            :disabled="!selectedFile"
          >
            上传并处理
          </button>
        </div>
      </div>
    </div>

    <!-- 添加账号模态框 -->
    <div v-if="isAddAccountModalVisible" class="modal-overlay">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>添加新账号</h3>
          <button @click="closeAddAccountModal" class="modal-close">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input 
              v-model="newAccount.username"
              placeholder="输入用户名"
              class="form-input"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">密码</label>
            <input 
              v-model="newAccount.password"
              type="password"
              placeholder="输入密码"
              class="form-input"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">角色</label>
            <div class="role-options">
              <label 
                :class="['role-option', { active: newAccount.role === 'student' }]"
                @click="newAccount.role = 'student'"
              >
                <input 
                  type="radio" 
                  name="accountRole" 
                  value="student" 
                  v-model="newAccount.role"
                >
                <span>学生</span>
              </label>
              <label 
                :class="['role-option', { active: newAccount.role === 'teacher' }]"
                @click="newAccount.role = 'teacher'"
              >
                <input 
                  type="radio" 
                  name="accountRole" 
                  value="teacher" 
                  v-model="newAccount.role"
                >
                <span>教师</span>
              </label>
            </div>
          </div>
          
          <!-- 学生额外信息 -->
          <div v-if="newAccount.role === 'student'" class="student-extra-info">
            <div class="form-group">
              <label class="form-label">姓名</label>
              <input 
                v-model="newAccount.name"
                placeholder="输入学生姓名"
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">班级</label>
              <input 
                v-model="newAccount.grade"
                placeholder="输入学生班级（如：高三(1)班）"
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">学号</label>
              <input 
                v-model="newAccount.studentNumber"
                placeholder="输入学生学号"
                class="form-input"
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">特点（可选）</label>
              <textarea 
                v-model="newAccount.features"
                placeholder="输入学生特点描述"
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeAddAccountModal" class="cancel-button">取消</button>
          <button 
            @click="addAccount"
            class="submit-button"
            :disabled="!newAccount.username || !newAccount.password || !newAccount.role || (newAccount.role === 'student' && (!newAccount.name || !newAccount.grade || !newAccount.studentNumber))"
          >
            添加账号
          </button>
        </div>
      </div>
    </div>

    <!-- 生成评语模态框 -->
    <SimpleModal 
      :isVisible="isCommentModalVisible" 
      :title="isEditingComment ? `修改评语 - ${selectedStudent?.name}` : `生成评语 - ${selectedStudent?.name}`"
      @close="closeCommentModal"
    >
      <div class="comment-generation-section">
        <!-- 图像上传 -->
        <div class="image-upload-section">
          <h4>上传试题截图</h4>
          <ImageUpload ref="imageUpload" :key="imageUploadKey" :student-id="selectedStudentId" :column-id="selectedColumnId" />
        </div>
        
        <!-- 评语风格选择 -->
        <div class="style-selection-section">
          <h4>选择评语风格</h4>
          <div class="style-options">
            <label 
              :class="['style-option', { active: selectedStyle === 'encouraging' }]"
              @click="selectedStyle = 'encouraging'"
            >
              <input 
                type="radio" 
                name="style" 
                value="encouraging" 
                v-model="selectedStyle"
              >
              <span>鼓励型</span>
            </label>
            <label 
              :class="['style-option', { active: selectedStyle === 'detailed' }]"
              @click="selectedStyle = 'detailed'"
            >
              <input 
                type="radio" 
                name="style" 
                value="detailed" 
                v-model="selectedStyle"
              >
              <span>详细型</span>
            </label>
            <label 
              :class="['style-option', { active: selectedStyle === 'concise' }]"
              @click="selectedStyle = 'concise'"
            >
              <input 
                type="radio" 
                name="style" 
                value="concise" 
                v-model="selectedStyle"
              >
              <span>简洁型</span>
            </label>
          </div>
        </div>
        
        <!-- 附加评语输入 -->
        <div class="addition-section">
          <h4>附加评语（可选）</h4>
          <textarea 
            v-model="additionComment" 
            class="addition-textarea"
            placeholder="请输入额外的评语信息..."
            rows="5"
          ></textarea>
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="closeCommentModal" class="cancel-button">关闭</button>
        <button 
          @click="generateComment"
          class="submit-button"
          :disabled="!selectedStudentId || !selectedColumnId || imageUpload.value?.previewImages.length === 0 || isGenerating"
        >
          {{ isGenerating ? '处理中...' : (isEditingComment ? '确定修改' : '生成评语') }}
        </button>
      </div>
    </SimpleModal>

    <!-- 存储中弹窗 -->
    <div v-if="isStoring" class="storing-overlay">
      <div class="storing-modal">
        <div class="storing-content">
          <div class="spinner"></div>
          <h3>存储中...</h3>
          <p>正在处理图片和生成评语，请稍候...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store/auth';
import { getStudents } from '../api/students';
import { getColumns, getColumnById, addColumn, deleteColumn, updateColumn } from '../api/columns';
import { generateComment as apiGenerateComment, getStudentComments, createComment as apiCreateComment, deleteComment as apiDeleteComment } from '../api/comments';
import { uploadImage } from '../api/images';
import { getAccounts, addAccount as apiAddAccount, deleteAccount as apiDeleteAccount, updateAccount as apiUpdateAccount, batchAddAccounts as apiBatchAddAccounts } from '../api/accounts';
import { getArchives, createArchive, createArchiveWithFiles, uploadArchiveFiles, getArchiveDetail, deleteArchive } from '../api/archives';
import ImageUpload from '../components/ImageUpload.vue';
import SimpleModal from '../components/SimpleModal.vue';

const router = useRouter();

// 获取当前用户信息
const store = useAuthStore();
const currentUser = computed(() => store.user);

// 退出登录
const logout = () => {
  store.logout();
  router.push('/login');
};

// 学生数据
const students = ref([]);
const columns = ref([]);

// 标签页管理
const activeTab = ref('comment-management');

// 筛选条件
const selectedColumnId = ref('');
const selectedClass = ref('');
const searchKeyword = ref('');

// 专栏模态框
const isColumnModalVisible = ref(false);
const isCreatingColumn = ref(false);
const newColumn = ref({ name: '', archiveId: '' });
const columnImageUpload = ref(null);
const humanKnowledgeFileForCreate = ref(null);
const humanKnowledgeFileInput = ref(null);

// 查看/修改专栏信息（图片只读）
const isColumnInfoModalVisible = ref(false);
const isUpdatingColumn = ref(false);
const editingColumn = ref({
  id: '',
  name: '',
  archiveId: '',
  imageUrls: []
});

// 专栏图片放大预览（只读）
const isColumnImagePreviewVisible = ref(false);
const columnImagePreviewUrl = ref('');

// 模型存档数据
const completedArchives = ref([]);

// 模型存档管理相关变量
const modelArchives = ref([]);
const showCreateArchiveModal = ref(false);
const newArchiveName = ref('');
const createMode = ref('existing'); // 'existing' 或 'train'
const showUploadModalFlag = ref(false);
const currentArchive = ref(null);
const showDetailModal = ref(false);
const showDeleteArchiveConfirm = ref(false);
const archiveToDelete = ref(null);
const knowledgeMappingFile = ref(null);
const dataFiles = ref([]);
const isUploading = ref(false);
const uploadProgress = ref(0);

// 创建存档 - 选择已有模型
const word2VecModelFile = ref(null);
const diagnosisModelFiles = ref([]);
const knowledgeMappingFileForCreate = ref(null);

// 创建存档 - 上传训练文件
const trainDataFiles = ref([]);
const knowledgeMappingFileForTrain = ref(null);

// 评语模态框
const isCommentModalVisible = ref(false);
// 测试简单模态框
const isSimpleModalVisible = ref(false);
// 查看评语模态框
const isViewCommentModalVisible = ref(false);
// 查看评语的内容
const viewCommentContent = ref('');
// 查看评语的学生反馈
const viewCommentFeedback = ref('');
// 修改评语模式
const isEditingComment = ref(false);

// 批量生成评语
const selectedStudents = ref([]);
const selectAllStudents = ref(false);
const isBatchCommentModalVisible = ref(false);
const batchStudents = ref([]);
const currentBatchIndex = ref(0);
const batchAdditionComments = ref([]);
const batchImagePaths = ref([]); // 存储每个学生的图片路径
const batchImageUploadKey = ref(0);
const isBatchGenerating = ref(false);
// 当前查看的评语对象
const currentViewingComment = ref(null);

const selectedStudent = ref(null);
const selectedStudentId = ref(null);
const selectedStyle = ref('encouraging');
const additionComment = ref('');
const currentComment = ref(null);
const isGenerating = ref(false);
const isStoring = ref(false);

// 图片上传
const imageUpload = ref(null);
const batchImageUploads = ref(null);
const uploadedImages = ref([]);
const previewImages = ref([]);
const imageUploadKey = ref(0);

// 缓存专栏题目图片数量，避免每次都请求
const columnImageCountCache = ref(new Map());
const getColumnImageCount = async (columnId) => {
  if (!columnId) return 0;
  const key = String(columnId);
  if (columnImageCountCache.value.has(key)) {
    return columnImageCountCache.value.get(key);
  }
  const resp = await getColumnById(columnId);
  if (!resp?.success || !resp?.data) {
    // 获取失败时不阻断流程，返回0表示无法校验
    return 0;
  }
  const col = resp.data;
  const paths = [
    col.questionImagePath1,
    col.questionImagePath2,
    col.questionImagePath3,
    col.questionImagePath4,
    col.questionImagePath5,
    col.questionImagePath6
  ].filter(p => p && String(p).trim() !== '' && String(p).trim() !== '无');
  const count = paths.length;
  columnImageCountCache.value.set(key, count);
  return count;
};

const getImageUploadSelectedCount = (uploadRefValue) => {
  const previewImagesMaybeRef = uploadRefValue?.previewImages;
  if (Array.isArray(previewImagesMaybeRef)) return previewImagesMaybeRef.length;
  const v = previewImagesMaybeRef?.value;
  if (Array.isArray(v)) return v.length;
  return 0;
};

// 账号管理
const accounts = ref([]);
const selectedRole = ref('');
const accountSearchKeyword = ref('');
const selectedAccountClass = ref(''); // 新增：账号管理的班级筛选
const isAddAccountModalVisible = ref(false);
const isEditAccountModalVisible = ref(false);
const isBatchAddModalVisible = ref(false);
const isDeleteConfirmVisible = ref(false);
const deleteConfirmMessage = ref('');
const accountToDelete = ref('');
const newAccount = ref({ 
  username: '', 
  password: '', 
  role: '',
  // 学生额外信息
  name: '',
  grade: '',
  studentNumber: '',
  features: ''
});
const editingAccount = ref({ 
  id: '',
  username: '', 
  password: '', 
  role: '',
  // 学生额外信息
  name: '',
  grade: '',
  studentNumber: '',
  features: ''
});

// 批量添加账号
const fileInput = ref(null);
const selectedFile = ref(null);
const batchAddResult = ref(null);

// 计算账号管理中的班级列表
const accountClassList = computed(() => {
  const classes = new Set();
  accounts.value.forEach(account => {
    if (account.role === 'student' && account.grade) {
      classes.add(account.grade);
    }
  });
  return Array.from(classes);
});

// 计算班级列表
const classList = computed(() => {
  const classes = new Set();
  students.value.forEach(student => classes.add(student.className));
  return Array.from(classes);
});

// 删除专栏
// 查看评语
const handleViewComment = (student, comment) => {
  viewCommentContent.value = comment.content;
  viewCommentFeedback.value = comment.feedback || '';
  currentViewingComment.value = comment;
  isViewCommentModalVisible.value = true;
};

// 修改评语
const handleEditComment = () => {
  if (!currentViewingComment.value) return;
  
  // 关闭查看评语模态框
  isViewCommentModalVisible.value = false;
  
  // 设置修改模式
  isEditingComment.value = true;
  
  // 查找对应的学生
  const student = students.value.find(s => s.id === currentViewingComment.value.studentId);
  if (student) {
    selectedStudent.value = student;
    selectedStudentId.value = student.id;
  }
  
  // 设置专栏ID
  selectedColumnId.value = currentViewingComment.value.columnId;
  
  // 加载当前评语的附加评语
  additionComment.value = currentViewingComment.value.addition || '';
  
  // 更新key强制重新渲染ImageUpload组件
  imageUploadKey.value++;
  
  // 打开生成评语模态框
  isCommentModalVisible.value = true;
};

// 生成评语按钮点击方法已统一为handleStudentAction，此处不再重复定义

const deleteSelectedColumn = async () => {
  if (!selectedColumnId.value || !confirm('确定要删除这个专栏以及其相关信息吗？此操作不可恢复。')) {
    return;
  }
  
  try {
    await deleteColumn(selectedColumnId.value);
    
    // 更新专栏列表
    columns.value = columns.value.filter(column => column.id !== selectedColumnId.value);
    
    // 重新选择第一个专栏或清空选择
    if (columns.value.length > 0) {
      selectedColumnId.value = columns.value[0].id;
    } else {
      selectedColumnId.value = '';
    }
    
    // 重新加载学生数据
    await loadStudents();
    
    alert('专栏删除成功！');
  } catch (error) {
    console.error('删除专栏失败:', error);
    alert('删除专栏失败，请重试');
  }
};

// 筛选后的学生列表
const filteredStudents = computed(() => {
  return students.value.filter(student => {
    // 班级筛选
    if (selectedClass.value && student.className !== selectedClass.value) {
      return false;
    }
    
    // 搜索筛选
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase();
      return (
        student.name.toLowerCase().includes(keyword) ||
        student.studentId.toLowerCase().includes(keyword)
      );
    }
    
    return true;
  });
});

// 筛选后的账号列表
const filteredAccounts = computed(() => {
  return accounts.value.filter(account => {
    // 角色筛选
    if (selectedRole.value && account.role !== selectedRole.value) {
      return false;
    }
    
    // 班级筛选（仅学生角色）
    if (selectedRole.value === 'student' && selectedAccountClass.value && account.grade !== selectedAccountClass.value) {
      return false;
    }
    
    // 搜索筛选
    if (accountSearchKeyword.value) {
      const keyword = accountSearchKeyword.value.toLowerCase();
      return account.username.toLowerCase().includes(keyword);
    }
    
    return true;
  });
});

// 获取学生在特定专栏的评语
const getStudentColumnComment = (studentId, columnId) => {
  if (!columnId) return null;
  
  const strStudentId = String(studentId);
  const strColumnId = String(columnId);
  
  const student = students.value.find(s => String(s.id) === strStudentId);
  if (!student || !student.comments || student.comments.length === 0) {
    return null;
  }
  
  return student.comments.find(comment => String(comment.columnId) === strColumnId) || null;
};

// 处理学生操作(生成评语)
const handleStudentAction = (student) => {
  selectedStudent.value = student;
  selectedStudentId.value = student.id;
  
  if (selectedColumnId.value) {
    currentComment.value = getStudentColumnComment(student.id, selectedColumnId.value);
  } else {
    currentComment.value = null;
  }
  
  selectedStyle.value = 'encouraging';
  isEditingComment.value = false;
  imageUploadKey.value++;
  isCommentModalVisible.value = true;
};

// 全选/取消全选
const handleSelectAll = () => {
  if (selectAllStudents.value) {
    selectedStudents.value = filteredStudents.value.map(student => student.id);
  } else {
    selectedStudents.value = [];
  }
};

// 批量生成评语按钮点击
const handleBatchGenerate = () => {
  if (!selectedColumnId.value || selectedStudents.value.length === 0) return;
  
  // 获取选中的学生
  batchStudents.value = filteredStudents.value.filter(student => 
    selectedStudents.value.includes(student.id)
  );
  
  // 初始化附加评语数组和图片路径数组
  batchAdditionComments.value = new Array(batchStudents.value.length).fill('');
  batchImagePaths.value = new Array(batchStudents.value.length).fill([]);
  
  // 重置当前索引
  currentBatchIndex.value = 0;
  
  // 打开批量生成模态框
  isBatchCommentModalVisible.value = true;
};

// 关闭批量生成模态框
const closeBatchCommentModal = () => {
  isBatchCommentModalVisible.value = false;
  batchStudents.value = [];
  batchAdditionComments.value = [];
  batchImagePaths.value = [];
  currentBatchIndex.value = 0;
};

// 导航批量模态框
const navigateBatchModal = async (direction) => {
  // 保存当前学生的图片
  if (batchImageUploads.value) {
    try {
      const uploadedImages = await batchImageUploads.value.uploadImages(true);
      const imagePaths = uploadedImages.map(img => {
        if (img.path && img.path.startsWith('http://localhost:5000/')) {
          return img.path.replace('http://localhost:5000/', '');
        }
        return img.path;
      });
      batchImagePaths.value[currentBatchIndex.value] = imagePaths;
      console.log(`[批量生成] 保存学生 ${batchStudents.value[currentBatchIndex.value].name} 的图片:`, imagePaths);
    } catch (error) {
      console.error(`[批量生成] 保存当前学生图片失败:`, error);
    }
  }
  
  const newIndex = currentBatchIndex.value + direction;
  if (newIndex >= 0 && newIndex < batchStudents.value.length) {
    currentBatchIndex.value = newIndex;
    batchImageUploadKey.value++;
  }
};

// 获取当前批量学生
const currentBatchStudent = computed(() => {
  return batchStudents.value[currentBatchIndex.value] || null;
});

// 批量生成评语
const generateBatchComments = async () => {
  if (!selectedColumnId.value || batchStudents.value.length === 0) return;
  
  isBatchGenerating.value = true;
  
  try {
    // ====== 前置校验：专栏图片数 vs 批量上传图片数（立即提示，不阻断后续生成） ======
    const columnCount = await getColumnImageCount(selectedColumnId.value);
    if (columnCount > 0) {
      // 先保存当前页面学生的图片（确保 batchImagePaths 最新），再做校验
      if (batchImageUploads.value) {
        try {
          const uploadedImages = await batchImageUploads.value.uploadImages(true);
          const imagePaths = uploadedImages.map(img => {
            if (img.path && img.path.startsWith('http://localhost:5000/')) {
              return img.path.replace('http://localhost:5000/', '');
            }
            return img.path;
          });
          batchImagePaths.value[currentBatchIndex.value] = imagePaths;
        } catch (error) {
          console.error(`[批量生成] 前置校验阶段保存当前学生图片失败:`, error);
        }
      }

      const earlyWarnings = [];
      for (let i = 0; i < batchStudents.value.length; i++) {
        const student = batchStudents.value[i];
        const imagePaths = batchImagePaths.value[i] || [];
        const studentCount = (imagePaths || []).filter(p => p && String(p).trim() !== '' && String(p).trim() !== '无').length;
        if (studentCount !== columnCount) {
          earlyWarnings.push(`${student.name}: 专栏 ${columnCount} 张，已上传 ${studentCount} 张`);
        }
      }
      if (earlyWarnings.length > 0) {
        alert(`注意：检测到上传图片数量与专栏不一致，已终止批量生成。\n\n${earlyWarnings.join('\n')}`);
        return;
      }
    }

    // 先保存当前学生的图片（如果是最后一个学生）
    if (batchImageUploads.value) {
      try {
        const uploadedImages = await batchImageUploads.value.uploadImages(true);
        const imagePaths = uploadedImages.map(img => {
          if (img.path && img.path.startsWith('http://localhost:5000/')) {
            return img.path.replace('http://localhost:5000/', '');
          }
          return img.path;
        });
        batchImagePaths.value[currentBatchIndex.value] = imagePaths;
        console.log(`[批量生成] 保存最后一个学生 ${batchStudents.value[currentBatchIndex.value].name} 的图片:`, imagePaths);
      } catch (error) {
        console.error(`[批量生成] 保存最后一个学生图片失败:`, error);
      }
    }
    
    // 并行处理，每次处理2-3个学生
    const batchSize = 2;
    const totalBatches = Math.ceil(batchStudents.value.length / batchSize);
    const mismatchWarnings = [];
    
    for (let i = 0; i < totalBatches; i++) {
      const start = i * batchSize;
      const end = Math.min(start + batchSize, batchStudents.value.length);
      const batch = batchStudents.value.slice(start, end);
      
      // 并行处理当前批次
      const batchPromises = batch.map(async (student, index) => {
        const studentIndex = start + index;
        const addition = batchAdditionComments.value[studentIndex] || '';
        
        // 获取该学生的图片路径
        const imagePaths = batchImagePaths.value[studentIndex] || [];
        console.log(`[批量生成] 学生 ${student.name} 使用图片:`, imagePaths);
        
        // 准备数据
        const commentData = {
          studentId: student.id,
          columnId: selectedColumnId.value,
          style: 'encouraging',
          imagePaths: imagePaths,
          addition: addition
        };
        
        // 生成评语
        const result = await apiGenerateComment(commentData);
        
        return result;
      });
      
      // 等待当前批次完成
      await Promise.all(batchPromises);
    }
    
    // 重新加载学生数据
    await loadStudents();
    
    // 关闭模态框
    closeBatchCommentModal();
    
    alert('批量生成评语成功！');
  } catch (error) {
    console.error('批量生成评语失败:', error);
    alert('批量生成评语失败，请重试');
  } finally {
    isBatchGenerating.value = false;
  }
};

// 关闭专栏模态框
const closeColumnModal = () => {
  newColumn.value = { name: '', archiveId: '' };
  isColumnModalVisible.value = false;
  humanKnowledgeFileForCreate.value = null;
  if (humanKnowledgeFileInput.value) {
    humanKnowledgeFileInput.value.value = '';
  }
};

const closeColumnInfoModal = () => {
  isColumnInfoModalVisible.value = false;
  isUpdatingColumn.value = false;
  editingColumn.value = { id: '', name: '', archiveId: '', imageUrls: [] };
};

const openColumnImagePreview = (url) => {
  if (!url) return;
  columnImagePreviewUrl.value = url;
  isColumnImagePreviewVisible.value = true;
};

const closeColumnImagePreview = () => {
  isColumnImagePreviewVisible.value = false;
  columnImagePreviewUrl.value = '';
};

const openColumnInfoModal = async () => {
  if (!selectedColumnId.value) return;
  try {
    isUpdatingColumn.value = true;
    const resp = await getColumnById(selectedColumnId.value);
    if (!resp?.success) {
      alert(resp?.message || '获取专栏信息失败');
      return;
    }
    const col = resp.data;
    const paths = [
      col.questionImagePath1,
      col.questionImagePath2,
      col.questionImagePath3,
      col.questionImagePath4,
      col.questionImagePath5,
      col.questionImagePath6
    ].filter(p => p && String(p).trim() !== '');

    editingColumn.value = {
      id: col.id,
      name: col.name,
      archiveId: col.archiveId ? String(col.archiveId) : '',
      imageUrls: paths.map(p => (String(p).startsWith('http') ? String(p) : `http://localhost:5000/${String(p).replace(/^\//, '')}`))
    };
    isColumnInfoModalVisible.value = true;
  } catch (e) {
    console.error('获取专栏信息失败:', e);
    alert('获取专栏信息失败，请重试');
  } finally {
    isUpdatingColumn.value = false;
  }
};

const saveColumnInfo = async () => {
  if (!editingColumn.value.id) return;
  if (!editingColumn.value.name || !editingColumn.value.archiveId) return;
  isUpdatingColumn.value = true;
  try {
    const resp = await updateColumn(editingColumn.value.id, {
      name: editingColumn.value.name,
      archiveId: editingColumn.value.archiveId
    });
    if (!resp?.success) {
      alert(resp?.message || '保存失败，请重试');
      return;
    }

    const updated = resp.data;
    const idx = columns.value.findIndex(c => String(c.id) === String(updated.id));
    if (idx !== -1) {
      columns.value[idx] = { ...columns.value[idx], ...updated };
    }
    closeColumnInfoModal();
    alert('专栏信息已更新');
  } catch (e) {
    console.error('保存专栏信息失败:', e);
    alert('保存失败，请重试');
  } finally {
    isUpdatingColumn.value = false;
  }
};

// 关闭评语模态框
const closeCommentModal = () => {
  selectedStudent.value = null;
  selectedStudentId.value = null;
  currentComment.value = null;
  selectedStyle.value = 'encouraging';
  // 清空附加评语
  additionComment.value = '';
  // 重置修改模式
  isEditingComment.value = false;
  
  // 清空ImageUpload组件的预览图片
  if (imageUpload.value) {
    imageUpload.value.clearAll();
  }
  
  isCommentModalVisible.value = false;
  isGenerating.value = false;
};

// 关闭添加账号模态框
const closeAddAccountModal = () => {
  isAddAccountModalVisible.value = false;
  newAccount.value = { 
    username: '', 
    password: '', 
    role: '',
    // 学生额外信息
    name: '',
    grade: '',
    studentNumber: '',
    features: ''
  };
};

// 切换功能标签页
const switchTab = (tabName) => {
  activeTab.value = tabName;
};

// 添加账号
const addAccount = async () => {
  if (!newAccount.value.username || !newAccount.value.password || !newAccount.value.role) {
    return;
  }
  
  try {
    const accountData = {
      username: newAccount.value.username,
      password: newAccount.value.password,
      role: newAccount.value.role,
      // 如果是学生，添加额外信息
      ...(newAccount.value.role === 'student' && {
        name: newAccount.value.name,
        grade: newAccount.value.grade,
        studentNumber: newAccount.value.studentNumber,
        features: newAccount.value.features
      })
    };
    
    const result = await apiAddAccount(accountData);
    if (result) {
      accounts.value.push(result);
      closeAddAccountModal();
      alert('账号添加成功');
    }
  } catch (error) {
    console.error('添加账号失败:', error);
    alert('添加账号失败，请重试');
  }
};

// 打开修改账号模态框
const handleEditAccount = (account) => {
  // 填充当前账号信息到编辑表单
  editingAccount.value = {
    id: account.id,
    username: account.username,
    password: '', // 密码留空，需要重新输入才会修改
    role: account.role,
    name: account.name,
    grade: account.grade,
    studentNumber: account.studentNumber,
    features: account.features
  };
  // 显示编辑模态框
  isEditAccountModalVisible.value = true;
};

// 关闭修改账号模态框
const closeEditAccountModal = () => {
  isEditAccountModalVisible.value = false;
  // 重置编辑表单
  editingAccount.value = {
    id: '',
    username: '',
    password: '',
    role: '',
    name: '',
    grade: '',
    studentNumber: '',
    features: ''
  };
};

// 关闭批量添加账号模态框
const closeBatchAddModal = () => {
  isBatchAddModalVisible.value = false;
  selectedFile.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

// 下载模板
const downloadTemplate = () => {
  // 调用后端API下载模板文件
  window.location.href = 'http://localhost:5000/api/accounts/template';
};

// 打开文件选择对话框
const openFileDialog = () => {
  fileInput.value?.click();
};

// 处理文件上传
const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    selectedFile.value = file;
  }
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

// 上传批量账号
const uploadBatchAccounts = async () => {
  if (!selectedFile.value) return;
  
  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    
    const result = await apiBatchAddAccounts(formData);
    if (result) {
      batchAddResult.value = result;
      // 刷新账号列表
      loadAccounts();
      // 关闭模态框
      closeBatchAddModal();
      alert(`批量添加成功！共添加 ${result.successCount} 个账号，失败 ${result.failureCount} 个账号`);
    }
  } catch (error) {
    console.error('批量添加账号失败:', error);
    alert('批量添加账号失败，请重试');
  }
};

// 更新账号信息
const updateAccount = async () => {
  // 验证表单
  if (!editingAccount.value.username || !editingAccount.value.role) {
    alert('用户名和角色不能为空');
    return;
  }
  
  if (editingAccount.value.role === 'student' && (!editingAccount.value.name || !editingAccount.value.grade || !editingAccount.value.studentNumber)) {
    alert('学生账号需要填写姓名、班级和学号');
    return;
  }
  
  try {
    // 调用API更新账号
    await apiUpdateAccount(editingAccount.value);
    
    // 更新本地账号列表
    const index = accounts.value.findIndex(acc => acc.id === editingAccount.value.id);
    if (index !== -1) {
      accounts.value[index] = {
        ...accounts.value[index],
        ...editingAccount.value,
        password: undefined // 不保存密码到本地
      };
    }
    
    alert('账号更新成功');
    closeEditAccountModal();
  } catch (error) {
    console.error('更新账号失败:', error);
    alert('更新账号失败，请重试');
  }
};

// 显示删除确认模态框
const handleDeleteAccount = (id) => {
  accountToDelete.value = id;
  deleteConfirmMessage.value = '确定要删除这个账号吗？此操作不可恢复。';
  isDeleteConfirmVisible.value = true;
};

// 确认删除账号
const confirmDelete = async () => {
  try {
    await apiDeleteAccount(accountToDelete.value);
    accounts.value = accounts.value.filter(account => account.id !== accountToDelete.value);
    alert('账号删除成功');
  } catch (error) {
    console.error('删除账号失败:', error);
    alert('删除账号失败，请重试');
  } finally {
    // 关闭模态框
    isDeleteConfirmVisible.value = false;
    // 重置删除信息
    accountToDelete.value = '';
    deleteConfirmMessage.value = '';
  }
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};





// 加载学生数据
const loadStudents = async () => {
  try {
    const studentsResp = await getStudents();
    const studentsData = studentsResp?.success ? (studentsResp.data || []) : [];
    for (const student of studentsData) {
      const commentsResp = await getStudentComments(student.id);
      student.comments = commentsResp?.success ? (commentsResp.data || []) : [];
    }
    students.value = studentsData;
  } catch (error) {
    console.error('加载学生数据失败:', error);
  }
};

// 加载专栏数据
const loadColumns = async () => {
  try {
    const columnsResp = await getColumns();
    const columnsData = columnsResp?.success ? (columnsResp.data || []) : [];
    columns.value = columnsData;
    // 默认选择第一个专栏
    if (columns.value.length > 0) {
      selectedColumnId.value = columns.value[0].id;
    }
  } catch (error) {
    console.error('加载专栏数据失败:', error);
  }
};

// 加载账号数据
const loadAccounts = async () => {
  try {
    const accountsResp = await getAccounts();
    accounts.value = accountsResp?.success ? (accountsResp.data || []) : [];
  } catch (error) {
    console.error('加载账号数据失败:', error);
  }
};

// 处理题目知识点标注文件选择（创建专栏用）
const handleHumanKnowledgeFileUpload = (event) => {
  const file = event?.target?.files?.[0] || null;
  humanKnowledgeFileForCreate.value = file;
};

// 创建专栏
const createColumn = async () => {
  if (!newColumn.value.name) {
    alert('请输入专栏名称');
    return;
  }
  
  if (!newColumn.value.archiveId) {
    alert('请选择模型存档');
    return;
  }
  
  isCreatingColumn.value = true;
  try {
    // 准备专栏数据
    const columnData = {
      name: newColumn.value.name,
      archiveId: newColumn.value.archiveId,
      teacherId: 1 // 默认教师 ID 为 1
    };

    // 可选：题目知识点标注文件（txt）
    if (humanKnowledgeFileForCreate.value) {
      columnData.humanKnowledgeFile = humanKnowledgeFileForCreate.value;
    }
    
    // 获取预览图片的文件对象
    if (columnImageUpload.value) {
      const imageFiles = columnImageUpload.value.getPreviewFiles();
      if (imageFiles.length > 0) {
        columnData.imageFiles = imageFiles;
      }
    }
    
    // 创建专栏
    const result = await addColumn(columnData);
    if (result?.success) {
      columns.value.push(result.data);
      newColumn.value = { name: '', archiveId: '' };
      isColumnModalVisible.value = false;
      humanKnowledgeFileForCreate.value = null;
      if (humanKnowledgeFileInput.value) {
        humanKnowledgeFileInput.value.value = '';
      }
      // 清空图片上传组件的预览
      if (columnImageUpload.value) {
        columnImageUpload.value.clearAll();
      }
    } else {
      alert(result?.message || '创建专栏失败，请重试');
    }
  } catch (error) {
    console.error('创建专栏失败:', error);
    alert('创建专栏失败，请重试');
  } finally {
    isCreatingColumn.value = false;
  }
};

// 生成评语
const generateComment = async () => {
  if (!selectedStudentId.value || !selectedColumnId.value) return;
  
  // ====== 前置校验：专栏图片数 vs 当前选择上传数（立即提示，不阻断后续生成） ======
  try {
    const columnCount = await getColumnImageCount(selectedColumnId.value);
    // 这里使用“预览区已选择的图片数”，因为 uploadImages() 会清空预览
    const selectedCount = getImageUploadSelectedCount(imageUpload.value);
    if (columnCount > 0 && selectedCount !== columnCount) {
      alert(`注意：当前专栏有 ${columnCount} 张试题图片，但你选择上传了 ${selectedCount} 张答案图片，请检查上传图片数量是否正确！`);
      return;
    }
  } catch (e) {
    // 校验失败不影响主流程
    console.error('前置图片数量校验失败:', e);
  }

  isGenerating.value = true;
  isStoring.value = true;
  
  try {
    // 准备图片路径（去掉完整URL前缀，只保留相对路径）
    const uploadedImages = await imageUpload.value.uploadImages(true);
    const relativeImagePaths = uploadedImages.map(img => {
      if (img.path && img.path.startsWith('http://localhost:5000/')) {
        return img.path.replace('http://localhost:5000/', '');
      }
      return img.path;
    });
    
    // 调用API生成评语或更新评语
    const commentData = {
      studentId: selectedStudentId.value,
      columnId: selectedColumnId.value,
      style: selectedStyle.value,
      imagePaths: relativeImagePaths, // 使用相对路径
      addition: additionComment.value // 附加评语
    };
    
    // 直接调用 apiGenerateComment，后端会自动处理更新或创建
    const resp = await apiGenerateComment(commentData);
    if (!resp?.success || !resp?.data) {
      throw new Error(resp?.message || '生成/修改评语失败');
    }
    const newComment = resp.data;
    
    // 更新学生的评语列表
    const student = students.value.find(s => s.id === selectedStudentId.value);
    if (student) {
      if (!student.comments) {
        student.comments = [];
      }
      
      if (isEditingComment.value) {
        // 修改模式：替换旧评语
        const index = student.comments.findIndex(c => c.id === currentViewingComment.value.id);
        if (index !== -1) {
          student.comments[index] = newComment;
        }
      } else {
        // 生成模式：同一专栏存在则替换，否则新增（避免重复/保持按钮状态立即更新）
        const existingIdx = student.comments.findIndex(
          c => String(c.columnId) === String(newComment.columnId)
        );
        if (existingIdx !== -1) {
          student.comments[existingIdx] = newComment;
        } else {
          student.comments.push(newComment);
        }
      }
    }
    
    // 关闭模态框
    closeCommentModal();
    
  } catch (error) {
    console.error('生成/修改评语失败:', error);
    alert('操作失败，请重试');
  } finally {
    isGenerating.value = false;
    isStoring.value = false;
  }
};

// 页面加载时初始化数据
onMounted(() => {
  loadStudents();
  loadColumns();
  loadAccounts();
  loadArchives();
});

// 加载模型存档
const loadArchives = async () => {
  try {
    const resp = await getArchives(currentUser.value.id);
    if (resp?.success) {
      const archives = resp.data || [];
      completedArchives.value = archives.filter(archive => archive.status === 'completed');
      modelArchives.value = archives;
    } else {
      completedArchives.value = [];
      modelArchives.value = [];
    }
  } catch (error) {
    console.error('加载存档失败:', error);
  }
};

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    'pending': '待训练',
    'training': '训练中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 处理 word2vec 模型文件选择
const handleWord2VecModelChange = (e) => {
  word2VecModelFile.value = e.target.files[0]
}

// 处理诊断模型文件夹选择
const handleDiagnosisModelChange = (e) => {
  diagnosisModelFiles.value = Array.from(e.target.files)
}

// 处理知识点对照表文件选择（创建存档用）
const handleKnowledgeMappingFileChange = (e) => {
  if (createMode.value === 'existing') {
    knowledgeMappingFileForCreate.value = e.target.files[0]
  } else {
    knowledgeMappingFileForTrain.value = e.target.files[0]
  }
}

// 处理训练数据文件选择
const handleTrainDataFilesChange = (e) => {
  trainDataFiles.value = Array.from(e.target.files)
}

// 创建存档
const handleCreateArchive = async () => {
  if (!newArchiveName.value.trim()) {
    alert('请输入存档名称')
    return
  }
  
  try {
    const formData = new FormData()
    formData.append('name', newArchiveName.value.trim())
    formData.append('user_id', currentUser.value.id)
    formData.append('create_mode', createMode.value)
    
    if (createMode.value === 'existing') {
      // 选择已有模型模式
      if (!word2VecModelFile.value) {
        alert('请上传知识点推理模型文件')
        return
      }
      if (diagnosisModelFiles.value.length === 0) {
        alert('请上传认知诊断模型文件夹')
        return
      }
      if (!knowledgeMappingFileForCreate.value) {
        alert('请上传知识点对照表')
        return
      }
      
      formData.append('word2vec_model', word2VecModelFile.value)
      diagnosisModelFiles.value.forEach(file => {
        formData.append('diagnosis_model_files', file)
      })
      formData.append('knowledge_mapping', knowledgeMappingFileForCreate.value)
    } else {
      // 上传训练文件模式
      if (!knowledgeMappingFileForTrain.value) {
        alert('请上传知识点对照表')
        return
      }
      if (trainDataFiles.value.length === 0) {
        alert('请上传训练数据文件')
        return
      }
      
      formData.append('knowledge_mapping', knowledgeMappingFileForTrain.value)
      trainDataFiles.value.forEach(file => {
        formData.append('train_data_files', file)
      })
    }
    
    const response = await createArchiveWithFiles(formData)
    if (response?.success) {
      alert('存档创建成功')
      showCreateArchiveModal.value = false
      newArchiveName.value = ''
      // 重置文件变量
      word2VecModelFile.value = null
      diagnosisModelFiles.value = []
      knowledgeMappingFileForCreate.value = null
      knowledgeMappingFileForTrain.value = null
      trainDataFiles.value = []
      loadArchives()
    }
  } catch (error) {
    console.error('创建存档失败:', error)
    alert(error?.message || '创建存档失败')
  }
}

// 显示上传模态框
const showUploadModal = (archive) => {
  currentArchive.value = archive
  showUploadModalFlag.value = true
  knowledgeMappingFile.value = null
  dataFiles.value = []
  uploadProgress.value = 0
}

// 处理知识点映射文件选择
const handleKnowledgeMappingChange = (e) => {
  knowledgeMappingFile.value = e.target.files[0]
}

// 处理数据文件选择
const handleDataFilesChange = (e) => {
  dataFiles.value = Array.from(e.target.files)
}

// 上传文件并开始训练
const handleUploadFiles = async () => {
  if (!knowledgeMappingFile.value) {
    alert('请上传知识点映射文件')
    return
  }
  
  if (dataFiles.value.length === 0) {
    alert('请至少上传一个训练数据文件')
    return
  }
  
  isUploading.value = true
  uploadProgress.value = 10
  
  try {
    const formData = new FormData()
    formData.append('knowledge_mapping', knowledgeMappingFile.value)
    dataFiles.value.forEach(file => {
      formData.append('data_files', file)
    })
    
    const response = await uploadArchiveFiles(currentArchive.value.id, formData)
    
    if (response?.success) {
      uploadProgress.value = 100
      alert('文件上传成功，训练已启动')
      showUploadModalFlag.value = false
      loadArchives()
    }
  } catch (error) {
    console.error('上传文件失败:', error)
    alert('上传文件失败：' + (error?.message || '未知错误'))
  } finally {
    isUploading.value = false
    setTimeout(() => {
      uploadProgress.value = 0
    }, 1000)
  }
}

// 显示存档详情
const showArchiveDetail = async (archive) => {
  currentArchive.value = archive
  try {
    const response = await getArchiveDetail(archive.id)
    if (response?.success) {
      currentArchive.value = response.data
      showDetailModal.value = true
    }
  } catch (error) {
    console.error('获取存档详情失败:', error)
    alert('获取存档详情失败')
  }
}

// 确认删除
const confirmDeleteArchive = (archive) => {
  archiveToDelete.value = archive
  showDeleteArchiveConfirm.value = true
}

// 删除存档
const handleDeleteArchive = async () => {
  try {
    const response = await deleteArchive(archiveToDelete.value.id)
    if (response?.success) {
      alert('存档删除成功')
      showDeleteArchiveConfirm.value = false
      archiveToDelete.value = null
      loadArchives()
    }
  } catch (error) {
    console.error('删除存档失败:', error)
    alert(error?.message || '删除存档失败')
  }
}
</script>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: Arial, sans-serif;
}

/* 顶部导航栏 */
.top-navigation {
  background-color: #4a90e2;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  height: 70px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 30px;
}

.nav-buttons {
  display: flex;
  gap: 10px;
}

.nav-button {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.nav-button:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.nav-button.active {
  background-color: rgba(255, 255, 255, 0.4);
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-name {
  font-weight: 500;
}

.logout-button {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.3s ease;
}

.logout-button:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

/* 主内容区域 */
.main-content {
  background-color: #f5f5f5;
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

/* 空界面样式 */
.empty-interface {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 40px;
  text-align: center;
}

.empty-interface h2 {
  color: #333;
  margin-bottom: 10px;
}

.empty-interface p {
  color: #666;
  font-size: 16px;
}

/* 页面标题和操作区 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #333;
  font-size: 24px;
}

/* 操作按钮容器 */
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.create-column-button {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.3s ease;
}

.create-column-button:hover {
  background-color: #357abd;
}

.batch-generate-button {
  background-color: #50e3c2;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.3s ease;
}

.batch-generate-button:hover:not(:disabled) {
  background-color: #38c1a1;
}

.batch-generate-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* 批量生成模态框样式 */
.batch-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 6px;
}

.nav-button {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s ease;
}

.nav-button:hover:not(:disabled) {
  background-color: #357abd;
}

.nav-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.batch-progress {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.batch-student-info {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 6px;
}

.batch-student-info h4 {
  margin: 0 0 5px 0;
  color: #333;
}

.batch-student-info p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

/* 复选框样式 */
.select-all-checkbox,
.student-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.student-row:hover {
  background-color: #f9f9f9;
}

/* 筛选和搜索区 */
.filter-section {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 15px 20px;
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  color: #555;
  font-weight: 500;
  white-space: nowrap;
  flex: 0 0 auto;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  background-color: white;
  min-width: 180px;
  cursor: pointer;
}

.column-select-container {
  position: relative;
  display: inline-block;
  width: 100%;
}

.column-select-container .filter-select {
  width: 100%;
  padding-right: 30px;
}

.column-info-text-button {
  background: transparent;
  color: #4a90e2;
  border: 1px solid rgba(74, 144, 226, 0.35);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
  white-space: nowrap;
}

.column-info-text-button:hover {
  background: rgba(74, 144, 226, 0.08);
  border-color: rgba(74, 144, 226, 0.6);
}

.delete-column-button {
  position: absolute;
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
  background-color: #ff4d4f;
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.delete-column-button:hover {
  opacity: 1;
}

.readonly-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.readonly-image-item {
  border: 1px solid #e6eaf2;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
}

.readonly-image {
  width: 100%;
  height: 120px;
  object-fit: cover;
  display: block;
  background: #f5f7fa;
  cursor: zoom-in;
}

.readonly-image-index {
  font-size: 12px;
  color: #666;
  padding: 8px 10px;
  border-top: 1px solid #eef2f7;
}

.no-readonly-images {
  margin-top: 10px;
  color: #999;
  font-size: 13px;
}

.image-preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 24px;
}

.image-preview-modal {
  position: relative;
  max-width: min(1100px, 95vw);
  max-height: 90vh;
}

.image-preview-close {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.92);
  color: #333;
  font-size: 22px;
  cursor: pointer;
  line-height: 1;
}

.image-preview-img {
  display: block;
  max-width: 100%;
  max-height: 90vh;
  border-radius: 10px;
  background: #fff;
}

.search-group {
  flex: 1;
  min-width: 250px;
  max-width: 400px;
}

.column-info-group {
  margin-left: auto;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

/* 学生列表 */
.students-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.students-table {
  width: 100%;
  border-collapse: collapse;
}

.students-table th {
  background-color: #f8f9fa;
  padding: 15px 20px;
  text-align: left;
  font-size: 14px;
  font-weight: 600;
  color: #555;
  border-bottom: 2px solid #e9ecef;
}

.students-table td {
  padding: 15px 20px;
  font-size: 14px;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
}

.student-row:hover {
  background-color: #f8f9fa;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.student-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #4a90e2;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
}

.student-details {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.student-name {
  font-weight: 600;
  color: #333;
}

.student-id {
  font-size: 12px;
  color: #666;
}

.column-info {
  font-size: 14px;
  color: #4a90e2;
  font-weight: 500;
}

.no-column {
  color: #999;
  font-style: italic;
}

.status-badge {
  padding: 5px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  display: inline-block;
  min-width: 60px;
}

.status-badge.pending {
  background-color: #fff3cd;
  color: #856404;
}

.status-badge.completed {
  background-color: #d4edda;
  color: #155724;
}

/* 批量添加账号样式 */
.download-template-button {
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
  margin-left: 10px;
}

.download-template-button:hover {
  background-color: #5a6268;
}

/* 文件上传区域样式 */
.file-upload-area {
  border: 2px dashed #e0e0e0;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #f5f7fa;
}

.file-upload-area:hover {
  border-color: #667eea;
  background-color: #e8ecf4;
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

.file-info {
  margin-top: 20px;
  padding: 10px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.file-name {
  font-weight: bold;
  color: #333;
}

.file-size {
  color: #666;
  margin-left: 10px;
}

.file-input {
  display: none;
}

.file-input-visible {
  display: block;
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.action-button {
  padding: 8px 15px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s ease;
  margin-right: 8px;
}

.action-button:last-child {
  margin-right: 0;
}

.delete-button {
  background-color: #dc3545;
  color: white;
}

.delete-button:hover {
  background-color: #c82333;
}

.delete-confirm-content {
  text-align: center;
  padding: 20px;
}

.delete-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.delete-confirm-content p {
  font-size: 16px;
  color: #333;
  line-height: 1.5;
  margin-bottom: 20px;
}

.generate-button {
  background-color: #4a90e2;
  color: white;
}

.generate-button:hover {
  background-color: #357abd;
}

.view-button {
  background-color: #28a745;
  color: white;
}

.view-button:hover {
  background-color: #218838;
}

.no-students {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.no-students-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.no-students h3 {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 18px;
}

.no-students p {
  margin: 0;
  font-size: 14px;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content.large-modal {
  max-width: 700px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

/* 模态框头部操作按钮容器 */
.modal-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.modal-close:hover {
  background-color: #f0f0f0;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 15px 20px;
  border-top: 1px solid #e9ecef;
}

.cancel-button {
  padding: 8px 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  background-color: white;
  color: #333;
  transition: background-color 0.3s ease;
}

.cancel-button:hover {
  background-color: #f8f9fa;
}

.submit-button {
  padding: 8px 15px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  background-color: #4a90e2;
  color: white;
  transition: background-color 0.3s ease;
}

.submit-button:hover {
  background-color: #357abd;
}

.submit-button:disabled {
  background-color: #a0c4f1;
  cursor: not-allowed;
}

/* 加载动画样式 */
.submit-container {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 15px;
  background-color: #4a90e2;
  color: white;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 表单样式 */
.form-group {
  margin-bottom: 15px;
}

.form-label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  box-sizing: border-box;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

/* 图片上传 */
.image-upload-section {
  margin-bottom: 25px;
}

.image-upload-section h4 {
  margin: 0 0 15px 0;
  color: #555;
  font-size: 16px;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s ease;
  background-color: #fafafa;
}

.upload-area:hover {
  border-color: #4a90e2;
}

.upload-area.drag-over {
  border-color: #4a90e2;
  background-color: #f0f7ff;
}

.file-input {
  display: none;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.upload-icon {
  font-size: 48px;
}

.upload-content h5 {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.browse-button {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.3s ease;
}

.browse-button:hover {
  background-color: #357abd;
}

.upload-hint {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.image-preview {
  margin-top: 15px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.preview-item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #ddd;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image-button {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: rgba(255, 0, 0, 0.8);
  color: white;
  border: none;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s ease;
}

.remove-image-button:hover {
  background-color: rgba(255, 0, 0, 1);
}

/* 评语风格选择 */
.style-selection-section {
  margin-bottom: 20px;
}

.style-selection-section h4 {
  margin: 0 0 15px 0;
  color: #555;
  font-size: 16px;
}

.style-options {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.style-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 15px;
  border: 2px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: white;
  user-select: none;
}

.style-option:hover {
  border-color: #4a90e2;
}

.style-option.active {
  border-color: #4a90e2;
  background-color: #f0f7ff;
}

.style-option input[type="radio"] {
  margin: 0;
}

/* 附加评语 */
.addition-section {
  margin-bottom: 20px;
}

.addition-section h4 {
  margin: 0 0 15px 0;
  color: #555;
  font-size: 16px;
}

.addition-textarea {
  width: 100%;
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 6px;
  resize: vertical;
  font-size: 14px;
  font-family: Arial, sans-serif;
  min-height: 100px;
  transition: border-color 0.3s ease;
}

.addition-textarea:focus {
  outline: none;
  border-color: #4a90e2;
}

/* 评语查看 */
.comment-meta {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #666;
}

.comment-column {
  background-color: #e3f2fd;
  padding: 4px 8px;
  border-radius: 4px;
  color: #1976d2;
}

.comment-content {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  line-height: 1.6;
  font-size: 14px;
  color: #333;
  margin-bottom: 20px;
}

.comment-feedback {
  border-top: 1px solid #e9ecef;
  padding-top: 20px;
}

.comment-feedback h4 {
  margin: 0 0 10px 0;
  color: #555;
  font-size: 14px;
}

.feedback-content {
  background-color: #fff3cd;
  padding: 15px;
  border-radius: 6px;
  line-height: 1.6;
  font-size: 14px;
  color: #856404;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-group {
    margin-left: 0;
    min-width: auto;
    max-width: none;
  }
  
  .students-table th, .students-table td {
    padding: 10px;
    font-size: 12px;
  }
  
  .action-button {
    padding: 6px 10px;
    font-size: 12px;
  }
}

/* 模型存档管理样式 */
.model-archives-interface {
  padding: 20px;
}

.model-archives-interface .page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.model-archives-interface .page-header h2 {
  font-size: 28px;
  color: #333;
  margin: 0;
}

.model-archives-interface .create-archive-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.model-archives-interface .create-archive-button:hover {
  transform: translateY(-2px);
}

.model-archives-interface .archives-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.model-archives-interface .archive-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border: 2px solid #e9ecef;
  transition: all 0.3s;
}

.model-archives-interface .archive-card.training {
  border-color: #667eea;
  background: #f0f4ff;
}

.model-archives-interface .archive-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.model-archives-interface .archive-header h3 {
  font-size: 20px;
  color: #333;
  margin: 0;
}

.model-archives-interface .status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.model-archives-interface .status-badge.pending {
  background: #ffeaa7;
  color: #d63031;
}

.model-archives-interface .status-badge.training {
  background: #74b9ff;
  color: #0984e3;
}

.model-archives-interface .status-badge.completed {
  background: #55efc4;
  color: #00b894;
}

.model-archives-interface .status-badge.failed {
  background: #fab1a0;
  color: #d63031;
}

.model-archives-interface .archive-info {
  margin-bottom: 20px;
}

.model-archives-interface .info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e9ecef;
}

.model-archives-interface .info-item:last-child {
  border-bottom: none;
}

.model-archives-interface .label {
  font-weight: bold;
  color: #666;
}

.model-archives-interface .value {
  color: #333;
}

.model-archives-interface .value.success {
  color: #00b894;
}

.model-archives-interface .archive-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.model-archives-interface .action-button {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  min-width: 120px;
}

.model-archives-interface .action-button.upload {
  background: #667eea;
  color: white;
}

.model-archives-interface .action-button.view {
  background: #00b894;
  color: white;
}

.model-archives-interface .action-button.training {
  background: #b2bec3;
  color: white;
  cursor: not-allowed;
}

.model-archives-interface .action-button.delete {
  background: #ff4757;
  color: white;
}

.model-archives-interface .action-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.model-archives-interface .empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  font-size: 16px;
}

/* 模态框样式 */
.model-archives-interface .modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.model-archives-interface .modal-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  min-width: 400px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.model-archives-interface .modal-content h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.model-archives-interface .form-group {
  margin-bottom: 20px;
}

.model-archives-interface .form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
  color: #666;
}

.model-archives-interface .form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.model-archives-interface .file-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.model-archives-interface .hint {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.model-archives-interface .progress-bar {
  width: 100%;
  height: 20px;
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
  margin-top: 15px;
  position: relative;
}

.model-archives-interface .progress {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s;
}

.model-archives-interface .progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-weight: bold;
  font-size: 12px;
}

.model-archives-interface .modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.model-archives-interface .cancel-button,
.model-archives-interface .submit-button {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.model-archives-interface .cancel-button {
  background: #f0f0f0;
  color: #666;
}

.model-archives-interface .submit-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.model-archives-interface .submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.model-archives-interface .submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.model-archives-interface .delete-button {
  background: #ff4757;
  color: white;
}

.model-archives-interface .upload-modal {
  max-width: 500px;
}

.model-archives-interface .detail-content {
  margin-bottom: 20px;
}

.model-archives-interface .info-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #e9ecef;
}

.model-archives-interface .info-row:last-child {
  border-bottom: none;
}

.model-archives-interface .training-log {
  margin-top: 20px;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  max-height: 300px;
  overflow-y: auto;
}

.model-archives-interface .training-log h4 {
  margin: 0 0 10px 0;
  color: #666;
}

.model-archives-interface .training-log pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 12px;
  color: #333;
  margin: 0;
}

/* 创建存档模态框样式 */
.create-archive-modal {
  max-width: 600px;
}

.create-mode-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e9ecef;
  padding-bottom: 10px;
}

.tab-button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: #f0f0f0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.tab-button:hover {
  background: #e0e0e0;
}

.tab-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.tab-content {
  min-height: 200px;
}

.existing-model-section,
.train-model-section {
  padding: 10px 0;
}
</style>
