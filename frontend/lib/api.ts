export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

let _onUnauthorized: (() => void) | null = null

export function setOnUnauthorized(fn: () => void) {
  _onUnauthorized = fn
}

async function refreshAccessToken(refreshToken: string): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) return null
    const data = await res.json()
    return data.access_token
  } catch {
    return null
  }
}

export async function apiClient(endpoint: string, options: RequestInit & { _retry?: boolean } = {}) {
  let tokens: { access_token: string; refresh_token: string } | null = null

  if (typeof window !== 'undefined') {
    try {
      const raw = localStorage.getItem('auth_tokens')
      if (raw) tokens = JSON.parse(raw)
    } catch {}
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(tokens?.access_token ? { Authorization: `Bearer ${tokens.access_token}` } : {}),
    ...options.headers,
  }

  let res: Response
  try {
    res = await fetch(`${API_BASE}/api/v1${endpoint}`, { ...options, headers })
  } catch {
    throw new Error('Cannot reach server. Is the backend running?')
  }

  if (res.status === 401 && tokens?.refresh_token && !options._retry) {
    const newToken = await refreshAccessToken(tokens.refresh_token)
    if (newToken && typeof window !== 'undefined') {
      tokens.access_token = newToken
      localStorage.setItem('auth_tokens', JSON.stringify(tokens))

      const retryHeaders: HeadersInit = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${newToken}`,
        ...options.headers,
      }
      try {
        res = await fetch(`${API_BASE}/api/v1${endpoint}`, { ...options, headers: retryHeaders })
      } catch {
        throw new Error('Cannot reach server after token refresh.')
      }

      if (res.status === 204) return null
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      return res.json()
    }

    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_tokens')
      if (_onUnauthorized) _onUnauthorized()
      else window.location.href = '/login'
    }
    throw new Error('Session expired. Please sign in again.')
  }

  if (res.status === 204) return null
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export function getStoredTokens() {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem('auth_tokens')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}