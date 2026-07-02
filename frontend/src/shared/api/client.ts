import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const httpClient = axios.create({
  baseURL: API_BASE_URL,
})

httpClient.interceptors.request.use((config) => {
  const openaiKey  = localStorage.getItem('openai_key')
  const youtubeKey = localStorage.getItem('youtube_key')
  if (openaiKey)  config.headers['X-OpenAI-Key']  = openaiKey
  if (youtubeKey) config.headers['X-YouTube-Key'] = youtubeKey
  return config
})
