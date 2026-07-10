# CLI Workflow

Guia de comandos para la capa `ui_core`.

Ejecuta los comandos desde la raiz del engine:

```powershell
cd J:\Fotos\ActionCamera
```

## Ayuda

```powershell
python -m ui_core.cli --help
```

## Proyectos

Listar proyectos:

```powershell
python -m ui_core.cli list-projects
```

Crear proyecto:

```powershell
python -m ui_core.cli create-project --name "Mi Ruta" --gpx "E:\Ruta\track.gpx" --output "E:\Ruta\salida"
```

Inspeccionar JSON completo:

```powershell
python -m ui_core.cli inspect-project --project "<project-id>"
```

Resumen legible:

```powershell
python -m ui_core.cli project-summary --project "<project-id>"
```

Borrar proyecto centralizado:

```powershell
python -m ui_core.cli delete-project --project "<project-id>" --confirm "<project-id>"
```

Esto no borra GPX, videos ni audios originales.

## Videos

Los videos pueden venir de cualquier camara siempre que sean MP4/MOV y tengan una fecha de creacion util. La CLI usa primero `creation_time` de metadata y, si no existe, la fecha de creacion del archivo.

Agregar un video:

```powershell
python -m ui_core.cli add-video --project "<project-id>" --video "E:\Ruta\VIDEO_0001.MP4" --mode hyperlapse --hyperlapse-speed 2.0
```

Agregar carpeta completa:

```powershell
python -m ui_core.cli add-videos-dir --project "<project-id>" --dir "E:\Ruta" --mode hyperlapse --hyperlapse-speed 2.0
```

Por defecto, `add-videos-dir` omite:

- videos duplicados
- videos fuera del rango GPX

Para incluir videos fuera del GPX a proposito:

```powershell
python -m ui_core.cli add-videos-dir --project "<project-id>" --dir "E:\Ruta" --mode hyperlapse --hyperlapse-speed 2.0 --include-out-of-gpx
```

Quitar video del proyecto:

```powershell
python -m ui_core.cli remove-video --project "<project-id>" --video "VIDEO_0001.MP4"
```

Asignar fecha manual a un video sin metadata valida:

```powershell
python -m ui_core.cli set-video-time --project "<project-id>" --video "VIDEO_0001.MP4" --time "2026-06-13T13:18:14Z"
```

## Validacion

Validacion de proyecto:

```powershell
python -m ui_core.cli validate-project --project "<project-id>"
```

Validacion tecnica del motor:

```powershell
python -m ui_core.cli engine-validate --project "<project-id>" --quiet
```

## Exportacion

Configurar salida:

```powershell
python -m ui_core.cli set-export --project "<project-id>" --resolution 1080p --fps 30 --output-speed 3.5 --remove-audio --single-final-video --transitions --closing --closing-message "Ruta Finalizada" --closing-seconds 3
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

## Preview

```powershell
python -m ui_core.cli engine-preview --project "<project-id>" --seconds 10 --quiet
```

Salida esperada:

```text
<output-dir>\previews
```

## Render Final

```powershell
python -m ui_core.cli engine-render-final --project "<project-id>" --confirm "RENDER_FINAL" --quiet
```

Salida esperada:

```text
<output-dir>\final
```

## Apertura Rapida

Abrir carpeta de salida:

```powershell
python -m ui_core.cli open-output --project "<project-id>"
```

Abrir subcarpetas:

```powershell
python -m ui_core.cli open-output --project "<project-id>" --subdir previews
python -m ui_core.cli open-output --project "<project-id>" --subdir final
python -m ui_core.cli open-output --project "<project-id>" --subdir data
```

Abrir carpeta interna del proyecto:

```powershell
python -m ui_core.cli open-project-data --project "<project-id>"
```

## Prueba Integral

Sin render final:

```powershell
.\run_project_integral_test.ps1 -ProjectId "<project-id>"
```

Con render final:

```powershell
.\run_project_integral_test.ps1 -ProjectId "<project-id>" -RunFinalRender
```

Parametros opcionales:

```powershell
-Resolution 1080p
-Fps 30
-OutputSpeed 3.5
-PreviewSeconds 10
-ClosingMessage "Ruta Finalizada"
-ClosingSeconds 3
```



