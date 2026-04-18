<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import axios from "axios"

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const result = ref(null)
const fileName = ref("")
const contractType = ref("")
const source = ref("text")
const fileId = ref(null)
const textContent = ref("")
const showSaveDialog = ref(false)
const activeRiskIndex = ref(-1)

onMounted(async () => {
  const storedResult = sessionStorage.getItem("contractAnalysisResult")
  if (storedResult) {
    try { result.value = JSON.parse(storedResult) }
    catch { result.value = { risks: [], summary: "数据解析失败" } }
    if (!result.value.risks) result.value.risks = []
    if (!result.value.summary) result.value.summary = "无评估结果"

    fileName.value = route.query.fileName || "未知文件"
    contractType.value = route.query.contractType || "未知合同"
    source.value = route.query.source || "text"
    fileId.value = route.query.fileId ? parseInt(route.query.fileId) : null

    if (source.value === "text") {
      textContent.value = sessionStorage.getItem("textFullText") || ""
    }
  } else {
    alert("未找到分析结果")
    router.push("/")
  }
  loading.value = false
})

const getLevelClass = (level) => ({ high: "badge-high", medium: "badge-medium", low: "badge-low" }[level] || "")
const getLevelText = (level) => ({ high: "高风险", medium: "中等风险", low: "低风险" }[level] || "未知")

const highCount = () => result.value?.risks?.filter(r => r.level === 'high').length || 0
const medCount = () => result.value?.risks?.filter(r => r.level === 'medium').length || 0
const lowCount = () => result.value?.risks?.filter(r => r.level === 'low').length || 0

const goReview = () => { router.push(source.value === "pdf" ? "/upload/pdf" : "/upload/text") }
const goHome = () => { showSaveDialog.value = true }

const handleSave = async (save) => {
  showSaveDialog.value = false
  if (save) {
    if (source.value === "pdf" && fileId.value) {
      try {
        await axios.post("http://127.0.0.1:8000/confirm-save", null, { params: { file_id: fileId.value, contract_type: contractType.value } })
      } catch (e) { console.error("保存失败:", e) }
    } else if (source.value === "text" && textContent.value) {
      const textFileName = fileName.value.endsWith(".txt") ? fileName.value : fileName.value + ".txt"
      try {
        await axios.post("http://127.0.0.1:8000/save-text", {
          file_name: textFileName,
          text_content: textContent.value,
          contract_type: contractType.value,
          stance: result.value.stance || "employee",
          result_data: result.value
        })
      } catch (e) { console.error("保存失败:", e) }
    }
  }
  sessionStorage.removeItem("contractAnalysisResult")
  sessionStorage.removeItem("pdfFullText")
  sessionStorage.removeItem("pdfFileId")
  sessionStorage.removeItem("textFullText")
  router.push("/")
}
</script>

<template>
  <div class="page-wide">

    <!-- Header -->
    <div class="result-header">
      <div class="result-header-left">
        <h1>审查报告</h1>
        <p v-if="result && result.stance" class="stance-badge" :class="result.stance === 'employee' ? 'stance-employee' : 'stance-employer'">
          {{ result.stance === 'employee' ? '👤 求职者' : '🏢 用人单位' }}
        </p>
      </div>
      <div class="result-header-actions">
        <button class="btn btn-secondary" @click="goReview">重新配置</button>
        <button class="btn btn-primary" @click="goHome">完成并返回</button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载报告中…</span>
    </div>

    <div v-else-if="result" class="result-body">

      <!-- Summary Bar -->
      <div class="summary-bar">
        <div class="summary-file">
          <div class="summary-file-icon">{{ source === 'pdf' ? '◈' : '✦' }}</div>
          <div>
            <div class="summary-name">{{ fileName }}</div>
            <div class="summary-type">{{ contractType }}</div>
          </div>
        </div>

        <div class="summary-stats">
          <div class="stat-chip stat-high" v-if="highCount() > 0">
            <span>●</span> {{ highCount() }} 高风险
          </div>
          <div class="stat-chip stat-med" v-if="medCount() > 0">
            <span>●</span> {{ medCount() }} 中风险
          </div>
          <div class="stat-chip stat-low" v-if="lowCount() > 0">
            <span>●</span> {{ lowCount() }} 低风险
          </div>
          <div class="stat-chip stat-ok" v-if="!result.risks?.length">
            <span>✓</span> 无明显风险
          </div>
        </div>

        <div class="summary-text">
          {{ result.summary }}
        </div>
      </div>

      <!-- Main content: doc + risks -->
      <div class="main-split">

        <!-- Left: Document -->
        <div class="doc-panel">
          <div class="panel-header">
            <span>{{ source === 'pdf' ? '📄 PDF 预览' : '📝 文本预览' }}</span>
          </div>

          <iframe
            v-if="source === 'pdf' && fileId"
            :src="`http://127.0.0.1:8000/pdf/${fileId}`"
            class="doc-iframe"
            title="PDF预览"
          />

          <pre v-else-if="source === 'text' && textContent" class="doc-text">{{ textContent }}</pre>
        </div>

        <!-- Right: Risk list -->
        <div class="risks-panel">
          <div class="panel-header">
            <span>审查结果</span>
            <span class="risks-count">{{ result.risks?.length || 0 }} 项</span>
          </div>

          <div class="risks-body">
            <div
              v-for="(risk, index) in result.risks"
              :key="index"
              class="risk-card"
              :class="{ active: activeRiskIndex === index }"
              @click="activeRiskIndex = index"
            >
              <div class="risk-top">
                <div class="risk-point">{{ risk.point }}</div>
                <span class="badge" :class="getLevelClass(risk.level)">{{ getLevelText(risk.level) }}</span>
              </div>
              <div class="risk-location">📍 {{ risk.clause_location }}</div>
              <blockquote class="risk-quote">{{ risk.evidence }}</blockquote>
            </div>

            <div v-if="!result.risks?.length" class="no-risk">
              <div class="no-risk-icon">✓</div>
              <div class="no-risk-text">未发现明显风险</div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Save Dialog -->
    <div v-if="showSaveDialog" class="dialog-overlay" @click.self="showSaveDialog = false">
      <div class="dialog">
        <div class="dialog-icon">💾</div>
        <div class="dialog-title">保存此次审查结果？</div>
        <div class="dialog-desc">保存后可在历史记录中随时查阅</div>
        <div class="dialog-actions">
          <button class="btn btn-secondary" @click="handleSave(false)">不保存</button>
          <button class="btn btn-primary" @click="handleSave(true)">保存</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.page-wide {
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px 24px 40px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.result-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--rule);
  gap: 16px;
  flex-wrap: wrap;
}

.result-header-left h1 {
  font-size: 28px;
  color: var(--ink);
  margin-bottom: 4px;
}

.result-header-left p {
  font-size: 13px;
  color: var(--ink-muted);
}

.stance-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  margin-top: 8px;
  border: 1px solid;
}

.stance-employee {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.3);
  color: #3b82f6;
}

.stance-employer {
  background: rgba(184, 146, 42, 0.08);
  border-color: rgba(184, 146, 42, 0.3);
  color: #b8922a;
}

.result-header-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

/* Summary Bar */
.summary-bar {
  background: var(--paper);
  border: 1px solid var(--rule);
  border-left: 4px solid var(--gold);
  border-radius: var(--r-lg);
  padding: 18px 24px;
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
  gap: 24px;
  flex-wrap: wrap;
  box-shadow: var(--shadow-sm);
}

.summary-file {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.summary-file-icon {
  width: 40px; height: 40px;
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--gold);
}

.summary-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
}

.summary-type {
  font-size: 12px;
  color: var(--ink-muted);
  margin-top: 2px;
}

.summary-stats {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.stat-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid;
}

.stat-high  { background: var(--risk-high-bg);  color: var(--risk-high);  border-color: var(--risk-high-border); }
.stat-med   { background: var(--risk-med-bg);   color: var(--risk-med);   border-color: var(--risk-med-border);  }
.stat-low   { background: var(--risk-low-bg);   color: var(--risk-low);   border-color: var(--risk-low-border);  }
.stat-ok    { background: var(--risk-low-bg);   color: var(--risk-low);   border-color: var(--risk-low-border);  }

.summary-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-soft);
  min-width: 200px;
}

/* Main split */
.main-split {
  display: flex;
  gap: 16px;
  flex: 1;
  height: calc(100vh - 240px);
  min-height: 500px;
}

/* Document panel */
.doc-panel {
  flex: 1;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--r-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-sm);
}

.doc-iframe {
  flex: 1;
  width: 100%;
  border: none;
}

.doc-text {
  flex: 1;
  overflow: auto;
  padding: 20px;
  margin: 0;
  font-family: var(--font-body);
  font-size: 13px;
  line-height: 1.8;
  color: var(--ink-soft);
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Risks panel */
.risks-panel {
  width: 400px;
  flex-shrink: 0;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--r-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-sm);
}

.risks-count {
  margin-left: auto;
  font-size: 12px;
  color: var(--ink-muted);
  font-weight: 400;
}

.risks-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.risk-card {
  padding: 14px;
  border: 1.5px solid var(--rule);
  border-radius: var(--r-md);
  margin-bottom: 10px;
  cursor: pointer;
  transition: all var(--t-fast) var(--ease);
  background: var(--paper);
}

.risk-card:hover {
  border-color: var(--ink-soft);
  box-shadow: var(--shadow-xs);
}

.risk-card.active {
  border-color: var(--gold);
  background: var(--gold-bg);
  box-shadow: 0 0 0 1px var(--gold-border);
}

.risk-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.risk-point {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  flex: 1;
}

.risk-location {
  font-size: 11px;
  color: var(--ink-muted);
  margin-bottom: 8px;
}

.risk-quote {
  margin: 0;
  font-size: 12px;
  color: var(--ink-soft);
  font-style: italic;
  background: var(--parchment);
  padding: 8px 10px;
  border-radius: var(--r-sm);
  border-left: 2px solid var(--gold-border);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.5;
}

.risk-card.active .risk-quote {
  -webkit-line-clamp: unset;
  display: block;
}

/* No risk */
.no-risk {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.no-risk-icon {
  width: 56px; height: 56px;
  background: var(--risk-low-bg);
  border: 1px solid var(--risk-low-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: var(--risk-low);
  margin-bottom: 14px;
}

.no-risk-text {
  font-size: 14px;
  color: var(--ink-muted);
}

/* Save Dialog */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(26,31,46,0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: fadeIn var(--t-mid) var(--ease);
}

@keyframes fadeIn { from { opacity: 0; } }

.dialog {
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--r-xl);
  padding: 36px 32px;
  min-width: 340px;
  box-shadow: var(--shadow-xl);
  text-align: center;
  animation: slideUp var(--t-mid) var(--ease-spring);
}

@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } }

.dialog-icon { font-size: 36px; margin-bottom: 12px; }

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 8px;
}

.dialog-desc {
  font-size: 14px;
  color: var(--ink-muted);
  margin-bottom: 24px;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
