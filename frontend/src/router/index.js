import { createRouter, createWebHistory } from 'vue-router'
import SearchPage from '../views/SearchPage.vue'
import SearchResultPage from '../views/SearchResultPage.vue'
import DocumentsPage from '../views/DocumentsPage.vue'

const routes = [
  {
    path: '/',
    name: 'search',
    component: SearchPage
  },
  {
    path: '/search',
    name: 'search-result',
    component: SearchResultPage
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
