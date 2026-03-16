import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const getDocuments = () => api.get('/documents')

export const getDocument = (id) => api.get(`/documents/${id}`)

export const addDocument = (data) => api.post('/documents', data)

export const deleteDocument = (id) => api.delete(`/documents/${id}`)

export const searchDocuments = (query, topK = 5) => api.post('/search', {
  query,
  top_k: topK
})

export const importFolder = (folderPath) => api.post('/documents/import', {
  folder_path: folderPath
})

export default api
