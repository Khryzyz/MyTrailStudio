# My Trail Studio

Engine and CLI layer for creating route videos with overlays from action-camera videos and GPX tracks.

The central rule is that the GPX leads the project: it defines date, start time, end time, base duration, distance, elevation, and the data used by overlays, timelines, and auxiliary views.

## Current Status

The project has two layers:

- Existing console engine: technical validation, preview generation, and final render.
- `ui_core`: CLI foundation for the future visual UI, with centralized projects, video validation, timeline, export settings, preview, final render, and logs.

The PySide6 visual UI is not implemented yet. The CLI layer is the functional backend first.

## Requirements

- Windows.
- Python 3.10 or newer available as `python`.
- FFmpeg and FFprobe available in `PATH`.
- Python dependencies used by the engine, including Pillow.
- `resources/font` folder present.
- `resources/assets` folder present with the application logo and isotype.
- MP4/MOV videos with a usable creation date. The system first uses video metadata `creation_time`; if missing, it uses the file creation date.

Quick checks:

```powershell
python --version
ffmpeg -version
ffprobe -version
```

## Structure

```text
<engine-root>
  input\
    pipeline_config.json
  output\
  resources\
    assets\
      logo.png
      iso.png
    font\
  scripts\
    validate_pipeline.py
    render_preview.py
    render_final.py
    ...
  ui_core\
    cli.py
    models\
    services\
  mts.ps1
  run_overlay.ps1
  run_mts_overlay_pipeline.ps1
  run_mts_integral_test.ps1
```

## Installation

1. Clone or copy the project.
2. Open PowerShell at the engine root:

```powershell
cd <engine-root>
```

3. Confirm Python and FFmpeg:

```powershell
python --version
ffmpeg -version
ffprobe -version
```

4. Verify the CLI:

```powershell
.\mts.ps1 --help
```

## Brand Assets

Application brand assets live in `resources/assets`:

- `logo.png`: full My Trail Studio logo for splash screens, headers, and documentation.
- `iso.png`: compact isotype for app icons, window chrome, and small UI placements.

## UI/CLI Projects

Projects are not stored inside `input` or next to the engine. They are centralized in:

```text
%APPDATA%\MyTrailStudio\projects\<project-id>
```

If you are coming from an older app data folder, projects are not deleted. You can copy them into `%APPDATA%\MyTrailStudio\projects` or use `--app-data` to point to the previous folder.

Each project references original GPX/videos without moving them. Temporary products and logs live in the centralized project folder or in the configured output folder.

## Basic Flow

Create a project:

```powershell
.\mts.ps1 create-project --name "My Route" --gpx "<route-folder>\track.gpx" --output "<route-folder>\output"
```

Add videos from a folder:

```powershell
.\mts.ps1 add-videos-dir --project "<project-id>" --dir "<route-folder>" --mode hyperlapse --hyperlapse-speed 2.0
```

If a video has an incorrect date, adjust it manually with `set-video-time`.

Validate the project:

```powershell
.\mts.ps1 validate-project --project "<project-id>"
```

Configure export:

```powershell
.\mts.ps1 set-export --project "<project-id>" --resolution 1080p --fps 30 --output-speed 3.5 --remove-audio --single-final-video --transitions --closing --closing-message "Route Completed" --closing-seconds 3
```

Or apply a preset:

```powershell
.\mts.ps1 list-export-presets
.\mts.ps1 apply-export-preset --project "<project-id>" --preset standard-1080p
```

Generate preview:

```powershell
.\mts.ps1 engine-preview --project "<project-id>" --seconds 10 --quiet
```

Final render:

```powershell
.\mts.ps1 engine-render-final --project "<project-id>" --confirm "RENDER_FINAL" --quiet
```

Summary:

```powershell
.\mts.ps1 project-summary --project "<project-id>"
```

## Integral Test

Without final render:

```powershell
.\run_mts_integral_test.ps1 -ProjectId "<project-id>"
```

With final render:

```powershell
.\run_mts_integral_test.ps1 -ProjectId "<project-id>" -RunFinalRender
```

## Outputs

Example:

```text
<route-folder>\output\previews
<route-folder>\output\final
<route-folder>\output\data\manifest.json
```

The final render also generates:

```text
render_report.json
render_report.txt
```

## Logs

Engine commands save logs in:

```text
%APPDATA%\MyTrailStudio\projects\<project-id>\logs
```

Use `--quiet` to reduce console noise and keep details in logs.

## Compatibility

The original launcher remains available:

```powershell
.\run_overlay.ps1
```

The new CLI uses temporary configuration and does not modify `input/pipeline_config.json` unless you edit it manually.

## Next Steps

1. Prepare the PySide6 visual UI on top of `ui_core`.
2. Create the visual project wizard: GPX, route name, output, and videos.
3. Create the visual video manager: import, GPX status, hyperlapse, manual date.
4. Create the export and render screen with confirmation.
5. Extract configurable layout without breaking the approved current layout.
