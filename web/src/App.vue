<template>
  <div id="app">
    <header>
      <h1>ApiGog</h1>
      <p>API测试工具</p>
    </header>
    <main>
      <div class="status">
        <h2>系统状态</h2>
        <p v-if="status">{{ status.message }}</p>
        <p v-else>连接中...</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const status = ref(null)

onMounted(async () => {
  try {
    const response = await axios.get('/api/')
    status.value = response.data
  } catch (error) {
    console.error('无法连接到后端服务:', error)
    status.value = { message: '无法连接到后端服务' }
  }
})
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

.status {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.status h2 {
  margin-bottom: 20px;
  color: #333;
}

.status p {
  font-size: 18px;
  color: #666;
}
</style>
