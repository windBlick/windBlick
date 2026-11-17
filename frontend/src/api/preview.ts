import type { PreviewRequest, PreviewResponse } from '../types'
import { computePreview } from '../lib/projection'
import { USE_MOCKS, mockDelay, request } from './client'

/**
 * Turbine outlines projected into the photo.
 *
 * PROVISIONAL: while mocking, the projection runs in the browser
 * (src/lib/projection.ts). If the backend provides this calculation,
 * switch VITE_USE_MOCKS=false and align the endpoint/shape with the contract.
 */
export async function generatePreview(req: PreviewRequest): Promise<PreviewResponse> {
  if (USE_MOCKS) {
    await mockDelay(500)
    return computePreview(req)
  }
  return request<PreviewResponse>('/preview', { method: 'POST', body: JSON.stringify(req) })
}
