import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  if (config.data instanceof FormData) {
    if (config.headers) {
      delete config.headers['Content-Type']
      delete config.headers['content-type']
    }
  }
  return config
})

const storedToken = localStorage.getItem('auth_token')
if (storedToken) {
  api.defaults.headers.common.Authorization = `Bearer ${storedToken}`
}

export function attachToken(token) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common.Authorization
  }
}

export function formatApiError(detail, fallbackMessage) {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  return fallbackMessage
}

export default api
