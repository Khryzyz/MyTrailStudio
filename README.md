# My Trail Studio

<p align="center">
  <img src="resources/assets/logo.png" alt="My Trail Studio logo" width="420">
</p>

My Trail Studio is a route video overlay tool built around action-camera footage, GPX tracks, previews, and final renders.

## Documentation

- [English](docs/en/README.md)
- [Español](docs/es/README.md)

## CLI

Use the MTS wrapper from the project root:

```powershell
.\mts.ps1 --help
```

## UI Preview

The first PySide6 shell is available as an optional desktop UI:

```powershell
python -m pip install -r requirements-ui.txt
.\mts_ui.ps1
```

For double-click launch on Windows, use:

```powershell
.\MyTrailStudio.cmd
```

To build a standalone `.exe`:

```powershell
.\build_mts_ui_exe.ps1
```
