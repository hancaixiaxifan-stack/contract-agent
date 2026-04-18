<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import axios from "axios"

const router = useRouter()
const contracts = ref([])

const loadContracts = async () => {
  try {
    const res = await axios.get("http://127.0.0.1:8000/history")
    if (res.data.success) contracts.value = res.data.contracts || []
  } catch (e) { console.error("获取历史失败", e) }
}

onMounted(() => { loadContracts() })

const goBack = () => { router.push("/") }
const goToReview = () => { router.push("/") }

const viewDetail = async (contract) => {
  sessionStorage.setItem("contractAnalysisResult", JSON.stringify({
    risks: contract.result_data?.risks || [],
    summary: contract.result_data?.summary || "无评估结果",
    stance: contract.stance || "employee"
  }))
  const isText = contract.file_name?.endsWith(".txt")
  if (isText) {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/text/${contract.id}`)
      if (res.data.success) sessionStorage.setItem("textFullText", res.data.content)
    } catch (e) { console.error("获取文本失败", e) }
  }
  router.push({
    path: "/history-detail",
    query: {
      fileName: contract.file_name,
      contractType: contract.contract_type || "未知合同",
      source: isText ? "text" : "pdf",
      fileId: contract.id
    }
  })
}

const deleteContract = async (contract) => {
  if (!confirm(`确定删除 "${contract.file_name}" 吗？`)) return
  try {
    await axios.delete(`http://127.0.0.1:8000/contract/${contract.id}`)
    loadContracts()
  } catch (e) {
    console.error("删除失败", e)
    alert("删除失败")
  }
}

const riskCount = (c) => c.result_data?.risks?.length || 0
const highRiskCount = (c) => c.result_data?.risks?.filter(r => r.level === 'high').length || 0
const getMaxLevel = (c) => {
  const r = c.result_data?.risks || []
  if (r.some(x => x.level === 'high')) return 'high'
  if (r.some(x => x.level === 'medium')) return 'medium'
  if (r.length) return 'low'
  return 'ok'
}
const levelBadge = { high: 'badge-high', medium: 'badge-medium', low: 'badge-low', ok: 'badge-done' }
const levelText = { high: '高风险', medium: '中风险', low: '低风险', ok: '无风险' }
</script>

<template>
  <div class="page">

    <div class="page-header">
      <button class="btn-back" @click="goBack">← 返回首页</button>
      <div class="page-header-title">
        <h1>审查历史</h1>
        <p>共 {{ contracts.length }} 份合同记录</p>
      </div>
    </div>

    <!-- List -->
    <div class="contracts-list" v-if="contracts.length > 0">
      <div
        v-for="contract in contracts"
        :key="contract.id"
        class="contract-row"
        @click="viewDetail(contract)"
      >
        <div class="row-icon">
          <span>{{ contract.file_name?.endsWith('.txt') ? '✦' : '◈' }}</span>
        </div>

        <div class="row-info">
          <div class="row-name">{{ contract.file_name }}</div>
          <div class="row-meta">
            <span>{{ contract.contract_type || '合同文件' }}</span>
            <span class="meta-sep">·</span>
            <span>{{ contract.created_at }}</span>
            <span class="meta-sep">·</span>
            <span>{{ riskCount(contract) }} 项审查点</span>
          </div>
        </div>

        <div class="row-status">
          <span class="badge" :class="levelBadge[getMaxLevel(contract)]">
            {{ levelText[getMaxLevel(contract)] }}
          </span>
          <span v-if="highRiskCount(contract) > 0" class="high-count">
            {{ highRiskCount(contract) }} 高风险
          </span>
        </div>

        <div class="row-actions">
          <button class="btn btn-danger btn-sm" @click.stop="deleteContract(contract)">删除</button>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="9" y1="13" x2="15" y2="13"/>
          <line x1="9" y1="17" x2="11" y2="17"/>
        </svg>
      </div>
      <h2>暂无审查记录</h2>
      <p>开始你的第一次 AI 合同审查吧</p>
      <button class="btn btn-primary" @click="goToReview">前往审查</button>
    </div>

  </div>
</template>

<style scoped>
.page {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 24px 60px;
}

/* Contract list */
.contracts-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.contract-row {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--r-lg);
  padding: 16px 20px;
  box-shadow: var(--shadow-xs);
  transition: all var(--t-fast) var(--ease);
  cursor: pointer;
}

.contract-row:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--ink-soft);
  transform: translateY(-1px);
}

.row-icon {
  width: 40px; height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-sm);
  font-size: 18px;
  color: var(--gold);
  flex-shrink: 0;
}

.row-info {
  flex: 1;
  min-width: 0;
}

.row-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.row-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ink-muted);
  flex-wrap: wrap;
}

.meta-sep { opacity: 0.4; }

.row-status {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.high-count {
  font-size: 12px;
  color: var(--risk-high);
  font-weight: 600;
}

.row-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-sm { padding: 7px 14px; font-size: 13px; }

.btn-danger {
  background: transparent;
  color: var(--risk-high);
  border: 1px solid var(--risk-high-border);
}

.btn-danger:hover {
  background: var(--risk-high-bg);
  border-color: var(--risk-high);
}

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  text-align: center;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--r-xl);
}

.empty-icon {
  width: 80px; height: 80px;
  background: var(--parchment);
  border: 1px solid var(--rule);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-muted);
  margin-bottom: 20px;
}

.empty-state h2 {
  font-size: 22px;
  color: var(--ink);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--ink-muted);
  margin-bottom: 24px;
}
</style>
