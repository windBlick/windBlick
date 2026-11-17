import exifr from 'exifr'
import { ApiProblem } from '../client'
import type {
  ApiWarning,
  CameraUsed,
  CameraValueSource,
  TurbineResult,
  ValidationErrorEntry,
  VisualizationParameters,
  VisualizationResponse,
} from '../../types/contract'
import { API_VERSION, WFS_FEATURE_TYPES } from '../../types/contract'
import { MOCK_STYLE_COLOR, renderTurbines } from './mockRenderer'

/**
 * MOCK ONLY — emulates POST /api/v0/visualizations in the browser.
 *
 * Mirrors the contract's behaviour closely enough to exercise the UI:
 * validation errors, field-level merge of explicit overrides over EXIF,
 * CAMERA_PARAMETERS_UNRESOLVED with all missing paths, turbine outcomes,
 * warnings and camera_value_sources. EXIF support is deliberately narrow:
 * only GPS latitude/longitude and a true-north GPSImgDirection are used;
 * elevation (unknown datum), pitch, roll and intrinsics are never guessed.
 */

const problem = (status: number, title: string, code: string, detail: string, errors: ValidationErrorEntry[] = []) =>
  new ApiProblem({ type: 'about:blank', title, status, detail, request_id: `mock-${Date.now()}`, code, errors })

const unprocessable = (code: string, detail: string, errors: ValidationErrorEntry[] = []) =>
  problem(422, 'Unprocessable Content', code, detail, errors)

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)

interface ResolvedValue {
  value: number
  source: CameraValueSource
}

export async function mockCreateVisualization(
  image: File,
  params: VisualizationParameters,
): Promise<VisualizationResponse> {
  await new Promise((r) => setTimeout(r, 600))

  /* ---- transport / version / reserved features ---- */
  if (!['image/jpeg', 'image/png'].includes(image.type)) {
    throw problem(415, 'Unsupported Media Type', 'UNSUPPORTED_IMAGE_TYPE', 'Only JPEG and PNG images are supported.', [
      { part: 'image', code: 'UNSUPPORTED_IMAGE_TYPE', message: `Received ${image.type || 'unknown type'}.` },
    ])
  }
  if (params.api_version !== API_VERSION) {
    throw unprocessable('UNSUPPORTED_API_VERSION', `api_version must be "${API_VERSION}".`)
  }
  if (params.reference_points && params.reference_points.length > 0) {
    throw unprocessable('FEATURE_NOT_SUPPORTED', 'Reference points are not supported in v0.1.')
  }
  if (params.turbines.length > 100) {
    throw problem(413, 'Content Too Large', 'TURBINE_LIMIT_EXCEEDED', 'At most 100 turbines per request.')
  }

  /* ---- field validation ---- */
  const errors: ValidationErrorEntry[] = []
  if (params.turbines.length === 0) {
    errors.push({ path: '/turbines', code: 'MIN_ITEMS', message: 'Select at least one turbine.' })
  }
  params.turbines.forEach((t, i) => {
    if (!(t.hub_height_m > 0)) errors.push({ path: `/turbines/${i}/hub_height_m`, code: 'NOT_POSITIVE', message: 'Hub height must be positive.' })
    if (!(t.rotor_diameter_m > 0)) errors.push({ path: `/turbines/${i}/rotor_diameter_m`, code: 'NOT_POSITIVE', message: 'Rotor diameter must be positive.' })
    if (WFS_FEATURE_TYPES[t.status] !== t.source.feature_type) {
      errors.push({ path: `/turbines/${i}/status`, code: 'STATUS_LAYER_MISMATCH', message: 'Status does not match the source layer.' })
    }
  })
  const o = params.camera?.orientation ?? {}
  const pos = params.camera?.position ?? {}
  const intr = params.camera?.intrinsics ?? {}
  const range = (v: number | undefined, path: string, ok: (n: number) => boolean, msg: string) => {
    if (v !== undefined && (!isNum(v) || !ok(v))) errors.push({ path, code: 'OUT_OF_RANGE', message: msg })
  }
  range(pos.latitude_deg, '/camera/position/latitude_deg', (n) => n >= -90 && n <= 90, 'Latitude must be between −90 and 90.')
  range(pos.longitude_deg, '/camera/position/longitude_deg', (n) => n >= -180 && n <= 180, 'Longitude must be between −180 and 180.')
  range(o.heading_deg, '/camera/orientation/heading_deg', (n) => n >= 0 && n < 360, 'Heading must be ≥ 0 and < 360.')
  range(o.pitch_deg, '/camera/orientation/pitch_deg', (n) => n > -90 && n < 90, 'Pitch must be between −90 and 90 (exclusive).')
  range(o.roll_deg, '/camera/orientation/roll_deg', (n) => n >= -180 && n < 180, 'Roll must be ≥ −180 and < 180.')
  if ('horizontal_fov_deg' in intr) {
    range(intr.horizontal_fov_deg, '/camera/intrinsics/horizontal_fov_deg', (n) => n > 0 && n < 180, 'Field of view must be between 0 and 180 (exclusive).')
  }
  if (errors.length) throw unprocessable('VALIDATION_ERROR', 'Some parameters are invalid.', errors)

  /* ---- camera resolution: explicit override, then supported EXIF ---- */
  const exif = await exifr
    .parse(image, {
      gps: true,
      // exifr derives latitude/longitude from the raw GPS tags, so those must be picked too
      pick: ['GPSLatitude', 'GPSLatitudeRef', 'GPSLongitude', 'GPSLongitudeRef', 'GPSImgDirection', 'GPSImgDirectionRef'],
    })
    .catch(() => null)

  const override = (v: number | undefined, path: string): ResolvedValue | null =>
    isNum(v) ? { value: v, source: { source: 'override', input_paths: [path] } } : null
  const fromExif = (v: unknown, tags: string[]): ResolvedValue | null =>
    isNum(v) ? { value: v, source: { source: 'exif', exif_tags: tags } } : null

  const unresolved: ValidationErrorEntry[] = []
  const need = (r: ResolvedValue | null, path: string, message: string): ResolvedValue => {
    if (!r) unresolved.push({ path, code: 'EXIF_MISSING_OR_UNUSABLE', message })
    return r ?? { value: NaN, source: { source: 'derived' } }
  }

  const lon = need(
    override(pos.longitude_deg, '/camera/position/longitude_deg') ?? fromExif(exif?.longitude, ['GPSLongitude', 'GPSLongitudeRef']),
    '/camera/position/longitude_deg',
    'No location in the photo. Place the camera on the map or enter latitude/longitude.',
  )
  const lat = need(
    override(pos.latitude_deg, '/camera/position/latitude_deg') ?? fromExif(exif?.latitude, ['GPSLatitude', 'GPSLatitudeRef']),
    '/camera/position/latitude_deg',
    'No location in the photo. Place the camera on the map or enter latitude/longitude.',
  )
  const elevation = need(
    override(pos.elevation?.value_m, '/camera/position/elevation/value_m'),
    '/camera/position/elevation/value_m',
    'Camera elevation cannot be taken from the photo (unknown height reference). Enter it in metres above NHN.',
  )
  const trueNorthHeading = exif?.GPSImgDirectionRef === 'T' ? exif?.GPSImgDirection : undefined
  const heading = need(
    override(o.heading_deg, '/camera/orientation/heading_deg') ?? fromExif(trueNorthHeading, ['GPSImgDirection', 'GPSImgDirectionRef']),
    '/camera/orientation/heading_deg',
    'No true-north viewing direction in the photo. Enter the heading in degrees.',
  )
  const pitch = need(
    override(o.pitch_deg, '/camera/orientation/pitch_deg'),
    '/camera/orientation/pitch_deg',
    'Pitch cannot be read from the photo. Enter it (0 = level).',
  )
  const roll = need(
    override(o.roll_deg, '/camera/orientation/roll_deg'),
    '/camera/orientation/roll_deg',
    'Roll cannot be read from the photo. Enter it (0 = level).',
  )
  const fov = need(
    'horizontal_fov_deg' in intr ? override(intr.horizontal_fov_deg, '/camera/intrinsics/horizontal_fov_deg') : null,
    '/camera/intrinsics',
    'The field of view cannot be derived from the photo. Enter the horizontal field of view in degrees.',
  )

  if (unresolved.length) {
    throw unprocessable(
      'CAMERA_PARAMETERS_UNRESOLVED',
      'Camera parameters could not be resolved from overrides and EXIF.',
      unresolved,
    )
  }

  /* ---- decode with EXIF orientation applied once, then render ---- */
  const bitmap = await createImageBitmap(image, { imageOrientation: 'from-image' }).catch(() => null)
  if (!bitmap) throw unprocessable('INVALID_IMAGE', 'The image could not be decoded.', [{ part: 'image', code: 'INVALID_IMAGE', message: 'The image could not be decoded.' }])
  const W = bitmap.width
  const H = bitmap.height
  if ((params.image?.width_px && params.image.width_px !== W) || (params.image?.height_px && params.image.height_px !== H)) {
    throw unprocessable('IMAGE_DIMENSION_MISMATCH', 'Asserted image size does not match the normalized image.')
  }

  const fx = W / (2 * Math.tan((fov.value * Math.PI) / 360))
  const camera_used: CameraUsed = {
    position: {
      longitude_deg: lon.value,
      latitude_deg: lat.value,
      elevation: { value_m: elevation.value, datum: 'DHHN2016_NHN', source: 'user_input' },
    },
    orientation: { heading_deg: heading.value, pitch_deg: pitch.value, roll_deg: roll.value },
    intrinsics: { fx_px: fx, fy_px: fx, cx_px: (W - 1) / 2, cy_px: (H - 1) / 2 },
  }
  const intrinsicsSource: CameraValueSource = { source: 'derived', input_paths: ['/camera/intrinsics/horizontal_fov_deg'] }
  const camera_value_sources: Record<string, CameraValueSource> = {
    '/position/longitude_deg': lon.source,
    '/position/latitude_deg': lat.source,
    '/position/elevation/value_m': elevation.source,
    '/orientation/heading_deg': heading.source,
    '/orientation/pitch_deg': pitch.source,
    '/orientation/roll_deg': roll.source,
    '/intrinsics/fx_px': intrinsicsSource,
    '/intrinsics/fy_px': intrinsicsSource,
    '/intrinsics/cx_px': { source: 'derived' },
    '/intrinsics/cy_px': { source: 'derived' },
  }

  const canvas = document.createElement('canvas')
  canvas.width = W
  canvas.height = H
  const ctx = canvas.getContext('2d')!
  ctx.drawImage(bitmap, 0, 0)
  bitmap.close()

  const labels = params.turbines.map((t, i) => t.name ?? `Turbine ${i + 1}`)
  const rendered = renderTurbines(ctx, W, H, camera_used, params.turbines, labels)

  const turbines: TurbineResult[] = rendered.map((r, i) => ({
    id: r.id,
    label: r.label,
    status: params.turbines[i]!.status,
    source: params.turbines[i]!.source,
    outcome: r.outcome,
    style: { color_hex: MOCK_STYLE_COLOR, category: 'uniform' },
    ...(r.projectedHub ? { projected_hub_px: r.projectedHub } : {}),
  }))

  const warnings: ApiWarning[] = [
    { code: 'PINHOLE_APPROXIMATION', message: 'Pinhole camera model without lens-distortion correction.' },
    { code: 'SCHEMATIC_ROTOR_ORIENTATION', message: 'Rotor orientation and blade position are schematic.' },
    ...turbines
      .filter((t) => t.outcome !== 'drawn')
      .map((t) => ({
        code: t.outcome === 'outside_frame' ? 'TURBINE_OUTSIDE_FRAME' : 'TURBINE_BEHIND_CAMERA',
        message: `${t.label} is ${t.outcome === 'outside_frame' ? 'outside the image frame' : 'behind the camera'}.`,
        turbine_id: t.id,
      })),
  ]
  if (turbines.every((t) => t.outcome !== 'drawn')) {
    warnings.push({ code: 'NO_TURBINES_DRAWN', message: 'None of the selected turbines is visible in this photo.' })
  }

  const dataUrl = canvas.toDataURL('image/png')
  return {
    api_version: API_VERSION,
    request_id: `mock-${Date.now()}`,
    image: { mime_type: 'image/png', encoding: 'base64', data: dataUrl.slice(dataUrl.indexOf(',') + 1), width_px: W, height_px: H },
    camera_used,
    camera_value_sources,
    turbines,
    warnings,
    calibration: { applied: false },
  }
}
