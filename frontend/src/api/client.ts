import type { ProblemDetails } from '../types/contract'

/**
 * HTTP plumbing shared by all API modules.
 *
 * In development, Vite proxies /api to the backend (see vite.config.ts), so
 * requests stay same-origin. Set VITE_API_BASE_URL only when the frontend is
 * served from a different origin than the API.
 */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''
export const USE_MOCKS: boolean = (import.meta.env.VITE_USE_MOCKS ?? 'true') !== 'false'

/** An RFC 9457 problem returned by the API (or synthesised for transport failures). */
export class ApiProblem extends Error {
  readonly problem: ProblemDetails

  constructor(problem: ProblemDetails) {
    super(problem.detail || problem.title)
    this.problem = problem
  }

  get code(): string {
    return this.problem.code
  }

  get status(): number {
    return this.problem.status
  }
}

function syntheticProblem(status: number, code: string, detail: string): ApiProblem {
  return new ApiProblem({ type: 'about:blank', title: code, status, detail, request_id: '', code, errors: [] })
}

/** POST multipart form data and parse a JSON or problem+json response. */
export async function postForm<T>(path: string, form: FormData): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      // Let the browser set the multipart boundary; only declare what we accept.
      headers: { Accept: 'application/json, application/problem+json' },
      body: form,
    })
  } catch {
    throw syntheticProblem(0, 'NETWORK_ERROR', 'The server could not be reached. Check your connection and try again.')
  }

  let body: unknown
  try {
    body = await res.json()
  } catch {
    throw syntheticProblem(res.status, 'INVALID_RESPONSE', `Unexpected response from the server (HTTP ${res.status}).`)
  }

  if (!res.ok) {
    const p = body as Partial<ProblemDetails>
    throw new ApiProblem({
      type: p.type ?? 'about:blank',
      title: p.title ?? res.statusText,
      status: p.status ?? res.status,
      detail: p.detail ?? res.statusText,
      request_id: p.request_id ?? '',
      code: p.code ?? 'UNKNOWN_ERROR',
      errors: Array.isArray(p.errors) ? p.errors : [],
    })
  }
  return body as T
}
