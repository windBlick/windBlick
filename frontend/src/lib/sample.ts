import type { CameraOverrideForm, Turbine } from '../types'
import { wfsFixture } from '../api/mocks/wfsFixture'

/**
 * Demo scenario: a bundled illustration (no EXIF) with fixture camera values
 * and two fixture turbines. The illustration is converted to PNG because the
 * API accepts only JPEG/PNG uploads.
 */
export const SAMPLE_CAMERA: CameraOverrideForm = {
  latitude: 51.0603,
  longitude: 6.2187,
  elevationM: 91.6,
  headingDeg: 142,
  pitchDeg: 2,
  rollDeg: 0,
  horizontalFovDeg: 65,
}

export const SAMPLE_TURBINE_IDS = ['turbine-fixture-op-101', 'turbine-fixture-ap-104']

export function sampleTurbines(): Turbine[] {
  return wfsFixture.filter((t) => SAMPLE_TURBINE_IDS.includes(t.id))
}

export async function loadSamplePhoto(): Promise<File> {
  const img = new Image()
  img.src = '/sample/landscape.svg'
  await img.decode()
  const canvas = document.createElement('canvas')
  canvas.width = img.naturalWidth
  canvas.height = img.naturalHeight
  canvas.getContext('2d')!.drawImage(img, 0, 0)
  const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, 'image/png'))
  if (!blob) throw new Error('Could not create the sample photo')
  return new File([blob], 'sample-landscape.png', { type: 'image/png' })
}
