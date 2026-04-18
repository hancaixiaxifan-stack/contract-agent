<script setup>
import { ref } from "vue"
import axios from "axios"
import { useRouter } from "vue-router"

const router = useRouter()
const text = ref("")
const loading = ref(false)

const goBack = () => { router.push("/") }

const handleConfirm = async () => {
  if (!text.value.trim()) { alert("请输入合同内容"); return }
  loading.value = true
  try {
    const res = await axios.post("http://127.0.0.1:8000/identify-contract", { text: text.value })
    sessionStorage.setItem("textFullText", text.value)
    const recommendedChecks = res.data.recommended_checks || []
    router.push({
      path: "/result",
      query: {
        fileName: res.data.file_name || "文本合同",
        contractType: res.data.contract_type || "未知合同",
        source: "text",
        checks: recommendedChecks.join(",")
      }
    })
  } catch (e) {
    alert("识别失败，请重试")
    console.error(e)
  }
  loading.value = false
}

const charCount = () => text.value.length
</script>

<template>
  <div class="page">

    <div class="page-header">
      <button class="btn-back" @click="goBack">← 返回</button>
      <div class="page-header-title">
        <h1>文本合同上传</h1>
        <p>粘贴或输入合同正文，AI将自动识别合同类型</p>
      </div>
    </div>

    <div class="card editor-card">
      <div class="editor-top">
        <span class="section-label">合同文本</span>
        <span class="char-count">{{ charCount() }} 字</span>
      </div>

      <textarea
        v-model="text"
        class="editor-area"
        placeholder="将合同文本粘贴至此处…&#10;&#10;AI 将自动分析合同类型，并为您推荐适合的审查维度。"
        spellcheck="false"
      />

      <div class="editor-footer">
        <div class="editor-hint">
          <span class="hint-dot"></span>
          支持劳动合同、租赁合同、购销合同等各类合同
        </div>
        <div class="editor-actions">
          <button class="btn btn-secondary" @click="goBack">取消</button>
          <button
            class="btn btn-primary"
            @click="handleConfirm"
            :disabled="loading || !text.trim()"
          >
            <span v-if="loading" class="btn-loading">
              <span class="spinner-sm"></span> 识别中…
            </span>
            <span v-else>确认 →</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Tips -->
    <div class="tips-row">
      <div class="tip-item">
        <span class="tip-icon">◉</span>
        <span>完整粘贴合同文本，分析更准确</span>
      </div>
      <div class="tip-item">
        <span class="tip-icon">◉</span>
        <span>支持中英文合同</span>
      </div>
      <div class="tip-item">
        <span class="tip-icon">◉</span>
        <span>建议文本长度 500 字以上</span>
      </div>
    </div>

  </div>
</template>

<style scoped>
.page {
  max-width: 840px;
  margin: 0 auto;
  padding: 40px 24px 60px;
}

.editor-card {
  padding: 0;
  overflow: hidden;
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-md);
}

.editor-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--rule);
  background: var(--parchment);
}

.char-count {
  font-size: 12px;
  color: var(--ink-muted);
  font-variant-numeric: tabular-nums;
}

.editor-area {
  display: block;
  width: 100%;
  min-height: 380px;
  padding: 24px;
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.8;
  color: var(--ink);
  background: var(--paper);
  border: none;
  resize: vertical;
  outline: none;
  transition: background var(--t-fast) var(--ease);
  box-sizing: border-box;
}

.editor-area::placeholder {
  color: var(--ink-muted);
  opacity: 0.6;
}

.editor-area:focus { background: #fffffe; }

.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid var(--rule);
  background: var(--parchment);
  gap: 16px;
  flex-wrap: wrap;
}

.editor-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--ink-muted);
}

.hint-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
  flex-shrink: 0;
}

.editor-actions {
  display: flex;
  gap: 10px;
}

.btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.spinner-sm {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Tips */
.tips-row {
  display: flex;
  gap: 0;
  margin-top: 20px;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--r-lg);
  overflow: hidden;
}

.tip-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  font-size: 12px;
  color: var(--ink-muted);
  border-right: 1px solid var(--rule);
}

.tip-item:last-child { border-right: none; }

.tip-icon {
  color: var(--gold);
  font-size: 10px;
  flex-shrink: 0;
}
</style>
