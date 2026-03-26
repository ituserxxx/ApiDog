<template>
  <div id="app">
    <header>
      <h1>ApiDog</h1>
      <p>API测试工具</p>
    </header>
    <main>

      <div class="panel card">
        <h2>API 测试</h2>
        <div class="form-grid">
          <div class="field">
            <label>URL 地址</label>
            <input v-model="baseUrl" type="text" placeholder="例如：http://localhost:5000" />
          </div>

          <div class="field">
            <label>接口路由</label>
            <input v-model="apiPath" type="text" placeholder="例如：/api/health" />
          </div>

          <div class="field">
            <label>请求方法</label>
            <select v-model="method">
              <option value="GET">GET</option>
              <option value="POST">POST</option>
            </select>
          </div>

          <div class="field span-2">
            <div class="field-header">
              <label>Header（JSON）</label>
              <button class="btn-format" @click="formatJson('headers')">格式化</button>
            </div>
            <textarea
              v-model="headersJson"
              rows="4"
              placeholder='例如：{"Authorization":"Bearer xxx"}'
              :class="{ 'input-error': headersError }"
              @blur="validateJson('headers')"
            ></textarea>
            <div class="json-error" v-if="headersError">{{ headersError }}</div>
          </div>

          <div class="field" v-if="method === 'GET'">
            <div class="field-header">
              <label>GET 参数（JSON）</label>
              <button class="btn-format" @click="formatJson('getParams')">格式化</button>
            </div>
            <textarea
              v-model="getParamsJson"
              rows="4"
              placeholder='例如：{"q":"test"}'
              :class="{ 'input-error': getParamsError }"
              @blur="validateJson('getParams')"
            ></textarea>
            <div class="json-error" v-if="getParamsError">{{ getParamsError }}</div>
          </div>

          <div class="field" v-if="method === 'POST'">
            <div class="field-header">
              <label>POST 参数（JSON）</label>
              <button class="btn-format" @click="formatJson('postParams')">格式化</button>
            </div>
            <textarea
              v-model="postParamsJson"
              rows="4"
              placeholder='例如：{"name":"tom"}'
              :class="{ 'input-error': postParamsError }"
              @blur="validateJson('postParams')"
            ></textarea>
            <div class="json-error" v-if="postParamsError">{{ postParamsError }}</div>
          </div>
        </div>

        <div class="actions">
          <button class="primary" :disabled="loading" @click="sendRequest">
            {{ loading ? '请求中...' : '发送请求' }}
          </button>
          <div class="hint" v-if="errorText">{{ errorText }}</div>
        </div>

        <div class="response">
          <div class="response-head">
            <div><b>响应状态：</b>{{ responseStatusText }}</div>
            <div class="muted" v-if="elapsedMs !== null"><b>耗时：</b>{{ elapsedMs }} ms</div>
          </div>
          <pre class="response-body" v-if="prettyResponse">{{ prettyResponse }}</pre>
          <div class="muted" v-else>暂无响应</div>
        </div>

        <!-- 完整请求/响应日志 -->
        <div class="request-log" v-if="requestLog">
          <div class="log-header">
            <h3>完整请求 & 响应</h3>
            <button class="btn-copy" @click="copyLog">
              {{ copyBtnText }}
            </button>
          </div>
          <pre class="log-body">{{ requestLog }}</pre>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'


const baseUrl = ref('http://localhost:5000')
const apiPath = ref('/api/health')
const method = ref('GET')

const headersJson = ref('{}')
const getParamsJson = ref('{}')
const postParamsJson = ref('{}')

const headersError = ref('')
const getParamsError = ref('')
const postParamsError = ref('')

const jsonFieldMap = {
  headers: { value: headersJson, error: headersError, label: 'Header' },
  getParams: { value: getParamsJson, error: getParamsError, label: 'GET 参数' },
  postParams: { value: postParamsJson, error: postParamsError, label: 'POST 参数' },
}

const loading = ref(false)
const errorText = ref('')

function validateJson(field) {
  const { value, error } = jsonFieldMap[field]
  const raw = String(value.value ?? '').trim()
  if (!raw) {
    error.value = ''
    return true
  }
  try {
    JSON.parse(raw)
    error.value = ''
    return true
  } catch (e) {
    error.value = `${jsonFieldMap[field].label} JSON 格式有误：${e.message}`
    return false
  }
}

function formatJson(field) {
  const { value, error } = jsonFieldMap[field]
  const raw = String(value.value ?? '').trim()
  if (!raw) return
  try {
    const parsed = JSON.parse(raw)
    value.value = JSON.stringify(parsed, null, 2)
    error.value = ''
  } catch (e) {
    error.value = `${jsonFieldMap[field].label} JSON 格式有误，无法格式化：${e.message}`
  }
}

const responseStatusText = ref('')
const elapsedMs = ref(null)
const prettyResponse = ref('')
const requestLog = ref('')
const copyBtnText = ref('一键复制')

function joinUrl(base, path) {
  if (!base) return path || ''
  if (!path) return base

  const hasSlashAtEnd = base.endsWith('/')
  const hasSlashAtStart = path.startsWith('/')
  if (hasSlashAtEnd && hasSlashAtStart) return base + path.slice(1)
  if (!hasSlashAtEnd && !hasSlashAtStart) return base + '/' + path
  return base + path
}

function parseJsonOrThrow(text, label) {
  const raw = String(text ?? '').trim()
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw)
    return parsed
  } catch (e) {
    throw new Error(`${label} JSON 格式不正确：${e?.message || e}`)
  }
}

function prettyPrint(data) {
  if (data === undefined) return ''
  if (data === null) return 'null'

  if (typeof data === 'string') {
    try {
      return JSON.stringify(JSON.parse(data), null, 2)
    } catch {
      return data
    }
  }

  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

async function sendRequest() {
  loading.value = true
  errorText.value = ''
  responseStatusText.value = ''
  elapsedMs.value = null
  prettyResponse.value = ''
  requestLog.value = ''

  const fullUrl = joinUrl(baseUrl.value, apiPath.value)

  let headers = {}
  let getParams = {}
  let postParams = {}

  try {
    headers = parseJsonOrThrow(headersJson.value, 'Header')
    getParams = parseJsonOrThrow(getParamsJson.value, 'GET 参数')
    postParams = parseJsonOrThrow(postParamsJson.value, 'POST 参数')
  } catch (e) {
    errorText.value = e?.message || String(e)
    loading.value = false
    return
  }

  // axios 对 headers 的类型容错有限：这里强制确保是对象
  if (headers === null || typeof headers !== 'object' || Array.isArray(headers)) {
    errorText.value = 'Header 必须是 JSON 对象（例如：{"k":"v"}）'
    loading.value = false
    return
  }

  const config = {
    method: method.value,
    url: fullUrl,
    headers: { ...headers },
    validateStatus: () => true // 让 4xx/5xx 也能拿到响应并显示
  }

  if (method.value === 'GET') {
    config.params = getParams
  } else {
    // POST 以 JSON body 发送
    config.data = postParams
    config.headers['Content-Type'] = config.headers['Content-Type'] || 'application/json'
  }

  const start = Date.now()
  try {
    const resp = await axios.request(config)
    const end = Date.now()

    responseStatusText.value = `${resp.status} ${resp.statusText || ''}`.trim()
    elapsedMs.value = end - start
    prettyResponse.value = prettyPrint(resp.data)
    requestLog.value = buildLog(method.value, fullUrl, headers, method.value === 'GET' ? getParams : undefined, method.value === 'POST' ? postParams : undefined, resp.status, resp.data, end - start)
  } catch (e) {
    const end = Date.now()
    elapsedMs.value = end - start

    const resp = e?.response
    const statusCode = resp?.status
    responseStatusText.value = resp
      ? `${statusCode} ${resp.statusText || ''}`.trim()
      : '请求失败'

    prettyResponse.value = prettyPrint(resp?.data ?? e?.message)
    errorText.value = '请求失败，请检查 URL/路由/参数或是否跨域允许'
    requestLog.value = buildLog(method.value, fullUrl, headers, method.value === 'GET' ? getParams : undefined, method.value === 'POST' ? postParams : undefined, statusCode, resp?.data ?? e?.message, end - start)
  } finally {
    loading.value = false
  }
}

function buildLog(method, url, headers, params, body, statusCode, responseData, elapsed) {
  const lines = []
  const time = new Date().toLocaleString('zh-CN')
  lines.push(`========== 请求时间: ${time} ==========`)
  lines.push('')
  lines.push('--- 请求 ---')
  lines.push(`${method} ${url}`)
  lines.push('')
  lines.push(`Headers:`)
  lines.push(JSON.stringify(headers, null, 2))
  if (params && Object.keys(params).length > 0) {
    lines.push('')
    lines.push(`Query Params:`)
    lines.push(JSON.stringify(params, null, 2))
  }
  if (body !== undefined && method !== 'GET') {
    lines.push('')
    lines.push(`Body:`)
    lines.push(JSON.stringify(body, null, 2))
  }
  lines.push('')
  lines.push('--- 响应 ---')
  lines.push(`Status: ${statusCode}`)
  lines.push(`耗时: ${elapsed} ms`)
  lines.push('')
  lines.push(`Response:`)
  lines.push(prettyPrint(responseData))
  lines.push('')
  lines.push('==========================================')
  return lines.join('\n')
}

async function copyLog() {
  if (!requestLog.value) return
  try {
    await navigator.clipboard.writeText(requestLog.value)
    copyBtnText.value = '已复制!'
    setTimeout(() => { copyBtnText.value = '一键复制' }, 2000)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = requestLog.value
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    copyBtnText.value = '已复制!'
    setTimeout(() => { copyBtnText.value = '一键复制' }, 2000)
  }
}





</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Helvetica Neue', sans-serif;
  background-color: #f5f5f5;
}

#app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

header {
  text-align: center;
  margin-bottom: 40px;
  padding: 40px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
}

header h1 {
  font-size: 48px;
  margin-bottom: 10px;
}

header p {
  font-size: 20px;
  opacity: 0.9;
}



.card {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.card h2 {
  margin-bottom: 20px;
  color: #333;
}

.card p {
  font-size: 18px;
  color: #666;
}

.panel {
  text-align: left;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.field label {
  display: block;
  font-size: 14px;
  color: #555;
  margin-bottom: 8px;
}

.field-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.field-header label {
  margin-bottom: 0;
}

.btn-format {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 4px 12px;
  background: #fff;
  color: #667eea;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-format:hover {
  background: #667eea;
  color: #fff;
  border-color: #667eea;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  background: #fafafa;
  transition: border-color 0.2s;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  border-color: #667eea;
}

.field textarea {
  resize: vertical;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.field textarea.input-error {
  border-color: #d93025;
  background: #fff5f5;
}

.json-error {
  color: #d93025;
  font-size: 12px;
  margin-top: 6px;
  padding: 4px 0;
}

.span-2 {
  grid-column: span 2;
}

.actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 18px 0;
}

.primary {
  border: none;
  border-radius: 10px;
  padding: 12px 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 16px;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(118, 75, 162, 0.2);
}

.primary:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.hint {
  color: #d93025;
  font-size: 14px;
}

.response {
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 16px;
  background: #fcfcfc;
}

.response-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12px;
}

.muted {
  color: #777;
  font-size: 14px;
}

.response-body {
  white-space: pre-wrap;
  word-break: break-word;
  background: #0b1020;
  color: #e5e7eb;
  border-radius: 8px;
  padding: 14px;
  max-height: 420px;
  overflow: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono',
    'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.request-log {
  margin-top: 20px;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 16px;
  background: #fcfcfc;
}

.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.log-header h3 {
  color: #333;
  font-size: 16px;
}

.btn-copy {
  border: 1px solid #667eea;
  border-radius: 8px;
  padding: 6px 16px;
  background: #fff;
  color: #667eea;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-copy:hover {
  background: #667eea;
  color: #fff;
}

.log-body {
  white-space: pre-wrap;
  word-break: break-word;
  background: #0b1020;
  color: #e5e7eb;
  border-radius: 8px;
  padding: 14px;
  max-height: 500px;
  overflow: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono',
    'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}
</style>
