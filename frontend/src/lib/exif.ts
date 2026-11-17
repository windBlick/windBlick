import exifr from 'exifr'
import type { ExifHints } from '../types'

/**
 * Read a few EXIF values in the browser to *preview* what the photo contains
 * (badge text, placeholders, map centre). These hints are never sent as
 * overrides — the backend resolves EXIF itself (docs/api-contract.md §1).
 */
export async function readExifHints(file: File): Promise<ExifHints> {
  const empty: ExifHints = { position: null, heading: null, gpsAltitudeM: null, focalLength35mm: null }
  try {
    const data = await exifr.parse(file, {
      gps: true,
      // exifr derives latitude/longitude from the raw GPS tags, so those must be picked too
      pick: [
        'GPSLatitude',
        'GPSLatitudeRef',
        'GPSLongitude',
        'GPSLongitudeRef',
        'GPSImgDirection',
        'GPSImgDirectionRef',
        'GPSAltitude',
        'FocalLengthIn35mmFormat',
      ],
    })
    if (!data) return empty
    const num = (v: unknown) => (typeof v === 'number' && Number.isFinite(v) ? v : null)
    const lat = num(data.latitude)
    const lon = num(data.longitude)
    const dir = num(data.GPSImgDirection)
    return {
      position: lat !== null && lon !== null ? { lat, lon } : null,
      heading:
        dir !== null
          ? { value: dir, reference: data.GPSImgDirectionRef === 'T' ? 'true' : data.GPSImgDirectionRef === 'M' ? 'magnetic' : 'unknown' }
          : null,
      gpsAltitudeM: num(data.GPSAltitude),
      focalLength35mm: num(data.FocalLengthIn35mmFormat),
    }
  } catch (err) {
    console.warn('Could not read EXIF hints', err)
    return empty
  }
}

/** Natural pixel size of an image URL, as the browser displays it. */
export function loadImageSize(url: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight })
    img.onerror = () => reject(new Error('Could not load image'))
    img.src = url
  })
}
