import exifr from 'exifr'
import type { PhotoMetadata } from '../types'

/**
 * Read GPS position, compass direction and field of view from a JPG.
 * Runs entirely in the browser — the photo is not uploaded for this step.
 */
export async function readPhotoMetadata(file: File): Promise<PhotoMetadata> {
  try {
    const data = await exifr.parse(file, {
      gps: true,
      pick: [
        'latitude',
        'longitude',
        'GPSLatitude',
        'GPSLongitude',
        'GPSLatitudeRef',
        'GPSLongitudeRef',
        'GPSImgDirection',
        'FocalLengthIn35mmFormat',
      ],
    })
    if (!data) return { gps: null, azimuth: null, fov: null }

    const gps =
      typeof data.latitude === 'number' && typeof data.longitude === 'number'
        ? { lat: data.latitude, lon: data.longitude }
        : null

    const azimuth = typeof data.GPSImgDirection === 'number' ? data.GPSImgDirection % 360 : null

    // Horizontal FOV from 35 mm-equivalent focal length (36 mm wide sensor)
    const f35 = data.FocalLengthIn35mmFormat
    const fov = typeof f35 === 'number' && f35 > 0 ? (2 * Math.atan(36 / (2 * f35)) * 180) / Math.PI : null

    return { gps, azimuth, fov }
  } catch {
    return { gps: null, azimuth: null, fov: null }
  }
}

/** Natural pixel size of an image URL. */
export function loadImageSize(url: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight })
    img.onerror = () => reject(new Error('Could not load image'))
    img.src = url
  })
}
