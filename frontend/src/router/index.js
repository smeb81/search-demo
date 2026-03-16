import { createRouter, createWebHistory } from 'vue-router'
import SearchPage from '../views/SearchPage.vue'
import DocumentsPage from '../views/DocumentsPage.vue'

const routes = [
  {
    path: '/',
    name: 'search',
    component: SearchPage
  },
  {
    path: '/documents',
    name: 'documents',
    component: DocumentsPage
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
