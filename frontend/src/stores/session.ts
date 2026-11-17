import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type {
  CameraField,
  CameraOverrideForm,
  ExifHints,
  FieldProvenance,
  PhotoInfo,
  Turbine,
  VisualizationParameters,
  VisualizationResponse,
} from '../types'
import { API_VERSION } from '../types/contract'
import { loadImageSize, readExifHints } from '../lib/exif'
import { createVisualization } from '../api/visualizations'
import { ApiProblem } from '../api/client'
import { SAMPLE_CAMERA, loadSamplePhoto, sampleTurbines } from '../lib/sample'

const EMPTY_OVERRIDES: CameraOverrideForm = {
  latitude: null,
  longitude: null,
  elevationM: null,
  headingDeg: null,
  pitchDeg: null,
  rollDeg: null,
  horizontalFovDeg: null,
}

/** JSON Pointer in the request parameters for each form field (contract §4). */
export const CAMERA_FIELD_PATHS: Record<CameraField, string> = {
  latitude: '/camera/position/latitude_deg',
  longitude: '/camera/position/longitude_deg',
  elevationM: '/camera/position/elevation/value_m',
  headingDeg: '/camera/orientation/heading_deg',
  pitchDeg: '/camera/orientation/pitch_deg',
  rollDeg: '/camera/orientation/roll_deg',
  horizontalFovDeg: '/camera/intrinsics/horizontal_fov_deg',
}

/** Build the contract's `parameters` part: only explicitly set camera values are sent. */
export function buildParameters(
  overrides: CameraOverrideForm,
  turbines: Turbine[],
  overrideSource: FieldProvenance['source'],
): VisualizationParameters {
  const o = overrides
  const params: VisualizationParameters = { api_version: API_VERSION, turbines, reference_points: [] }
  const camera: NonNullable<VisualizationParameters['camera']> = {}
  const provenance: Record<string, FieldProvenance> = {}

  if (o.latitude !== null || o.longitude !== null || o.elevationM !== null) {
    camera.position = {}
    if (o.longitude !== null) camera.position.longitude_deg = o.longitude
    if (o.latitude !== null) camera.position.latitude_deg = o.latitude
    if (o.elevationM !== null) {
      camera.position.elevation = {
        value_m: o.elevationM,
        datum: 'DHHN2016_NHN',
        source: overrideSource === 'fixture' ? 'fixture' : 'user_input',
      }
    }
  }
  if (o.headingDeg !== null || o.pitchDeg !== null || o.rollDeg !== null) {
    camera.orientation = { north_reference: 'true' }
    if (o.headingDeg !== null) camera.orientation.heading_deg = o.headingDeg
    if (o.pitchDeg !== null) camera.orientation.pitch_deg = o.pitchDeg
    if (o.rollDeg !== null) camera.orientation.roll_deg = o.rollDeg
  }
  if (o.horizontalFovDeg !== null) {
    camera.intrinsics = { kind: 'horizontal_fov', horizontal_fov_deg: o.horizontalFovDeg }
  }
  for (const [field, path] of Object.entries(CAMERA_FIELD_PATHS) as [CameraField, string][]) {
    if (o[field] !== null) provenance[path] = { source: overrideSource }
  }

  if (Object.keys(camera).length) params.camera = camera
  if (Object.keys(provenance).length) params.provenance = provenance
  return params
}

/** Everything the user does across the three steps. */
export const useSessionStore = defineStore('session', () => {
  const photo = ref<PhotoInfo | null>(null)
  const exif = ref<ExifHints | null>(null)
  const overrides = ref<CameraOverrideForm>({ ...EMPTY_OVERRIDES })
  /** Whether the current override values come from the demo fixture or the user. */
  const overrideSource = ref<'user_input' | 'fixture'>('user_input')
  const turbines = ref<Turbine[]>([])

  const result = ref<VisualizationResponse | null>(null)
  const loading = ref(false)
  const problem = ref<ApiProblem | null>(null)

  const hasPhoto = computed(() => photo.value !== null)
  const canGenerate = computed(() => hasPhoto.value && turbines.value.length > 0)

  /** Messages from the last error response, keyed by JSON Pointer. */
  const fieldErrors = computed<Record<string, string>>(() => {
    const out: Record<string, string> = {}
    for (const e of problem.value?.problem.errors ?? []) if (e.path) out[e.path] ??= e.message
    return out
  })

  /** Effective values for drawing the map (override, else EXIF hint). Not sent to the API. */
  const mapCamera = computed(() => {
    const o = overrides.value
    const hintPos = exif.value?.position
    const hintHeading = exif.value?.heading?.reference === 'true' ? exif.value.heading.value : null
    return {
      lat: o.latitude ?? hintPos?.lat ?? null,
      lon: o.longitude ?? hintPos?.lon ?? null,
      headingDeg: o.headingDeg ?? hintHeading,
      fovDeg: o.horizontalFovDeg,
    }
  })

  function invalidate() {
    result.value = null
    problem.value = null
  }

  async function setPhoto(file: File, hints: ExifHints) {
    if (photo.value) URL.revokeObjectURL(photo.value.url)
    const url = URL.createObjectURL(file)
    const size = await loadImageSize(url)
    photo.value = { file, url, name: file.name, ...size }
    exif.value = hints
  }

  async function loadPhoto(file: File) {
    await setPhoto(file, await readExifHints(file))
    overrides.value = { ...EMPTY_OVERRIDES }
    overrideSource.value = 'user_input'
    turbines.value = []
    invalidate()
  }

  /** Demo: bundled photo + fixture camera values + two fixture turbines. */
  async function loadSample() {
    await setPhoto(await loadSamplePhoto(), { position: null, heading: null, gpsAltitudeM: null, focalLength35mm: null })
    overrides.value = { ...SAMPLE_CAMERA }
    overrideSource.value = 'fixture'
    turbines.value = sampleTurbines()
    invalidate()
  }

  function setOverride(field: CameraField, value: number | null) {
    overrides.value = { ...overrides.value, [field]: value }
    overrideSource.value = 'user_input'
    invalidate()
  }

  function toggleTurbine(t: Turbine) {
    const i = turbines.value.findIndex((x) => x.id === t.id)
    if (i >= 0) turbines.value.splice(i, 1)
    else if (turbines.value.length < 100) turbines.value.push(t)
    invalidate()
  }

  function removeTurbine(id: string) {
    turbines.value = turbines.value.filter((t) => t.id !== id)
    invalidate()
  }

  async function generate(): Promise<boolean> {
    if (!photo.value || !turbines.value.length) return false
    loading.value = true
    problem.value = null
    try {
      const params = buildParameters(overrides.value, turbines.value, overrideSource.value)
      result.value = await createVisualization(photo.value.file, params)
      return true
    } catch (e) {
      problem.value =
        e instanceof ApiProblem
          ? e
          : new ApiProblem({
              type: 'about:blank',
              title: 'Error',
              status: 0,
              detail: e instanceof Error ? e.message : 'The preview could not be generated.',
              request_id: '',
              code: 'CLIENT_ERROR',
              errors: [],
            })
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    photo,
    exif,
    overrides,
    turbines,
    result,
    loading,
    problem,
    hasPhoto,
    canGenerate,
    fieldErrors,
    mapCamera,
    loadPhoto,
    loadSample,
    setOverride,
    toggleTurbine,
    removeTurbine,
    generate,
  }
})
