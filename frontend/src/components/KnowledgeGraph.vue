<template>
  <div class="knowledge-graph-container">
    <div class="main-content">
      <div class="left-panel">
        <h2 class="panel-title">知识查询</h2>
        <div class="query-buttons">
          <button 
            v-for="button in queryButtons" 
            :key="button.id"
            :class="['query-btn', { active: activeQuery === button.id }]"
            @click="executeQuery(button.id)"
            :disabled="!isGraphReady"
          >
            {{ button.label }}
          </button>
        </div>
        
        <div class="statistics">
          <div class="stat-item">
            <div class="stat-value">{{ statistics.nodeCount }}</div>
            <div class="stat-label">知识节点</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.edgeCount }}</div>
            <div class="stat-label">关联关系</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ statistics.categoryCount }}</div>
            <div class="stat-label">知识领域</div>
          </div>
        </div>
        
        <div v-if="selectedNode" class="node-info">
          <div class="node-title">{{ selectedNode.label }}</div>
          <div class="node-property">
            <span class="property-label">类型:</span> 
            <span>{{ getGroupName(selectedNode.group) }}</span>
          </div>
          <div class="node-property">
            <span class="property-label">描述:</span> 
            <span>{{ selectedNode.description || '暂无描述' }}</span>
          </div>
          <div class="node-property">
            <span class="property-label">年份:</span> 
            <span>{{ selectedNode.year || '未知' }}</span>
          </div>
        </div>
        
        <div class="legend">
          <div class="legend-item" v-for="item in legendItems" :key="item.group">
            <div class="legend-color" :style="{ backgroundColor: item.color }"></div>
            <span>{{ item.label }}</span>
          </div>
        </div>
      </div>
      
      <div class="right-panel">
        <div ref="graphContainer" id="graph"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { Network, DataSet } from 'vis'
import 'vis/dist/vis.min.css'

// 导入axios用于API调用
import axios from 'axios'

// 组件状态
const graphContainer = ref(null)
let network = null
let allNodes = null
let allEdges = null
const activeQuery = ref('all')
const selectedNode = ref(null)
const isGraphReady = ref(false)

// 查询按钮配置
const queryButtons = [
  { id: 'all', label: '显示全部知识图谱' },
  { id: 'programming', label: '编程语言相关' },
  { id: 'databases', label: '数据库技术' },
  { id: 'network', label: '网络与安全' },
  { id: 'ai', label: '人工智能与数据科学' },
  { id: 'developers', label: '知名开发者/组织' },
  { id: 'influences', label: '技术影响关系' },
  { id: 'clear', label: '清空图谱' }
]

// 统计信息
const statistics = reactive({
  nodeCount: 0,
  edgeCount: 0,
  categoryCount: 0
})

// 图例配置
const legendItems = [
  { group: 'concept', label: '技术概念', color: '#e74c3c' },
  { group: 'language', label: '编程语言', color: '#3498db' },
  { group: 'database', label: '数据库', color: '#2ecc71' },
  { group: 'person', label: '人物/组织', color: '#9b59b6' },
  { group: 'framework', label: '开发框架', color: '#f39c12' }
]

// 获取分组名称
const getGroupName = (group) => {
  const groupNames = {
    'language': '编程语言',
    'database': '数据库',
    'concept': '技术概念',
    'framework': '开发框架',
    'person': '人物',
    'organization': '组织'
  }
  return groupNames[group] || group
}

// 更新统计信息
const updateStatistics = () => {
  if (!allNodes || !allEdges) return
  
  const nodeCount = allNodes.get().length
  const edgeCount = allEdges.get().length
  
  // 计算不同分组的数量
  const groups = new Set()
  allNodes.get().forEach(node => {
    groups.add(node.group)
  })
  
  statistics.nodeCount = nodeCount
  statistics.edgeCount = edgeCount
  statistics.categoryCount = groups.size
}

// 显示节点信息
const showNodeInfo = (node) => {
  selectedNode.value = node
}

// 隐藏节点信息
const hideNodeInfo = () => {
  selectedNode.value = null
}

// 初始化图谱
const initGraph = async () => {
  try {
    // 从API获取完整的知识图谱数据
    const response = await axios.get('/api/knowledge-graph')
    const { nodes: apiNodes, edges: apiEdges } = response.data
    
    // 转换为DataSet格式
    const nodes = new DataSet(apiNodes);
    const edges = new DataSet(apiEdges);

    allNodes = nodes
    allEdges = edges
    
    const data = {
      nodes: nodes,
      edges: edges
    }
  
    const options = {
      nodes: {
        shape: 'dot',
        size: 20,
        font: {
          size: 14,
          color: '#333'
        },
        borderWidth: 2,
        borderWidthSelected: 4,
        shadow: true
      },
      edges: {
        width: 2,
        font: {
          size: 12,
          align: 'middle'
        },
        arrows: {
          to: { enabled: true, scaleFactor: 0.5 }
        },
        smooth: {
          type: 'continuous',
          roundness: 0.5
        }
      },
      physics: {
        enabled: true,
        stabilization: {
          iterations: 100
        },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 150,
          springConstant: 0.04,
          damping: 0.09
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        hideEdgesOnDrag: true,
        keyboard: false,
        selectable: true,
        selectConnectedEdges: false,
        multiselect: false,
        dragView: true,
        zoomView: true,
        navigationButtons: false
      },
      layout: {
        improvedLayout: true
      }
    }
  
    network = new Network(graphContainer.value, data, options)
  
    // 添加节点点击事件
    network.on("click", function(params) {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0]
        const node = allNodes.get(nodeId)
        showNodeInfo(node)
      } else {
        hideNodeInfo()
      }
    })
  
    // 添加双击事件处理（可选）
    network.on("doubleClick", function(params) {
      console.log("Double clicked on network")
    })
  
    // 确保事件不会冒泡到父组件
    network.on("click", function(params) {
      params.event.stopPropagation()
    })
  
    // 更新统计信息
    updateStatistics()
    isGraphReady.value = true
  } catch (error) {
    console.error('初始化图谱失败:', error)
  }
}

// 查询函数
const executeQuery = async (queryId) => {
  activeQuery.value = queryId
  
  try {
    switch (queryId) {
      case 'all':
        await queryAll()
        break
      case 'programming':
        await queryProgramming()
        break
      case 'databases':
        await queryDatabases()
        break
      case 'network':
        // 网络与安全查询在后端可能没有直接的端点，使用自定义过滤
        await queryNetwork()
        break
      case 'ai':
        await queryAI()
        break
      case 'developers':
        await queryDevelopers()
        break
      case 'influences':
        // 影响关系查询在后端可能没有直接的端点，使用自定义过滤
        await queryInfluences()
        break
      case 'clear':
        clearGraph()
        break
    }
  } catch (error) {
    console.error('查询失败:', error)
  }
}

const queryAll = async () => {
  // 从API获取完整数据
  const response = await axios.get('/api/knowledge-graph')
  const { nodes: apiNodes, edges: apiEdges } = response.data
  
  // 先清空现有数据，然后添加新数据
  allNodes.clear()
  allEdges.clear()
  allNodes.add(apiNodes)
  allEdges.add(apiEdges)
  updateStatistics()
}

const queryProgramming = async () => {
  // 从API获取编程语言相关数据
  const response = await axios.get('/api/knowledge-graph/query/programming')
  const { nodes: apiNodes, edges: apiEdges } = response.data
  
  // 先清空现有数据，然后添加新数据
  allNodes.clear()
  allEdges.clear()
  allNodes.add(apiNodes)
  allEdges.add(apiEdges)
  updateStatistics()
}

const queryDatabases = async () => {
  // 从API获取数据库相关数据
  const response = await axios.get('/api/knowledge-graph/query/databases')
  const { nodes: apiNodes, edges: apiEdges } = response.data
  
  // 先清空现有数据，然后添加新数据
  allNodes.clear()
  allEdges.clear()
  allNodes.add(apiNodes)
  allEdges.add(apiEdges)
  updateStatistics()
}

const queryNetwork = async () => {
  // 从API获取完整数据，然后在前端进行过滤
  const response = await axios.get('/api/knowledge-graph')
  const { nodes: allApiNodes, edges: allApiEdges } = response.data
  
  // 筛选网络与安全相关的节点和边
  const filteredNodes = allApiNodes.filter(node => 
    node.label === '网络安全' || 
    node.label === '物联网' || 
    node.label === '云计算' ||
    node.label === '区块链'
  )
  
  // 获取相关节点ID
  const networkNodeIds = new Set(filteredNodes.map(node => node.id))
  
  const filteredEdges = allApiEdges.filter(edge => 
    networkNodeIds.has(edge.from) || 
    networkNodeIds.has(edge.to)
  )
  
  // 先清空现有数据，然后添加新数据
  allNodes.clear()
  allEdges.clear()
  allNodes.add(filteredNodes)
  allEdges.add(filteredEdges)
  updateStatistics()
}

const queryAI = async () => {
  // 从API获取人工智能相关数据
  const response = await axios.get('/api/knowledge-graph/query/ai')
  const { nodes: apiNodes, edges: apiEdges } = response.data
  
  // 先清空现有数据，然后添加新数据
  allNodes.clear()
  allEdges.clear()
  allNodes.add(apiNodes)
  allEdges.add(apiEdges)
  updateStatistics()
}

const queryDevelopers = async () => {
  // 从API获取开发者相关数据
  const response = await axios.get('/api/knowledge-graph/query/developers')
  const { nodes: apiNodes, edges: apiEdges } = response.data
  
  // 先清空现有数据，然后添加新数据
  allNodes.clear()
  allEdges.clear()
  allNodes.add(apiNodes)
  allEdges.add(apiEdges)
  updateStatistics()
}

const queryInfluences = async () => {
  // 从API获取完整数据，然后在前端进行过滤
  const response = await axios.get('/api/knowledge-graph')
  const { nodes: allApiNodes, edges: allApiEdges } = response.data
  
  // 只显示"影响"关系
  const influenceEdges = allApiEdges.filter(edge => 
    edge.label === '影响' || 
    edge.label === '促进' || 
    edge.label === '增强' || 
    edge.label === '依赖于'
  )
  
  // 获取相关节点ID
  const influenceNodeIds = new Set()
  influenceEdges.forEach(edge => {
    influenceNodeIds.add(edge.from)
    influenceNodeIds.add(edge.to)
  })
  
  const filteredNodes = allApiNodes.filter(node => 
    influenceNodeIds.has(node.id)
  )
  
  // 先清空现有数据，然后添加新数据
  allNodes.clear()
  allEdges.clear()
  allNodes.add(filteredNodes)
  allEdges.add(influenceEdges)
  updateStatistics()
}

const clearGraph = () => {
  if (!allNodes || !allEdges) return
  
  allNodes.clear()
  allEdges.clear()
  hideNodeInfo()
  updateStatistics()
}

// 生命周期
onMounted(() => {
  initGraph()
})
</script>

<style scoped>
.knowledge-graph-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 700px;
  max-height: 100%;
}

.main-content {
  display: flex;
  height: 100%;
}

.left-panel {
  width: 300px;
  padding: 25px;
  border-right: 1px solid #eaeaea;
  background-color: #fafbfd;
  overflow-y: auto;
}

.right-panel {
  flex: 1;
  position: relative;
  padding: 15px;
  height: 100%;
}

.panel-title {
  font-size: 1.3rem;
  margin-bottom: 20px;
  color: #2c3e50;
  border-bottom: 2px solid #4a6491;
  padding-bottom: 8px;
}

.query-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 30px;
}

.query-btn {
  padding: 12px 18px;
  background-color: #f0f4f8;
  border: none;
  border-radius: 8px;
  text-align: left;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
  color: #3a506b;
  border-left: 4px solid #4a6491;
}

.query-btn:hover {
  background-color: #e1e8f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.query-btn.active {
  background-color: #4a6491;
  color: white;
}

.statistics {
  display: flex;
  justify-content: space-between;
  background-color: #f0f4f8;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #2c3e50;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
}

.node-info {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
}

.node-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 10px;
  color: #2c3e50;
}

.node-property {
  margin-bottom: 8px;
  font-size: 0.95rem;
}

.property-label {
  font-weight: 600;
  color: #4a6491;
}

#graph {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  border: 1px solid #ddd;
  background-color: white;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
}

.legend-color {
  width: 18px;
  height: 18px;
  border-radius: 50%;
}

@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
    height: auto;
  }
  
  .left-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #eaeaea;
  }
  
  .right-panel {
    height: 600px;
  }
}
</style>
