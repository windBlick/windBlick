import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { CameraPose, PhotoInfo, PlannedTurbine, PreviewResponse, LatLon } from '../types'
import { loadImageSize, readPhotoMetadata } from '../lib/exif'
import { destination } from '../lib/geo'
import { generatePreview } from '../api/preview'

export const DEFAULT_HUB_HEIGHT = 160
export const DEFAULT_ROTOR_DIAMETER = 130
export const CAMERA_HEIGHT = 1.6
const DEFAULT_CAMERA: CameraPose = { lat: 51.0603, lon: 6.2187, azimuth: 142, pitch: 2, fov: 65 }

/** Everything the user does across the three steps. */
export const useSessionStore = defineStore('session', () => {
  const photo = ref<PhotoInfo | null>(null)
  const camera = ref<CameraPose>({ ...DEFAULT_CAMERA })
  const gpsDetected = ref(false)
  const compassDetected = ref(false)
  const turbines = ref<PlannedTurbine[]>([])
  const preview = ref<PreviewResponse | null>(null)
  const previewLoading = ref(false)
  const previewError = ref<string | null>(null)
  let nextId = 1

  const hasPhoto = computed(() => photo.value !== null)
  const canGenerate = computed(() => hasPhoto.value && turbines.value.length > 0)

  function setPhotoUrl(url: string) {
    if (photo.value?.file && photo.value.url !== url) URL.revokeObjectURL(photo.value.url)
    return url
  }

  async function loadPhoto(file: File) {
    const url = setPhotoUrl(URL.createObjectURL(file))
    const [size, meta] = await Promise.all([loadImageSize(url), readPhotoMetadata(file)])
    photo.value = { file, url, name: file.name, ...size }
    gpsDetected.value = meta.gps !== null
    compassDetected.value = meta.azimuth !== null
    camera.value = {
      ...DEFAULT_CAMERA,
      ...(meta.gps ?? {}),
      azimuth: meta.azimuth ?? DEFAULT_CAMERA.azimuth,
      fov: meta.fov ? Math.round(meta.fov) : DEFAULT_CAMERA.fov,
      pitch: 0,
    }
    turbines.value = []
    preview.value = null
  }

  /** Bundled sample photo + camera + two turbines, for demos without a real JPG. */
  async function loadSample() {
    const url = setPhotoUrl('/sample/landscape.svg')
    const size = await loadImageSize(url)
    photo.value = { file: null, url, name: 'sample-landscape.jpg', ...size }
    gpsDetected.value = true
    compassDetected.value = true
    camera.value = { ...DEFAULT_CAMERA }
    turbines.value = []
    nextId = 1
    addTurbine(destination(DEFAULT_CAMERA, 128, 950))
    addTurbine(destination(DEFAULT_CAMERA, 151, 1350))
    preview.value = null
  }

  function addTurbine(pos: LatLon) {
    const n = nextId++
    turbines.value.push({
      id: `wt-${n}`,
      label: `WT ${String(n).padStart(2, '0')}`,
      lat: pos.lat,
      lon: pos.lon,
      hubHeight: DEFAULT_HUB_HEIGHT,
      rotorDiameter: DEFAULT_ROTOR_DIAMETER,
    })
    preview.value = null
  }

  function updateTurbine(id: string, patch: Partial<Omit<PlannedTurbine, 'id'>>) {
    const t = turbines.value.find((x) => x.id === id)
    if (t) Object.assign(t, patch)
    preview.value = null
  }

  function removeTurbine(id: string) {
    turbines.value = turbines.value.filter((t) => t.id !== id)
    preview.value = null
  }

  function updateCamera(patch: Partial<CameraPose>) {
    camera.value = { ...camera.value, ...patch }
    preview.value = null
  }

  async function runPreview() {
    if (!photo.value) return
    previewLoading.value = true
    previewError.value = null
    try {
      preview.value = await generatePreview({
        image: { width: photo.value.width, height: photo.value.height },
        camera: camera.value,
        cameraHeight: CAMERA_HEIGHT,
        turbines: turbines.value,
      })
    } catch (e) {
      previewError.value = e instanceof Error ? e.message : 'Preview could not be generated.'
    } finally {
      previewLoading.value = false
    }
  }

  function reset() {
    if (photo.value?.file) URL.revokeObjectURL(photo.value.url)
    photo.value = null
    turbines.value = []
    preview.value = null
    nextId = 1
  }

  return {
    photo,
    camera,
    gpsDetected,
    compassDetected,
    turbines,
    preview,
    previewLoading,
    previewError,
    hasPhoto,
    canGenerate,
    loadPhoto,
    loadSample,
    addTurbine,
    updateTurbine,
    removeTurbine,
    updateCamera,
    runPreview,
    reset,
  }
})
