import { VISUALIZATIONS_PATH, type VisualizationParameters, type VisualizationResponse } from '../types/contract'
import { USE_MOCKS, postForm } from './client'

/**
 * POST /api/v0/visualizations (docs/api-contract.md §2, §7).
 *
 * Sends the original photo unchanged (EXIF preserved) plus the parameters
 * JSON as two multipart parts. Throws ApiProblem on error responses.
 */
export async function createVisualization(
  image: File,
  parameters: VisualizationParameters,
): Promise<VisualizationResponse> {
  if (USE_MOCKS) {
    // Loaded lazily so the mock backend is not part of production bundles.
    const { mockCreateVisualization } = await import('./mocks/mockBackend')
    return mockCreateVisualization(image, parameters)
  }

  const form = new FormData()
  form.append('image', image, image.name)
  form.append(
    'parameters',
    new Blob([JSON.stringify(parameters)], { type: 'application/json' }),
    'parameters.json',
  )
  return postForm<VisualizationResponse>(VISUALIZATIONS_PATH, form)
}

/** Data URL for displaying the rendered PNG from a response. */
export function resultImageUrl(res: VisualizationResponse): string {
  return `data:${res.image.mime_type};base64,${res.image.data}`
}
