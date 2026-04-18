<script setup>
import { ref } from "vue"
import axios from "axios"
import { useRouter } from "vue-router"

const router = useRouter()
const file = ref(null)
const isDragover = ref(false)
const fileInput = ref(null)
const loading = ref(false)

const triggerFileInput = () => { fileInput.value.click() }

const handleFile = (e) => {
  const f = e.target.files[0]
  if (f && f.type === "application/pdf") { file.value = f }
  else { alert("请上传PDF文件") }
}

const handleDrop = (e) => {
  isDragover.value = false
  const f = e.dataTransfer.files[0]
  if (f && f.type === "application/pdf") { file.value = f }
  else { alert("请上传PDF文件") }
}

const goBack = () => { router.push("/") }

const handleConfirm = async () => {
  if (!file.value) { alert("请上传PDF文件"); return }
  loading.value = true
  try {
    const reader = new FileReader()
    const fileData = await new Promise((resolve) => {
      reader.onload = (e) => resolve(e.target.result.split(",")[1])
      reader.readAsDataURL(file.value)
    })
    const res = await axios.post("http://127.0.0.1:8000/identify-contract", {
      file_data: fileData,
      file_name: file.value.name,
      file_type: "pdf"
    })
    sessionStorage.setItem("pdfFullText", res.data.full_text || res.data.text_preview || "")
    sessionStorage.setItem("pdfFileId", res.data.file_id || "")
    const recommendedChecks = res.data.recommended_checks || []
    router.push({
      path: "/result",
      query: {
        fileName: res.data.file_name || file.value.name,
        contractType: res.data.contract_type || "未知合同",
        source: "pdf",
        fileId: res.data.file_id,
        checks: recommendedChecks.join(",")
      }
    })
  } catch (e) {
    alert("识别失败，请重试")
    console.error(e)
  }
  loading.value = false
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
</script>

<template>
  <div class="page">

    <div class="page-header">
      <button class="btn-back" @click="goBack">← 返回</button>
      <div class="page-header-title">
        <h1>PDF 合同上传</h1>
        <p>上传 PDF 格式合同，AI 将自动提取文本并识别合同类型</p>
      </div>
    </div>

    <div class="upload-card card">

      <!-- Drop Zone -->
      <div
        class="drop-zone"
        :class="{ dragover: isDragover, 'has-file': !!file }"
        @dragover.prevent="isDragover = true"
        @dragleave.prevent="isDragover = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept="application/pdf"
          @change="handleFile"
          style="display: none"
        />

        <!-- Empty state -->
        <template v-if="!file">
          <div class="dz-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="12" y1="18" x2="12" y2="12"/>
              <line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
          </div>
          <div class="dz-text">拖拽 PDF 文件至此处</div>
          <div class="dz-hint">或点击选择文件 · 最大 50MB</div>
        </template>

        <!-- File selected -->
        <template v-else>
          <div class="file-preview">
            <div class="file-preview-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </div>
            <div class="file-preview-info">
              <div class="file-preview-name">{{ file.name }}</div>
              <div class="file-preview-meta">PDF · {{ formatSize(file.size) }}</div>
            </div>
            <div class="file-preview-check">✓</div>
          </div>
          <div class="dz-change-hint">点击更换文件</div>
        </template>
      </div>

      <div class="upload-footer">
        <div class="editor-hint">
          <span class="hint-dot"></span>
          仅支持 PDF 格式，建议上传原始文本 PDF（非扫描版）
        </div>
        <div class="upload-actions">
          <button class="btn btn-secondary" @click="goBack">取消</button>
          <button
            class="btn btn-primary"
            @click="handleConfirm"
            :disabled="loading || !file"
          >
            <span v-if="loading" class="btn-loading">
              <span class="spinner-sm"></span> 识别中…
            </span>
            <span v-else>确认 →</span>
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.page {
  max-width: 720px;
  margin: 0 auto;
  padding: 40px 24px 60px;
}

.upload-card {
  padding: 0;
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 48px 32px;
  cursor: pointer;
  transition: all var(--t-mid) var(--ease);
  background: var(--paper);
  border-bottom: 1px solid var(--rule);
  position: relative;
}

.drop-zone::after {
  content: '';
  position: absolute;
  inset: 12px;
  border: 2px dashed var(--rule);
  border-radius: var(--r-md);
  transition: all var(--t-mid) var(--ease);
  pointer-events: none;
}

.drop-zone:hover::after,
.drop-zone.dragover::after {
  border-color: var(--gold);
  border-style: solid;
}

.drop-zone.dragover {
  background: var(--gold-bg);
}

.drop-zone.has-file::after { border-style: solid; border-color: var(--gold); }

.dz-icon {
  color: var(--ink-muted);
  margin-bottom: 16px;
  transition: color var(--t-mid) var(--ease), transform var(--t-mid) var(--ease-spring);
}

.drop-zone:hover .dz-icon,
.drop-zone.dragover .dz-icon {
  color: var(--gold);
  transform: translateY(-4px);
}

.dz-text {
  font-size: 15px;
  font-weight: 500;
  color: var(--ink);
  margin-bottom: 6px;
}

.dz-hint {
  font-size: 12px;
  color: var(--ink-muted);
}

/* File Preview */
.file-preview {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-md);
  padding: 16px 20px;
  min-width: 300px;
  margin-bottom: 12px;
}

.file-preview-icon {
  color: var(--gold);
  flex-shrink: 0;
}

.file-preview-info {
  flex: 1;
  min-width: 0;
}

.file-preview-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-preview-meta {
  font-size: 12px;
  color: var(--ink-muted);
  margin-top: 2px;
}

.file-preview-check {
  color: var(--risk-low);
  font-weight: 700;
  font-size: 16px;
  flex-shrink: 0;
}

.dz-change-hint {
  font-size: 12px;
  color: var(--ink-muted);
}

/* Footer */
.upload-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
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
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--gold);
  flex-shrink: 0;
}

.upload-actions { display: flex; gap: 10px; }

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
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
