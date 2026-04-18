<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import axios from "axios"

const router = useRouter()
const reviewType = ref("pdf")
const recentContracts = ref([])

const loadRecent = async () => {
  try {
    const res = await axios.get("http://127.0.0.1:8000/history")
    if (res.data.success) {
      recentContracts.value = (res.data.contracts || []).slice(0, 5)
    }
  } catch (e) {
    console.error("获取历史失败", e)
  }
}

onMounted(() => { loadRecent() })

const goToReview = () => {
  router.push(reviewType.value === "text" ? "/upload/text" : "/upload/pdf")
}

const goToHistory = () => { router.push("/history") }

const viewRecentDetail = async (contract) => {
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
      fileId: contract.id,
      from: "home"
    }
  })
}

const riskCount = (c) => c.result_data?.risks?.length || 0
const highRiskCount = (c) => c.result_data?.risks?.filter(r => r.level === 'high').length || 0
</script>

<template>
  <div class="home">

    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-badge">AI 驱动合同审查</div>
        <h1 class="hero-title">智能合同<br/><em>风险识别</em></h1>
        <p class="hero-desc">精准定位合同隐患，提供专业修改意见，守护你的每一份权益</p>

        <div class="hero-actions">
          <div class="type-selector">
            <button
              class="type-btn"
              :class="{ active: reviewType === 'text' }"
              @click="reviewType = 'text'"
            >
              <span class="type-icon">✦</span> 文本审查
            </button>
            <button
              class="type-btn"
              :class="{ active: reviewType === 'pdf' }"
              @click="reviewType = 'pdf'"
            >
              <span class="type-icon">◈</span> PDF审查
            </button>
          </div>

          <button class="btn-start" @click="goToReview">
            开始审查
            <span class="btn-arrow">→</span>
          </button>
        </div>
      </div>

      <!-- Decorative elements -->
      <div class="hero-deco">
        <div class="deco-circle deco-1"></div>
        <div class="deco-circle deco-2"></div>
        <div class="deco-lines"></div>
      </div>
    </section>

    <!-- Stats row -->
    <div class="stats-row">
      <div class="stat-item">
        <span class="stat-num">15+</span>
        <span class="stat-label">审查维度</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-num">双立场</span>
        <span class="stat-label">甲方 / 乙方</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <span class="stat-num">AI 驱动</span>
        <span class="stat-label">专业法律分析</span>
      </div>
    </div>

    <!-- Recent history -->
    <section class="recent-section" v-if="recentContracts.length > 0">
      <div class="section-heading">
        <span class="section-label">最近审查</span>
        <button class="btn-ghost" @click="goToHistory">查看全部 →</button>
      </div>

      <div class="recent-list">
        <div
          v-for="contract in recentContracts"
          :key="contract.id"
          class="recent-item"
          @click="viewRecentDetail(contract)"
        >
          <div class="recent-icon">
            <span>{{ contract.file_name?.endsWith('.txt') ? '✦' : '◈' }}</span>
          </div>
          <div class="recent-info">
            <span class="recent-name">{{ contract.file_name }}</span>
            <span class="recent-type">{{ contract.contract_type || '合同文件' }}</span>
          </div>
          <div class="recent-meta">
            <span v-if="highRiskCount(contract) > 0" class="badge badge-high">
              {{ highRiskCount(contract) }} 高风险
            </span>
            <span v-else-if="riskCount(contract) > 0" class="badge badge-medium">
              {{ riskCount(contract) }} 风险点
            </span>
            <span v-else class="badge badge-low">无风险</span>
            <span class="recent-date">{{ contract.created_at }}</span>
          </div>
          <div class="recent-arrow">›</div>
        </div>
      </div>
    </section>

  </div>
</template>

<style scoped>
.home {
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 24px 60px;
}

/* ── Hero ── */
.hero {
  position: relative;
  background: var(--ink);
  border-radius: var(--r-xl);
  padding: 64px 56px;
  margin-bottom: 24px;
  overflow: hidden;
  color: var(--parchment);
}

.hero-inner {
  position: relative;
  z-index: 2;
  max-width: 500px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--gold-light);
  margin-bottom: 20px;
}

.hero-title {
  font-family: var(--font-display);
  font-size: 52px;
  font-weight: 400;
  line-height: 1.1;
  color: var(--parchment);
  margin-bottom: 16px;
  letter-spacing: -0.02em;
}

.hero-title em {
  font-style: italic;
  color: var(--gold-light);
}

.hero-desc {
  font-size: 15px;
  color: rgba(250,248,243,0.6);
  line-height: 1.6;
  margin-bottom: 36px;
  max-width: 380px;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* Type selector */
.type-selector {
  display: flex;
  gap: 4px;
  background: rgba(255,255,255,0.08);
  padding: 4px;
  border-radius: var(--r-md);
  border: 1px solid rgba(255,255,255,0.12);
}

.type-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  color: rgba(250,248,243,0.55);
  background: transparent;
  border: none;
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: all var(--t-fast) var(--ease);
}

.type-btn .type-icon { font-size: 11px; }

.type-btn.active {
  background: var(--gold);
  color: white;
  box-shadow: 0 2px 8px rgba(184,146,42,0.4);
}

.type-btn:not(.active):hover {
  color: var(--parchment);
  background: rgba(255,255,255,0.1);
}

/* Start button */
.btn-start {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  background: var(--parchment);
  border: none;
  border-radius: var(--r-md);
  cursor: pointer;
  transition: all var(--t-mid) var(--ease-spring);
  letter-spacing: 0.01em;
}

.btn-start:hover {
  background: white;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  transform: translateY(-2px);
}

.btn-arrow {
  display: inline-block;
  transition: transform var(--t-mid) var(--ease-spring);
}

.btn-start:hover .btn-arrow {
  transform: translateX(4px);
}

/* Decorative elements */
.hero-deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
}

.deco-circle {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.06);
}

.deco-1 {
  width: 400px; height: 400px;
  right: -100px; top: -100px;
  background: radial-gradient(circle, rgba(184,146,42,0.08) 0%, transparent 70%);
}

.deco-2 {
  width: 200px; height: 200px;
  right: 80px; bottom: -60px;
  background: radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%);
}

.deco-lines {
  position: absolute;
  right: 60px;
  top: 50%;
  transform: translateY(-50%);
  width: 240px;
  height: 200px;
  background-image: repeating-linear-gradient(
    0deg,
    rgba(255,255,255,0.04) 0px,
    rgba(255,255,255,0.04) 1px,
    transparent 1px,
    transparent 28px
  );
}

/* ── Stats Row ── */
.stats-row {
  display: flex;
  align-items: center;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--r-lg);
  padding: 20px 32px;
  margin-bottom: 32px;
  box-shadow: var(--shadow-xs);
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--ink);
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 12px;
  color: var(--ink-muted);
  letter-spacing: 0.02em;
}

.stat-divider {
  width: 1px;
  height: 36px;
  background: var(--rule);
  flex-shrink: 0;
}

/* ── Recent Section ── */
.recent-section {}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.btn-ghost {
  background: transparent;
  border: none;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--ink-muted);
  cursor: pointer;
  transition: color var(--t-fast) var(--ease);
}

.btn-ghost:hover { color: var(--ink); }

.recent-list {
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--r-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--rule-light);
  cursor: pointer;
  transition: background var(--t-fast) var(--ease);
}

.recent-item:last-child { border-bottom: none; }

.recent-item:hover { background: var(--parchment); }

.recent-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-sm);
  font-size: 16px;
  color: var(--gold);
  flex-shrink: 0;
}

.recent-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.recent-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recent-type {
  font-size: 12px;
  color: var(--ink-muted);
}

.recent-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.recent-date {
  font-size: 12px;
  color: var(--ink-muted);
}

.recent-arrow {
  font-size: 18px;
  color: var(--ink-muted);
  flex-shrink: 0;
  transition: transform var(--t-fast) var(--ease);
}

.recent-item:hover .recent-arrow { transform: translateX(3px); }
</style>
