<template>
  <div class="builder-container">
    <div class="toolbar">
      <label>选择专栏：</label>
      <select v-model="selectedColumnId" @change="loadGraphData">
        <option value="">请选择专栏</option>
        <option v-for="col in columns" :key="col.id" :value="String(col.id)">
          {{ col.name }}
        </option>
      </select>
      <button class="save-btn" :disabled="!selectedColumnId || saving" @click="saveGraph">
        {{ saving ? '保存中...' : '保存图谱' }}
      </button>
      <button class="connect-btn" :disabled="!selectedColumnId" @click="startConnectMode">
        {{ isConnectMode ? '取消连线' : '连接两个节点' }}
      </button>
    </div>

    <div class="partition-bar">
      <div v-if="isConnectMode" class="connect-hint">
        连线模式：
        <span v-if="!connectSourceLabel">请先点击起点节点</span>
        <span v-else>当前起点：{{ connectSourceLabel }}，请点击终点节点</span>
      </div>
      <div class="partition-list">
        <button
          :class="['partition-chip', { active: activePartitionFilter === '' }]"
          @click="activePartitionFilter = ''; renderGraph()"
        >
          全部
        </button>
        <button
          v-for="part in partitions"
          :key="part"
          :class="['partition-chip', { active: activePartitionFilter === part }]"
          @click="activePartitionFilter = part; renderGraph()"
        >
          {{ part }}
        </button>
      </div>
      <div class="create-partition">
        <input v-model.trim="newPartitionName" placeholder="输入分区名称" />
        <button @click="createPartition">创建分区</button>
      </div>
    </div>

    <div class="content">
      <div class="graph-panel fixed">
        <div ref="graphContainer" class="graph"></div>
      </div>
      <div class="side-panel">
        <div class="section">
          <h3>知识点背包</h3>
          <div class="bag-list">
            <div v-for="node in backpackNodes" :key="node.id" class="bag-item">
              <div class="bag-main">
                <span class="bag-label">{{ node.label }}</span>
                <span class="bag-weight">权重 {{ node.weight }}</span>
              </div>
              <button @click="putNodeIntoGraph(node.id)">放入图谱</button>
            </div>
            <div v-if="backpackNodes.length === 0" class="empty">背包为空</div>
          </div>
        </div>

        <div class="section" v-if="selectedNode">
          <h3>节点编辑</h3>
          <div class="form-row"><span>名称：</span><b>{{ selectedNode.label }}</b></div>
          <div class="form-row">
            <span>权重：</span>
            <input type="number" min="1" v-model.number="selectedNode.weight" @change="syncSelectedNodeWeight" />
          </div>
          <div class="form-row">
            <span>分区：</span>
            <select v-model="selectedNodePartition" @change="updateNodePartition">
              <option value="">请选择分区</option>
              <option v-for="part in partitions" :key="part" :value="part">
                {{ part }}
              </option>
            </select>
          </div>
          <button @click="putNodeInBackpack(selectedNode.id)">放回背包</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Network, DataSet } from 'vis'
import 'vis/dist/vis.min.css'
import { getColumnKnowledgeGraph, saveColumnKnowledgeGraph } from '../api/knowledgeBuilder'

const props = defineProps({
  columns: { type: Array, default: () => [] }
})

const graphContainer = ref(null)
const selectedColumnId = ref('')
const nodes = ref([])
const edges = ref([])
const partitions = ref([])
const newPartitionName = ref('')
const activePartitionFilter = ref('')
const selectedNode = ref(null)
const selectedNodePartition = ref('')
const saving = ref(false)
const isConnectMode = ref(false)
const connectSourceId = ref('')
const connectSourceLabel = computed(() => {
  if (!connectSourceId.value) return ''
  const node = nodes.value.find(n => n.id === connectSourceId.value)
  return node?.label || connectSourceId.value
})

// 监听选中节点变化，更新分区选择
watch(selectedNode, (newNode) => {
  if (newNode) {
    selectedNodePartition.value = (newNode.partitionTags && newNode.partitionTags.length > 0) ? newNode.partitionTags[0] : ''
  } else {
    selectedNodePartition.value = ''
  }
}, { immediate: true })

let network = null
let nodesDs = null
let edgesDs = null

const backpackNodes = computed(() => nodes.value.filter(n => n.inBackpack))

const loadGraphData = async () => {
  selectedNode.value = null
  if (!selectedColumnId.value) {
    nodes.value = []
    edges.value = []
    partitions.value = []
    renderGraph()
    return
  }
  const resp = await getColumnKnowledgeGraph(selectedColumnId.value)
  if (!resp?.success) {
    alert(resp?.message || '加载知识图谱失败')
    return
  }
  nodes.value = (resp.data?.nodes || []).map(n => ({
    ...n,
    partitionTags: Array.isArray(n.partitionTags) ? n.partitionTags : []
  }))
  edges.value = resp.data?.edges || []
  partitions.value = resp.data?.partitions || []
  activePartitionFilter.value = ''
  await nextTick()
  renderGraph()
}

const renderGraph = () => {
  if (!graphContainer.value) return
  const visibleNodes = nodes.value.filter(n => !n.inBackpack).filter(n => {
    if (!activePartitionFilter.value) return true
    return (n.partitionTags || []).includes(activePartitionFilter.value)
  })
  const visibleNodeIds = new Set(visibleNodes.map(n => n.id))
  const visibleEdges = edges.value.filter(e => visibleNodeIds.has(e.from) && visibleNodeIds.has(e.to))

  nodesDs = new DataSet(
    visibleNodes.map(n => ({
      ...n,
      color: connectSourceId.value === n.id
        ? {
            background: '#ffd166',
            border: '#f39c12',
            highlight: { background: '#ffd166', border: '#e67e22' }
          }
        : n.color,
      borderWidth: connectSourceId.value === n.id ? 4 : 2,
      size: Math.max(16, Number(n.weight || 1) * 3),
      title: `${n.label} (权重: ${n.weight || 1})`
    }))
  )
  edgesDs = new DataSet(visibleEdges)

  const data = { nodes: nodesDs, edges: edgesDs }
  const options = {
    nodes: { shape: 'dot', borderWidth: 2, font: { size: 14 }, shadow: true },
    edges: {
      arrows: { to: { enabled: true, scaleFactor: 0.6 } },
      font: { align: 'middle', size: 12 },
      smooth: { type: 'continuous', roundness: 0.35 }
    },
    physics: { enabled: true, stabilization: { iterations: 80 } },
    interaction: { hover: true, dragNodes: true, dragView: true, zoomView: true }
  }

  if (network) network.destroy()
  network = new Network(graphContainer.value, data, options)

  network.on('click', params => {
    if (!params.nodes.length) {
      selectedNode.value = null
      return
    }
    const id = params.nodes[0]
    // 连线模式下：依次选择起点和终点，自动创建关系
    if (isConnectMode.value) {
      if (!connectSourceId.value) {
        connectSourceId.value = id
        return
      }

      const fromId = connectSourceId.value
      const toId = id
      connectSourceId.value = ''

      if (fromId === toId) {
        alert('不能连接同一个节点')
        return
      }

      const relation = window.prompt('请输入关系名称', '相关')
      if (!relation) return

      const edgeId = `${fromId}->${toId}`
      const existing = edges.value.find(e => e.id === edgeId)
      if (existing) {
        existing.label = relation
      } else {
        edges.value.push({ id: edgeId, from: fromId, to: toId, label: relation })
      }
      renderGraph()
      return
    }

    selectedNode.value = nodes.value.find(n => n.id === id) || null
  })

  // 移除右键菜单设置分区的功能，现在通过节点编辑界面的下拉框设置
  network.on('oncontext', params => {
    params.event.preventDefault()
  })

  network.on('dragEnd', params => {
    if (!params.nodes?.length) return
    params.nodes.forEach(id => {
      const p = network.getPositions([id])[id]
      const n = nodes.value.find(item => item.id === id)
      if (n && p) {
        n.x = p.x
        n.y = p.y
      }
    })
  })
}

const createPartition = () => {
  if (!newPartitionName.value) return
  if (partitions.value.includes(newPartitionName.value)) {
    alert('分区名称已存在')
    return
  }
  partitions.value.push(newPartitionName.value)
  newPartitionName.value = ''
}

const putNodeIntoGraph = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return
  node.inBackpack = false
  renderGraph()
}

const putNodeInBackpack = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return
  node.inBackpack = true
  renderGraph()
}

const syncSelectedNodeWeight = () => {
  if (!selectedNode.value) return
  selectedNode.value.weight = Math.max(1, Number(selectedNode.value.weight || 1))
  renderGraph()
}

const updateNodePartition = () => {
  if (!selectedNode.value) return
  if (selectedNodePartition.value) {
    selectedNode.value.partitionTags = [selectedNodePartition.value]
  } else {
    selectedNode.value.partitionTags = []
  }
  renderGraph()
}

const startConnectMode = () => {
  if (!network) return
  isConnectMode.value = !isConnectMode.value
  connectSourceId.value = ''
  if (isConnectMode.value) {
    selectedNode.value = null
  }
}

const saveGraph = async () => {
  if (!selectedColumnId.value) return
  saving.value = true
  try {
    const payload = {
      nodes: nodes.value.map(n => ({
        ...n,
        weight: Math.max(1, Number(n.weight || 1)),
        partitionTags: Array.isArray(n.partitionTags) ? n.partitionTags : []
      })),
      edges: edges.value,
      partitions: partitions.value
    }
    const resp = await saveColumnKnowledgeGraph(selectedColumnId.value, payload)
    if (!resp?.success) {
      alert(resp?.message || '保存失败')
      return
    }
    alert('知识图谱保存成功')
  } finally {
    saving.value = false
  }
}

watch(
  () => props.columns,
  (cols) => {
    if (!selectedColumnId.value && cols.length > 0) {
      selectedColumnId.value = String(cols[0].id)
      loadGraphData()
    }
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
.builder-container { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.toolbar select, .toolbar input { padding: 6px 10px; border: 1px solid #d5dbe6; border-radius: 6px; }
.save-btn, .connect-btn { border: none; border-radius: 6px; padding: 8px 12px; color: #fff; cursor: pointer; }
.save-btn { background: #667eea; }
.connect-btn { background: #3fb27f; }
.partition-bar { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
.connect-hint { font-size: 13px; color: #3fb27f; font-weight: 600; }
.partition-list { display: flex; gap: 8px; flex-wrap: wrap; }
.partition-chip { border: 1px solid #d5dbe6; background: #fff; border-radius: 14px; padding: 4px 10px; cursor: pointer; }
.partition-chip.active { background: #667eea; color: #fff; border-color: #667eea; }
.create-partition { display: flex; gap: 8px; }
.content { display: grid; grid-template-columns: 1fr 320px; gap: 12px; min-height: 600px; }
.graph-panel { border: 1px solid #eceff5; border-radius: 10px; padding: 8px; background: #fff; }
.graph-panel.fixed { position: sticky; top: 20px; z-index: 10; }
.graph { width: 100%; height: 580px; border: 1px solid #d5dbe6; border-radius: 8px; }

/* 分区选择下拉框样式 */
.form-row select {
  padding: 4px 8px;
  border: 1px solid #d5dbe6;
  border-radius: 6px;
  font-size: 14px;
  min-width: 120px;
}
.side-panel { display: flex; flex-direction: column; gap: 12px; }
.section { background: #fff; border: 1px solid #eceff5; border-radius: 10px; padding: 12px; }
.bag-list { display: flex; flex-direction: column; gap: 8px; max-height: 280px; overflow-y: auto; }
.bag-item { border: 1px solid #edf0f6; border-radius: 8px; padding: 8px; display: flex; justify-content: space-between; gap: 8px; align-items: center; }
.bag-main { display: flex; flex-direction: column; gap: 4px; }
.bag-label { font-size: 14px; color: #333; }
.bag-weight { font-size: 12px; color: #667eea; }
.form-row { margin-bottom: 8px; display: flex; gap: 8px; align-items: center; }
.form-row input { width: 90px; padding: 4px 8px; border: 1px solid #d5dbe6; border-radius: 6px; }
.empty { color: #8b93a7; font-size: 13px; }
@media (max-width: 1200px) {
  .content { grid-template-columns: 1fr; }
}
</style>
