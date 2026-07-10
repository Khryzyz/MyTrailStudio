# CLI Workflow

Command guide for the `ui_core` layer.

Run commands from the engine root:

```powershell
cd J:\Fotos\MyTrailStudio
```

## Help

```powershell
.\mts.ps1 --help
```

## Projects

By default, projects live in `%APPDATA%\MyTrailStudio\projects`. If you need to use an older or portable project folder, add `--app-data "PATH"` before the subcommand.

List projects:

```powershell
.\mts.ps1 list-projects
```

Create project:

```powershell
.\mts.ps1 create-project --name "My Route" --gpx "E:\Route\track.gpx" --output "E:\Route\output"
```

Inspect full JSON:

```powershell
.\mts.ps1 inspect-project --project "<project-id>"
```

Readable summary:

```powershell
.\mts.ps1 project-summary --project "<project-id>"
```

Delete centralized project:

```powershell
.\mts.ps1 delete-project --project "<project-id>" --confirm "<project-id>"
```

This does not delete original GPX, videos, or audio files.

## Videos

Videos can come from any camera as long as they are MP4/MOV and have a usable creation date. The CLI first uses metadata `creation_time`; if missing, it uses the file creation date.

Add one video:

```powershell
.\mts.ps1 add-video --project "<project-id>" --video "E:\Route\VIDEO_0001.MP4" --mode hyperlapse --hyperlapse-speed 2.0
```

Add a full folder:

```powershell
.\mts.ps1 add-videos-dir --project "<project-id>" --dir "E:\Route" --mode hyperlapse --hyperlapse-speed 2.0
```

By default, `add-videos-dir` skips:

- duplicate videos
- videos outside the GPX range

To intentionally include videos outside the GPX range:

```powershell
.\mts.ps1 add-videos-dir --project "<project-id>" --dir "E:\Route" --mode hyperlapse --hyperlapse-speed 2.0 --include-out-of-gpx
```

Remove video from the project:

```powershell
.\mts.ps1 remove-video --project "<project-id>" --video "VIDEO_0001.MP4"
```

Assign manual time to a video with invalid metadata:

```powershell
.\mts.ps1 set-video-time --project "<project-id>" --video "VIDEO_0001.MP4" --time "2026-06-13T13:18:14Z"
```

## Validation

Project validation:

```powershell
.\mts.ps1 validate-project --project "<project-id>"
```

Engine technical validation:

```powershell
.\mts.ps1 engine-validate --project "<project-id>" --quiet
```

## Export

Configure output:

```powershell
.\mts.ps1 set-export --project "<project-id>" --resolution 1080p --fps 30 --output-speed 3.5 --remove-audio --single-final-video --transitions --closing --closing-message "Route Completed" --closing-seconds 3
```

Useful options:

```powershell
--resolution 1080p|2k|4k
--fps 15|30|60
--output-speed 0.1..50.0
--remove-audio / --no-remove-audio
--single-final-video / --no-single-final-video
--transitions / --no-transitions
--closing / --no-closing
```

## Preview

```powershell
.\mts.ps1 engine-preview --project "<project-id>" --seconds 10 --quiet
```

Expected output:

```text
<output-dir>\previews
```

## Final Render

```powershell
.\mts.ps1 engine-render-final --project "<project-id>" --confirm "RENDER_FINAL" --quiet
```

Expected output:

```text
<output-dir>\final
```

## Quick Open

Open output folder:

```powershell
.\mts.ps1 open-output --project "<project-id>"
```

Open subfolders:

```powershell
.\mts.ps1 open-output --project "<project-id>" --subdir previews
.\mts.ps1 open-output --project "<project-id>" --subdir final
.\mts.ps1 open-output --project "<project-id>" --subdir data
```

Open internal project data:

```powershell
.\mts.ps1 open-project-data --project "<project-id>"
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

Optional parameters:

```powershell
-Resolution 1080p
-Fps 30
-OutputSpeed 3.5
-PreviewSeconds 10
-ClosingMessage "Route Completed"
-ClosingSeconds 3
```

