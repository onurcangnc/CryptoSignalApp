// src/api/index.js
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : `${window.location.protocol}//${window.location.host}`

export const api = {
  request: async (endpoint, options = {}) => {
    const token = localStorage.getItem('token')
    const headers = { 'Content-Type': 'application/json', ...options.headers }
    if (token) headers['Authorization'] = `Bearer ${token}`
    
    const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers })
    
    if (response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.reload()
    }
    return response
  },
  get: (endpoint) => api.request(endpoint),
  post: (endpoint, data) => api.request(endpoint, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  put: (endpoint, data) => api.request(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  delete: (endpoint) => api.request(endpoint, {
    method: 'DELETE'
  }),
}

export default api
