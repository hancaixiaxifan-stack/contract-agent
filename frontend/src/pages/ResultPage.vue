<script setup>
import { ref, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import axios from "axios"

const route = useRoute()
const router = useRouter()

const source = ref(route.query.source || "text")
const text = ref(source.value === "pdf"
  ? (sessionStorage.getItem("pdfFullText") || "")
  : (sessionStorage.getItem("textFullText") || ""))

const fileName = ref(
  source.value === "text"
    ? (text.value.split("\n")[0].trim().substring(0, 50)) || "文本合同"
    : (route.query.fileName || "未知文件")
)
const contractType = ref(route.query.contractType || "未知合同")
const fileId = ref(route.query.fileId || null)

const recommendedChecks = route.query.checks
  ? route.query.checks.split(",")
  : []

const allChecks = [
  "penalty", "confidentiality", "payment", "dispute", "liability",
  "termination", "non_compete", "privacy", "ip_ownership", "force_majeure",
  "working_hours", "social_insurance", "delivery", "interest_rate", "warranty"
]

const checkLabels = {
  penalty: "违约金", confidentiality: "保密条款", payment: "付款条款",
  dispute: "争议解决", liability: "责任限制", termination: "终止条款",
  non_compete: "竞业禁止", privacy: "隐私保护", ip_ownership: "知识产权",
  force_majeure: "不可抗力", working_hours: "工时制度", social_insurance: "社保福利",
  delivery: "交付条款", interest_rate: "利率条款", warranty: "质保维修"
}

const config = ref({})
allChecks.forEach(key => {
  config.value[key] = recommendedChecks.includes(key)
})

const stance = ref("employee")
const loading = ref(false)

const allSelected = computed(() => Object.values(config.value).every(v => v))
const selectedCount = computed(() => Object.values(config.value).filter(v => v).length)

const selectAll = () => { Object.keys(config.value).forEach(k => { config.value[k] = true }) }
const selectNone = () => { Object.keys(config.value).forEach(k => { config.value[k] = false }) }

const goBack = () => { router.push(source.value === "pdf" ? "/upload/pdf" : "/upload/text") }

const handleAnalyze = async () => {
  if (!text.value) { alert("合同内容为空，无法分析"); return }
  if (!Object.values(config.value).some(v => v)) { alert("请至少选择一个审查点"); return }
  try {
    loading.value = true
    const checkConfig = Object.fromEntries(allChecks.map(k => [k, !!config.value[k]]))
    const res = await axios.post("http://127.0.0.1:8000/analyze-full", {
      file_id: fileId.value,
      text: text.value,
      contract_type: contractType.value,
      stance: stance.value,
      ...checkConfig
    })
    sessionStorage.setItem("contractAnalysisResult", JSON.stringify(res.data.result))
    sessionStorage.removeItem("textFullText")
    sessionStorage.removeItem("pdfFullText")
    router.push({
      path: "/result-detail",
      query: {
        fileName: fileName.value,
        contractType: contractType.value,
        stance: stance.value,
        source: source.value,
        fileId: fileId.value
      }
    })
  } catch (e) {
    console.error("分析失败:", e)
    const errorMsg = e.response?.data?.result?.summary || e.message || "未知错误"
    alert("分析失败: " + errorMsg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">

    <div class="page-header">
      <button class="btn-back" @click="goBack">← 返回</button>
      <div class="page-header-title">
        <h1>审查配置</h1>
        <p>选择审查立场与检查维度，AI 将据此生成报告</p>
      </div>
    </div>

    <!-- Contract Info Card -->
    <div class="card contract-card">
      <div class="contract-icon-wrap">
        <span>{{ source === 'pdf' ? '◈' : '✦' }}</span>
      </div>
      <div class="contract-info">
        <div class="contract-name">{{ fileName }}</div>
        <div class="contract-type-badge">
          <span class="badge badge-done">AI 识别</span>
          {{ contractType }}
        </div>
      </div>
    </div>

    <!-- Stance Card -->
    <div class="card config-card">
      <div class="section-label">审查立场</div>
      <div class="stance-group">
        <label class="stance-card" :class="{ active: stance === 'employee' }">
          <input type="radio" v-model="stance" value="employee" />
          <div class="stance-inner">
            <span class="stance-emoji">👤</span>
            <div>
              <div class="stance-title">求职者 / 乙方</div>
              <div class="stance-desc">侧重保护个人权益</div>
            </div>
          </div>
          <div class="stance-check" v-show="stance === 'employee'">✓</div>
        </label>

        <label class="stance-card" :class="{ active: stance === 'employer' }">
          <input type="radio" v-model="stance" value="employer" />
          <div class="stance-inner">
            <span class="stance-emoji">🏢</span>
            <div>
              <div class="stance-title">用人单位 / 甲方</div>
              <div class="stance-desc">侧重企业风险管控</div>
            </div>
          </div>
          <div class="stance-check" v-show="stance === 'employer'">✓</div>
        </label>
      </div>
    </div>

    <!-- Checks Card -->
    <div class="card config-card">
      <div class="checks-header">
        <div>
          <div class="section-label">审查维度</div>
          <div class="checks-count">
            已选 <strong>{{ selectedCount }}</strong> / {{ allChecks.length }} 项
            <span v-if="recommendedChecks.length > 0" class="ai-tip"> · AI 已预选推荐项</span>
          </div>
        </div>
        <div class="checks-actions">
          <button class="btn-ghost" @click="selectAll">全选</button>
          <span class="sep">·</span>
          <button class="btn-ghost" @click="selectNone">清空</button>
        </div>
      </div>

      <div class="checks-grid">
        <label
          v-for="key in allChecks"
          :key="key"
          class="check-item"
          :class="{ active: config[key], recommended: recommendedChecks.includes(key) }"
        >
          <input type="checkbox" v-model="config[key]" />
          <span class="check-label">{{ checkLabels[key] }}</span>
          <span v-if="config[key]" class="check-tick">✓</span>
          <span v-if="recommendedChecks.includes(key) && !config[key]" class="rec-dot" title="AI推荐"></span>
        </label>
      </div>
    </div>

    <!-- Actions -->
    <div class="bottom-bar">
      <button class="btn btn-secondary" @click="goBack">上一步</button>
      <button class="btn btn-primary btn-lg" @click="handleAnalyze" :disabled="loading">
        <span v-if="loading" class="btn-loading">
          <span class="spinner-sm"></span> 分析中…
        </span>
        <span v-else>开始 AI 分析 →</span>
      </button>
    </div>

  </div>
</template>

<style scoped>
.page {
  max-width: 720px;
  margin: 0 auto;
  padding: 40px 24px 60px;
}

/* Contract Info */
.contract-card {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 14px;
  padding: 16px 20px;
}

.contract-icon-wrap {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-sm);
  font-size: 20px;
  color: var(--gold);
  flex-shrink: 0;
}

.contract-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  word-break: break-all;
  margin-bottom: 4px;
}

.contract-type-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--ink-muted);
}

/* Config Cards */
.config-card {
  margin-bottom: 14px;
  padding: 20px 24px;
}

/* Stance */
.stance-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}

.stance-card {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1.5px solid var(--rule);
  border-radius: var(--r-md);
  cursor: pointer;
  transition: all var(--t-fast) var(--ease);
  background: var(--paper);
}

.stance-card input { display: none; }

.stance-card:hover {
  border-color: var(--ink-soft);
  background: var(--parchment);
}

.stance-card.active {
  border-color: var(--gold);
  background: var(--gold-bg);
  box-shadow: 0 0 0 1px var(--gold-border);
}

.stance-inner {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stance-emoji { font-size: 22px; }

.stance-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
}

.stance-desc {
  font-size: 12px;
  color: var(--ink-muted);
  margin-top: 2px;
}

.stance-check {
  color: var(--gold);
  font-weight: 700;
  font-size: 14px;
}

/* Checks */
.checks-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.checks-count {
  font-size: 12px;
  color: var(--ink-muted);
  margin-top: 4px;
}

.checks-count strong { color: var(--gold); }

.ai-tip { color: var(--risk-low); }

.checks-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-ghost {
  background: none;
  border: none;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--ink-muted);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--r-sm);
  transition: all var(--t-fast) var(--ease);
}

.btn-ghost:hover { color: var(--ink); background: var(--rule-light); }

.sep { color: var(--rule); font-size: 12px; }

.checks-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.check-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1.5px solid var(--rule);
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: all var(--t-fast) var(--ease);
  font-size: 13px;
  color: var(--ink-soft);
  background: var(--paper);
}

.check-item input { display: none; }

.check-item:hover {
  border-color: var(--ink-soft);
  background: var(--parchment);
  color: var(--ink);
}

.check-item.active {
  border-color: var(--gold);
  background: var(--gold-bg);
  color: var(--ink);
}

.check-label { flex: 1; font-weight: 500; }

.check-tick {
  color: var(--gold);
  font-size: 12px;
  font-weight: 700;
}

.rec-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--risk-low);
  flex-shrink: 0;
}

/* Bottom bar */
.bottom-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--rule);
}

.btn-lg { padding: 12px 32px; font-size: 15px; }

.btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.spinner-sm {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
