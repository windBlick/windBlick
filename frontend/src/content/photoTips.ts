/**
 * User-facing text for the "Which photos are suitable?" card (issue #47).
 * Kept separate from the component so it can be edited or translated
 * without touching layout code.
 *
 * Field-of-view figures use the 35 mm-equivalent definition on the 43.27 mm
 * diagonal (same as CameraPanel): for a 4:3 photo the horizontal extent is
 * 34.6 mm in landscape and 26.0 mm in portrait.
 */

export interface TipItem {
  ok: boolean
  text: string
}

export interface SettingStep {
  title: string
  path: string
  why: string
}

export const suitablePhotos: { intro: string; items: TipItem[]; check: string } = {
  intro: 'The app needs to know where you stood and which way you looked. A good photo carries this information inside the file.',
  items: [
    { ok: true, text: 'JPG or PNG file, up to 20 MB' },
    { ok: true, text: 'The original file from your phone — it contains location and compass direction' },
    { ok: true, text: 'Taken outdoors, with a clear view towards where the turbines are or will be' },
    { ok: true, text: 'Landscape (horizontal) format, phone held level, normal 1× camera' },
    { ok: false, text: 'Photos sent as pictures via WhatsApp, Messenger or social media — they remove location data' },
    { ok: false, text: 'Screenshots, edited, cropped or filtered photos' },
    { ok: false, text: 'Panoramas, ultra-wide (0.5×) or zoomed photos — they distort the view' },
    { ok: false, text: 'iPhone HEIC files — not supported yet (see Phone settings to save as JPG)' },
  ],
  check:
    'To check a file on Windows: right-click it → Properties → Details. If you see “GPS Latitude” and “Longitude”, the location is included.',
}

export const transferTips: string[] = [
  'USB cable: copy the photo from the phone’s DCIM folder',
  'Google Photos or OneDrive camera upload: download the original',
  'WhatsApp: send it to yourself as a Document (paperclip → Document), not as a photo',
]

export const sensorNote =
  'Your phone saves its location and compass direction in each photo when the settings below are on. Tilt and roll (measured by the gyroscope) are not saved in photos by any camera app — so hold the phone level and confirm this in step 2.'

export const phoneSettings: Record<'ios' | 'android', SettingStep[]> = {
  ios: [
    {
      title: 'Allow the Camera to save your location',
      path: 'Settings → Privacy & Security → Location Services → Camera → “While Using the App” and “Precise Location” on',
      why: 'Saves where the photo was taken.',
    },
    {
      title: 'Turn on compass calibration',
      path: 'Settings → Privacy & Security → Location Services → System Services → “Compass Calibration” on',
      why: 'Makes the saved viewing direction more accurate.',
    },
    {
      title: 'Save photos as JPG',
      path: 'Settings → Camera → Formats → “Most Compatible”',
      why: 'iPhones save HEIC by default, which the app cannot read yet.',
    },
    {
      title: 'Show the level guide',
      path: 'Settings → Camera → “Grid” and “Level” on',
      why: 'Helps you hold the phone straight (tilt and roll ≈ 0°).',
    },
  ],
  android: [
    {
      title: 'Turn on location',
      path: 'Swipe down → Location on. Then Settings → Location → Location services → “Google Location Accuracy” on',
      why: 'Lets the phone determine where you are.',
    },
    {
      title: 'Allow the Camera to save your location',
      path: 'Camera app → Settings (⚙) → “Location tags” (Samsung) or “Save location” (Pixel) on',
      why: 'Saves where the photo was taken. The name differs by manufacturer.',
    },
    {
      title: 'Calibrate the compass',
      path: 'Open Google Maps → tap the blue dot → “Calibrate” and move the phone in a figure-8',
      why: 'Makes the saved viewing direction more accurate.',
    },
    {
      title: 'Show grid lines',
      path: 'Camera app → Settings (⚙) → “Grid lines” or “Framing hints” on',
      why: 'Helps you hold the phone straight (tilt and roll ≈ 0°).',
    },
  ],
}

export const motionSensorNote = {
  title: 'Taking photos directly in WindBlick (planned)',
  text: 'A later version may take photos in the browser and read the motion sensors (gyroscope) for tilt and roll. Your browser will then ask for permission — tap “Allow”. On Android you can change it later under Chrome → Site settings → Motion sensors.',
}

export interface RecommendedValue {
  name: string
  value: string
  note: string
}

export const recommendedValues: RecommendedValue[] = [
  {
    name: 'Camera elevation',
    value: 'Ground height + 1.6 m',
    note: 'In metres above sea level (NHN). Standing outside: about +1.6 m. From a first-floor window: about +4.5 m. Ground height can be read from a topographic map.',
  },
  {
    name: 'Heading',
    value: 'From the photo',
    note: 'Taken from the compass if saved. Otherwise read the direction from the map: 0° = north, 90° = east, 180° = south, 270° = west.',
  },
  { name: 'Pitch (tilt up/down)', value: '0°', note: 'Phone held level. Small errors matter: 1° at 2 km moves a turbine top by about 35 m.' },
  { name: 'Roll (sideways tilt)', value: '0°', note: 'Phone held straight, horizon level in the photo.' },
  { name: 'Field of view, 1× camera', value: '≈ 67° landscape · ≈ 53° portrait', note: 'Typical phone main camera (24–26 mm equivalent). The app shows a value calculated from your photo when available.' },
  { name: 'Field of view, 2× camera', value: '≈ 37° landscape', note: 'Telephoto lens (about 52 mm equivalent).' },
  { name: 'Field of view, 0.5× camera', value: 'Not recommended', note: 'Ultra-wide lenses (≈ 105°) are strongly distorted, so outlines will be inaccurate.' },
]

export const recommendedFootnote =
  'These are starting values. Compare the outlines with landmarks you know (a church tower, a mast) and adjust if they do not line up.'
