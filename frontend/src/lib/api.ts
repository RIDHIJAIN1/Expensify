const NO_REFRESH = [
  '/api/auth/login',
  '/api/auth/signup',
  '/api/auth/refresh',
  '/api/auth/logout',
]

let refreshPromise: Promise<boolean> | null = null

function refresh(): Promise<boolean> {
  // Single-flight: concurrent 401s share one refresh request.
  if (!refreshPromise) {
    refreshPromise = fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' })
      .then((r) => r.ok)
      .catch(() => false)
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

export async function api<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const doFetch = () => fetch(path, { credentials: 'include', ...options })

  let res = await doFetch()

  // On 401, silently refresh once and retry. If refresh fails, force re-login.
  if (res.status === 401 && !NO_REFRESH.some((p) => path.startsWith(p))) {
    const ok = await refresh()
    if (ok) {
      res = await doFetch()
    } else {
      window.dispatchEvent(new Event('auth:unauthorized'))
      throw new Error('Your session has expired. Please sign in again.')
    }
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }

  if (res.status === 204) return undefined as T

  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return (await res.json()) as T
  return res as unknown as T
}

export async function uploadFile(file: File) {
  const fd = new FormData()
  fd.append('file', file)
  return api<import('./types').Upload>('/api/uploads', { method: 'POST', body: fd })
}

export async function download(path: string, filename: string): Promise<void> {
  let res = await fetch(path, { credentials: 'include' })
  if (res.status === 401) {
    if (await refresh()) res = await fetch(path, { credentials: 'include' })
    else {
      window.dispatchEvent(new Event('auth:unauthorized'))
      throw new Error('Your session has expired. Please sign in again.')
    }
  }
  if (!res.ok) throw new Error('Download failed')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
