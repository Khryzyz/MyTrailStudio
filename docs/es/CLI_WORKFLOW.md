# CLI Workflow

Guia de comandos para la capa `ui_core`.

Ejecuta los comandos desde la raiz del engine:

```powershell
cd <raiz-engine>
```

## Ayuda

```powershell
.\mts.ps1 --help
```

## Proyectos

Por defecto, los proyectos viven en `%APPDATA%\MyTrailStudio\projects`. Si necesitas usar una carpeta de proyectos anterior o portable, agrega `--app-data "RUTA"` antes del subcomando.

Listar proyectos:

```powershell
.\mts.ps1 list-projects
```

Crear proyecto:

```powershell
.\mts.ps1 create-project --name "Mi Ruta" --gpx "<carpeta-ruta>\track.gpx" --output "<carpeta-ruta>\output"
```

Inspeccionar JSON completo:

```powershell
.\mts.ps1 inspect-project --project "<project-id>"
```

Resumen legible:

```powershell
.\mts.ps1 project-summary --project "<project-id>"
```

Borrar proyecto centralizado:

```powershell
.\mts.ps1 delete-project --project "<project-id>" --confirm "<project-id>"
```

Esto no borra GPX, videos ni audios originales.

## Videos

Los videos pueden venir de cualquier camara siempre que sean MP4/MOV y tengan una fecha de creacion util. La CLI usa primero `creation_time` de metadata y, si no existe, la fecha de creacion del archivo.

Agregar un video:

```powershell
.\mts.ps1 add-video --project "<project-id>" --video "<carpeta-ruta>\VIDEO_0001.MP4" --mode hyperlapse --hyperlapse-speed 2.0
```

Agregar carpeta completa:

```powershell
.\mts.ps1 add-videos-dir --project "<project-id>" --dir "<carpeta-ruta>" --mode hyperlapse --hyperlapse-speed 2.0
```

Por defecto, `add-videos-dir` omite:

- videos duplicados
- videos fuera del rango GPX

Para incluir videos fuera del GPX a proposito:

```powershell
.\mts.ps1 add-videos-dir --project "<project-id>" --dir "<carpeta-ruta>" --mode hyperlapse --hyperlapse-speed 2.0 --include-out-of-gpx
```

Quitar video del proyecto:

```powershell
.\mts.ps1 remove-video --project "<project-id>" --video "VIDEO_0001.MP4"
```

Asignar fecha manual a un video sin metadata valida:

```powershell
.\mts.ps1 set-video-time --project "<project-id>" --video "VIDEO_0001.MP4" --time "2026-06-13T13:18:14Z"
```

## Validacion

Validacion de proyecto:

```powershell
.\mts.ps1 validate-project --project "<project-id>"
```

Validacion tecnica del motor:

```powershell
.\mts.ps1 engine-validate --project "<project-id>" --quiet
```

## Exportacion

Listar presets de exportacion:

```powershell
.\mts.ps1 list-export-presets
```

Aplicar un preset:

```powershell
.\mts.ps1 apply-export-preset --project "<project-id>" --preset standard-1080p
```

Configurar `output`:

```powershell
.\mts.ps1 set-export --project "<project-id>" --resolution 1080p --fps 30 --output-speed 3.5 --remove-audio --single-final-video --transitions --closing --closing-message "Route Completed" --closing-seconds 3
```

Opciones utiles:

```powershell
--resolution 1080p|2k|4k
--fps 15|30|60
--output-speed 0.1..50.0
--remove-audio / --no-remove-audio
--single-final-video / --no-single-final-video
--transitions / --no-transitions
--closing / --no-closing
```

Presets disponibles:

```text
preview-fast
standard-1080p
final-4k
social-vertical-source
```

## Preview

```powershell
.\mts.ps1 engine-preview --project "<project-id>" --seconds 10 --quiet
```

Salida esperada:

```text
<output-dir>\previews
```

## Render Final

```powershell
.\mts.ps1 engine-render-final --project "<project-id>" --confirm "RENDER_FINAL" --quiet
```

Salida esperada:

```text
<output-dir>\final
```

## Apertura Rapida

Abrir carpeta `output`:

```powershell
.\mts.ps1 open-output --project "<project-id>"
```

Abrir subcarpetas:

```powershell
.\mts.ps1 open-output --project "<project-id>" --subdir previews
.\mts.ps1 open-output --project "<project-id>" --subdir final
.\mts.ps1 open-output --project "<project-id>" --subdir data
```

Abrir carpeta interna del proyecto:

```powershell
.\mts.ps1 open-project-data --project "<project-id>"
```

## Prueba Integral

Sin render final:

```powershell
.\run_mts_integral_test.ps1 -ProjectId "<project-id>"
```

Con render final:

```powershell
.\run_mts_integral_test.ps1 -ProjectId "<project-id>" -RunFinalRender
```

Parametros opcionales:

```powershell
-Resolution 1080p
-Fps 30
-OutputSpeed 3.5
-ExportPreset standard-1080p
-PreviewSeconds 10
-ClosingMessage "Route Completed"
-ClosingSeconds 3
```








