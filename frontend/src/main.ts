import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { initializeCSRF } from './api'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 在应用启动时初始化CSRF token
const initializeApp = async () => {
  try {
    // 使用API模块的初始化函数
    await initializeCSRF()
    console.log('CSRF token initialized on app start')
  } catch (error) {
    console.warn('Failed to initialize CSRF token on app start:', error)
  }
  
  app.mount('#app')
}

initializeApp()
