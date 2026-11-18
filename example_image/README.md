# Example images

This folder contains four photo examples: **castle**, **drone**, **example**, and **Marsberg**. Use them to compare windBlick results with the windPRO drawings and renderings.

## Files

- **Original photos:** `castle_example_image.JPG`, `drone_picture.jpg`, `example_image.JPG`, and `Marsberg_example.JPG`.
- **Settings screenshots:** `castle.png`, `drone.png`, `example.png`, and `Marsberg.png`.
- **Drawings:** files ending in `_drawing.png`; for the drone, `drone_picture_example.png`. They mark turbine towers and rotor circles.
- **Renderings:** `*_Turbine_facing_Camera.png` and `*_Turbine_facing_Mainwinddirection.png` show different rotor directions.
- **Camera data:** [windpro_camera_settings.csv](windpro_camera_settings.csv), one row per example.

## Why the Marsberg example matters

`Marsberg_Demonstration_Image.jpeg` is a poster promoting a local protest. According to Robin, the manually Photoshopped montage helped trigger the protest and shows inaccurate turbine proportions and locations. Robin then created the windPRO comparison from the same viewpoint to show a more geometrically grounded alternative. `Marsberg_example.JPG` is the original photo for that comparison, not the poster's source photograph.

Robin describes the poster's source photo as strongly zoomed. Such a narrow, enlarged view can make distant turbines appear more prominent than in an unaided overview of the landscape. **Zoom alone does not change foreground/background size ratios from a fixed viewpoint**; perspective depends on camera position, and the displayed impression also depends on image size and viewing distance. See [PPA's explanation of perspective](https://wiki.ppa.com/books/photography-certification-guide/page/module-1e-lens-selection).

The poster's original focal length is unverified. The supplied comparison photo records **35 mm (52 mm equivalent)** in EXIF. The comparison illustrates why scale, placement and framing matter; it is not a claim that either image exactly reproduces human vision.

## Reading the CSV

- `windpro_*`: values read from the settings screenshots.
- `photo_*`: metadata read from the photos **before** GPS was added.
- `notes`: missing information and differences between the sources.
- Blank cells mean **unknown**, not zero. Units are included in column names: `_m`, `_deg`, `_mm`, `_px`.

All windPRO map coordinates use **ETRS89 / UTM zone 32N (EPSG:25832)**, in metres.

When automatic terrain height is enabled, camera height is **terrain height + Z offset**. For the drone, Z is already the absolute camera height. The CSV records the result in `camera_elevation_derived_m`.

For Excel import, select **UTF-8**, **comma separator**, and **decimal point**.

## Added GPS metadata

GPS coordinates were added to the castle and example originals, converted from windPRO coordinates to WGS84. They are manually derived positions, not camera GPS measurements. Unmodified backups are in [exif_backups](exif_backups/).

The drone's existing GPS data was kept. Image content was preserved. The CSV still describes the metadata before these additions.

## Still to clarify

Before using the data directly in the API, confirm the height reference, the meaning/sign of windPRO angles, and the calibrated focal length and film format. These are not fully established by the screenshots. Normalizing an azimuth to 0-360 degrees does not establish true north.

No height or angle EXIF fields were added. Keep windPRO values and original camera measurements separate, especially for the drone where they differ.

Reference: [windPRO VISUAL manual](https://help.emd.dk/knowledgebase/content/windPRO4.1/c7-UK_windPRO4.1-VISUAL.pdf), pages 13-15 and 29-30.
