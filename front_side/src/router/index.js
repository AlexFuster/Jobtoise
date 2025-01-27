import { createRouter, createWebHashHistory } from 'vue-router'
import JobBoard from '@/components/JobBoard.vue'
const routes = [
  {
    path: '/',
    name: 'JobBoard',
    component: JobBoard
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
