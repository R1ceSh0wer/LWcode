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
        </div>

        <!-- 学生列表 -->
        <div class="students-container">
          <table class="students-table">
            <thead>
              <tr>
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
            <label class="form-label">上传试题图片</label>
            <ImageUpload ref="columnImageUpload" />
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeColumnModal" class="cancel-button">取消</button>
          <button 
            @click="createColumn"
            class="submit-button"
            :disabled="!newColumn.name"
          >
            创建专栏
          </button>
        </div>
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
import { getColumns, addColumn, deleteColumn } from '../api/columns';
import { generateComment as apiGenerateComment, getStudentComments, createComment as apiCreateComment, deleteComment as apiDeleteComment } from '../api/comments';
import { uploadImage } from '../api/images';
import { getAccounts, addAccount as apiAddAccount, deleteAccount as apiDeleteAccount, updateAccount as apiUpdateAccount, batchAddAccounts as apiBatchAddAccounts } from '../api/accounts';
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
const newColumn = ref({ name: '' });
const columnImageUpload = ref(null);

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
const uploadedImages = ref([]);
const previewImages = ref([]);
const imageUploadKey = ref(0);

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

// 关闭专栏模态框
const closeColumnModal = () => {
  newColumn.value = { name: '', description: '' };
  isColumnModalVisible.value = false;
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
    const studentsData = await getStudents();
    for (const student of studentsData) {
      student.comments = await getStudentComments(student.id);
    }
    students.value = studentsData;
  } catch (error) {
    console.error('加载学生数据失败:', error);
  }
};

// 加载专栏数据
const loadColumns = async () => {
  try {
    const columnsData = await getColumns();
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
    const accountsData = await getAccounts();
    accounts.value = accountsData;
  } catch (error) {
    console.error('加载账号数据失败:', error);
  }
};

// 创建专栏
const createColumn = async () => {
  if (!newColumn.value.name) return;
  
  try {
    // 准备专栏数据
    const columnData = {
      name: newColumn.value.name,
      teacherId: 1 // 默认教师ID为1
    };
    
    // 获取预览图片的文件对象
    if (columnImageUpload.value) {
      const imageFiles = columnImageUpload.value.getPreviewFiles();
      if (imageFiles.length > 0) {
        columnData.imageFiles = imageFiles;
      }
    }
    
    // 创建专栏
    const result = await addColumn(columnData);
    if (result) {
      columns.value.push(result);
      newColumn.value = { name: '' };
      isColumnModalVisible.value = false;
      // 清空图片上传组件的预览
      if (columnImageUpload.value) {
        columnImageUpload.value.clearAll();
      }
    }
  } catch (error) {
    console.error('创建专栏失败:', error);
    alert('创建专栏失败，请重试');
  }
};

// 生成评语
const generateComment = async () => {
  if (!selectedStudentId.value || !selectedColumnId.value) return;
  
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
    
    let newComment;
    // 直接调用apiGenerateComment，后端会自动处理更新或创建
    newComment = await apiGenerateComment(commentData);
    
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
        // 生成模式：添加新评语
        student.comments.push(newComment);
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
});
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

.search-group {
  margin-left: auto;
  flex: 1;
  min-width: 250px;
  max-width: 400px;
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
</style>
