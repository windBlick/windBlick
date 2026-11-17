/**
 * Minimal HTTP client. All backend calls go through here so the base URL,
 * auth headers and error format live in one place once the contract is known.
 *
 * Configure in .env.local:
 *   VITE_API_BASE_URL=https://api.example.org/v1
 *   VITE_USE_MOCKS=false
 */

export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '/api'
export const USE_MOCKS: boolean = (import.meta.env.VITE_USE_MOCKS ?? 'true') !== 'false'

export class ApiError extends Error {
  readonly status: number
  readonly code?: string

  constructor(status: number, message: string, code?: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init.body && !(init.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
  })
  if (!res.ok) {
    // TODO: adapt to the backend's error format from the API contract
    let message = res.statusText
    let code: string | undefined
    try {
      const body = await res.json()
      message = body.message ?? message
      code = body.code
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, message, code)
  }
  return res.json() as Promise<T>
}

/** Simulated latency for mocks so loading states are visible. */
export const mockDelay = (ms = 400) => new Promise((r) => setTimeout(r, ms))
