from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ui_core.models.project_model import touch_project
from ui_core.services.engine_config_builder import build_engine_config
from ui_core.services.export_settings import update_export_settings
from ui_core.services.pipeline_adapter import run_engine_preview, run_engine_render_final, run_engine_validate
from ui_core.services.project_validator import validate_project
from ui_core.services.project_summary import build_project_summary
from ui_core.services.project_store import (
    create_project,
    delete_project,
    list_projects,
    load_project,
    project_file,
    save_project,
)
from ui_core.services.video_service import add_video, add_videos_from_dir, remove_video


def print_json(data: dict) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def print_validation_report(report: dict) -> None:
    print("Validacion del proyecto")
    print(f"Proyecto: {report['project_id']}")
    print(f"Videos: {report['videos']}")
    print(f"Timelines: {report['timelines']}")
    print(f"Huecos detectados: {len(report['gaps'])}")

    if report["warnings"]:
        print("")
        print("Advertencias:")
        for warning in report["warnings"]:
            print(f" - {warning}")

    if report["errors"]:
        print("")
        print("Errores:")
        for error in report["errors"]:
            print(f" - {error}")


def print_project_list(projects: list[dict]) -> None:
    if not projects:
        print("No hay proyectos creados.")
        return

    print("Proyectos")
    for project in projects:
        print("")
        print(f"ID: {project['id']}")
        print(f"Nombre: {project['name']}")
        print(f"GPX: {project['gpx_start_utc']} -> {project['gpx_end_utc']}")
        print(f"Videos: {project['videos']}")
        print(f"Actualizado: {project['updated_at_utc']}")


def print_project_summary(summary: dict) -> None:
    project = summary["project"]
    gpx = summary["gpx"]
    videos = summary["videos"]
    engine = summary["engine"]

    print("Resumen del proyecto")
    print(f"ID: {project['id']}")
    print(f"Nombre: {project['name']}")
    print(f"Actualizado: {project['updated_at_utc']}")
    print("")
    print("GPX")
    print(f"Inicio: {gpx.get('start_utc')}")
    print(f"Fin: {gpx.get('end_utc')}")
    print(f"Duracion: {summary['duration_text']['gpx']}")
    print(f"Distancia: {round(float(gpx.get('distance_m') or 0) / 1000, 3)} km")
    print(f"Altura: {gpx.get('min_altitude_m')} m -> {gpx.get('max_altitude_m')} m")
    print("")
    print("Videos")
    print(f"Cantidad: {videos['count']}")
    print(f"Duracion archivos: {summary['duration_text']['videos_file']}")
    print(f"Duracion real: {summary['duration_text']['videos_real']}")
    if videos["statuses"]:
        print("Estados: " + ", ".join(f"{key}={value}" for key, value in sorted(videos["statuses"].items())))
    print(f"Timelines: {summary['timelines']['count']}")
    print(f"Huecos: {len(summary['gaps'])}")
    print("")
    print("Exportacion")
    export = summary["export"]
    print(f"Salida: {export.get('output_dir')}")
    print(f"Resolucion: {export.get('resolution')}")
    print(f"FPS: {export.get('fps')}")
    print(f"Velocidad final: {export.get('output_hyperlapse_speed')}x")
    print(f"Eliminar audio: {export.get('remove_audio')}")
    print(f"Video unico: {export.get('single_final_video')}")
    print(f"Transiciones: {export.get('apply_transitions')}")
    closing = export.get("closing_screen", {})
    print(f"Cierre: {closing.get('enabled')} - {closing.get('seconds')}s - {closing.get('message')}")

    if videos["items"]:
        print("")
        print("Lista de videos")
        for index, video in enumerate(videos["items"], start=1):
            timeline = video["timeline_id"] if video["timeline_id"] is not None else "N/D"
            print(f"{index}. {video['name']} | {video['gpx_status']} | timeline {timeline}")

    if summary["warnings"]:
        print("")
        print("Advertencias:")
        for warning in summary["warnings"]:
            print(f" - {warning}")

    if summary["errors"]:
        print("")
        print("Errores:")
        for error in summary["errors"]:
            print(f" - {error}")

    print("")
    print("Motor")
    print(f"Config temporal: {engine['generated_config_path'] or 'N/D'}")
    print(f"Manifest: {engine['last_manifest_path'] or 'N/D'}")
    print(f"Manifest existe: {engine['manifest_exists']}")
    if engine["previews"]:
        print("Previews:")
        for preview in engine["previews"]:
            print(f" - {preview}")
    else:
        print("Previews: ninguno detectado")


def cmd_create_project(args: argparse.Namespace) -> int:
    project = create_project(
        name=args.name,
        gpx_path=Path(args.gpx),
        output_dir=Path(args.output),
        engine_root=Path(args.engine_root) if args.engine_root else None,
        app_data_dir=Path(args.app_data) if args.app_data else None,
        timezone_name=args.timezone,
    )
    path = project_file(Path(project["workspace"]["project_data_dir"]))
    print("Proyecto creado:")
    print(path)
    print("")
    print_json({
        "id": project["project"]["id"],
        "name": project["project"]["name"],
        "gpx": project["gpx_summary"],
    })
    return 0


def cmd_inspect_project(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    print_json(project)
    return 0


def cmd_list_projects(args: argparse.Namespace) -> int:
    projects = list_projects(Path(args.app_data) if args.app_data else None)
    print_project_list(projects)
    return 0


def cmd_project_summary(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    print_project_summary(build_project_summary(project))
    return 0


def cmd_add_video(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    video = add_video(
        project,
        Path(args.video),
        mode=args.mode,
        hyperlapse_speed=args.hyperlapse_speed,
    )
    print("Video agregado")
    print(f"Proyecto: {project['project']['id']} - {project['project']['name']}")
    print(f"GPX: {project['gpx_summary']['start_utc']} -> {project['gpx_summary']['end_utc']}")
    print(f"Video: {video['name']}")
    print(f"Inicio video: {video['creation_time_utc'] or 'SIN HORA'}")
    print(f"Duracion archivo: {video['duration_file_seconds']} s")
    print(f"Duracion real: {video['duration_real_seconds']} s")
    print(f"Estado GPX: {video['gpx_status']}")
    if video["gpx_status"] == "FUERA_DEL_GPX":
        print("")
        print("Advertencia: el video queda fuera del rango del GPX de este proyecto.")
    return 0


def cmd_add_videos_dir(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    result = add_videos_from_dir(
        project,
        Path(args.dir),
        mode=args.mode,
        hyperlapse_speed=args.hyperlapse_speed,
        recursive=args.recursive,
        include_out_of_gpx=args.include_out_of_gpx,
    )

    print("Importacion de carpeta")
    print(f"Proyecto: {project['project']['id']} - {project['project']['name']}")
    print(f"Carpeta: {result['folder']}")
    print(f"Videos encontrados: {result['candidates']}")
    print(f"Agregados: {len(result['added'])}")
    print(f"Omitidos: {len(result['skipped'])}")
    print(f"Fallidos: {len(result['failed'])}")
    if result["statuses"]:
        print("Estados: " + ", ".join(f"{key}={value}" for key, value in sorted(result["statuses"].items())))

    if result["added"]:
        print("")
        print("Videos agregados:")
        for video in result["added"]:
            print(f" - {video['name']} | {video['gpx_status']} | {video['creation_time_utc'] or 'SIN HORA'}")

    if result["failed"]:
        print("")
        print("Fallidos:")
        for item in result["failed"]:
            print(f" - {item['path']}: {item['error']}")

    if result["skipped"]:
        print("")
        print("Omitidos:")
        for item in result["skipped"]:
            print(f" - {item['path']}: {item['reason']}")

    return 1 if result["failed"] else 0


def cmd_build_engine_config(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    config_path = build_engine_config(project)
    print("Config temporal generada:")
    print(config_path)
    return 0


def cmd_set_export(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    updates = {
        "output_dir": args.output_dir,
        "resolution": args.resolution,
        "fps": args.fps,
        "output_hyperlapse_speed": args.output_speed,
        "remove_audio": args.remove_audio,
        "single_final_video": args.single_final_video,
        "apply_transitions": args.transitions,
        "closing_enabled": args.closing,
        "closing_message": args.closing_message,
        "closing_seconds": args.closing_seconds,
    }
    export = update_export_settings(project, updates)
    print("Configuracion de exportacion actualizada")
    print_json(export)
    return 0


def cmd_engine_validate(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    return run_engine_validate(project)


def cmd_engine_preview(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    return run_engine_preview(project, seconds=args.seconds)


def cmd_engine_render_final(args: argparse.Namespace) -> int:
    if args.confirm != "RENDER_FINAL":
        raise ValueError('Para render final debes pasar --confirm "RENDER_FINAL".')
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    return run_engine_render_final(project)


def cmd_validate_project(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    report = validate_project(project)
    print_validation_report(report)
    return 1 if report["errors"] else 0


def cmd_set_video_time(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    videos = project["assets"].get("videos", [])
    matched = None
    for video in videos:
        if video["id"] == args.video or video["name"].lower() == args.video.lower():
            matched = video
            break
    if not matched:
        raise SystemExit(f"No se encontro video por id o nombre: {args.video}")

    matched["manual_creation_time_utc"] = args.time
    touch_project(project)
    save_project(project)
    print("Fecha manual asignada:")
    print_json({
        "video_id": matched["id"],
        "name": matched["name"],
        "manual_creation_time_utc": matched["manual_creation_time_utc"],
    })
    return 0


def cmd_remove_video(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    removed = remove_video(project, args.video)
    print("Video eliminado del proyecto:")
    print(f"Proyecto: {project['project']['id']} - {project['project']['name']}")
    print(f"Video: {removed['name']}")
    return 0


def cmd_delete_project(args: argparse.Namespace) -> int:
    if args.confirm != args.project:
        raise ValueError("Para borrar el proyecto, --confirm debe ser exactamente igual a --project.")

    deleted = delete_project(args.project, Path(args.app_data) if args.app_data else None)
    print("Proyecto eliminado:")
    print(f"ID: {deleted['id']}")
    print(f"Nombre: {deleted['name']}")
    print(f"Carpeta eliminada: {deleted['deleted_dir']}")
    print("Nota: no se eliminaron GPX, videos ni audios originales referenciados por el proyecto.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ui_core.cli")
    parser.add_argument("--app-data", help="Carpeta central de datos de la app.")

    subparsers = parser.add_subparsers(required=True)

    create = subparsers.add_parser("create-project")
    create.add_argument("--name", required=True)
    create.add_argument("--gpx", required=True)
    create.add_argument("--output", required=True)
    create.add_argument("--engine-root", help="Carpeta del engine. Si se omite, usa la carpeta actual.")
    create.add_argument("--timezone", default="America/Bogota")
    create.set_defaults(func=cmd_create_project)

    inspect = subparsers.add_parser("inspect-project")
    inspect.add_argument("--project", required=True, help="ID, carpeta o archivo project.overlayproject.json.")
    inspect.set_defaults(func=cmd_inspect_project)

    list_cmd = subparsers.add_parser("list-projects")
    list_cmd.set_defaults(func=cmd_list_projects)

    summary = subparsers.add_parser("project-summary")
    summary.add_argument("--project", required=True)
    summary.set_defaults(func=cmd_project_summary)

    add = subparsers.add_parser("add-video")
    add.add_argument("--project", required=True)
    add.add_argument("--video", required=True)
    add.add_argument("--mode", choices=["normal", "hyperlapse"], default="normal")
    add.add_argument("--hyperlapse-speed", type=float, default=2.0)
    add.set_defaults(func=cmd_add_video)

    add_dir = subparsers.add_parser("add-videos-dir")
    add_dir.add_argument("--project", required=True)
    add_dir.add_argument("--dir", required=True)
    add_dir.add_argument("--mode", choices=["normal", "hyperlapse"], default="normal")
    add_dir.add_argument("--hyperlapse-speed", type=float, default=2.0)
    add_dir.add_argument("--recursive", action="store_true")
    add_dir.add_argument("--include-out-of-gpx", action="store_true")
    add_dir.set_defaults(func=cmd_add_videos_dir)

    build_config = subparsers.add_parser("build-engine-config")
    build_config.add_argument("--project", required=True)
    build_config.set_defaults(func=cmd_build_engine_config)

    set_export = subparsers.add_parser("set-export")
    set_export.add_argument("--project", required=True)
    set_export.add_argument("--output-dir")
    set_export.add_argument("--resolution", choices=["1080p", "2k", "4k"])
    set_export.add_argument("--fps", type=int, choices=[15, 30, 60])
    set_export.add_argument("--output-speed", type=float)
    set_export.add_argument("--remove-audio", action=argparse.BooleanOptionalAction)
    set_export.add_argument("--single-final-video", action=argparse.BooleanOptionalAction)
    set_export.add_argument("--transitions", action=argparse.BooleanOptionalAction)
    set_export.add_argument("--closing", action=argparse.BooleanOptionalAction)
    set_export.add_argument("--closing-message")
    set_export.add_argument("--closing-seconds", type=int)
    set_export.set_defaults(func=cmd_set_export)

    engine_validate = subparsers.add_parser("engine-validate")
    engine_validate.add_argument("--project", required=True)
    engine_validate.set_defaults(func=cmd_engine_validate)

    engine_preview = subparsers.add_parser("engine-preview")
    engine_preview.add_argument("--project", required=True)
    engine_preview.add_argument("--seconds", type=int, default=10)
    engine_preview.set_defaults(func=cmd_engine_preview)

    engine_render = subparsers.add_parser("engine-render-final")
    engine_render.add_argument("--project", required=True)
    engine_render.add_argument("--confirm", required=True, help='Debe ser exactamente "RENDER_FINAL".')
    engine_render.set_defaults(func=cmd_engine_render_final)

    validate = subparsers.add_parser("validate-project")
    validate.add_argument("--project", required=True)
    validate.set_defaults(func=cmd_validate_project)

    set_time = subparsers.add_parser("set-video-time")
    set_time.add_argument("--project", required=True)
    set_time.add_argument("--video", required=True, help="ID o nombre del video.")
    set_time.add_argument("--time", required=True, help="Fecha ISO UTC, por ejemplo 2026-07-09T12:00:00Z.")
    set_time.set_defaults(func=cmd_set_video_time)

    remove = subparsers.add_parser("remove-video")
    remove.add_argument("--project", required=True)
    remove.add_argument("--video", required=True, help="ID o nombre del video.")
    remove.set_defaults(func=cmd_remove_video)

    delete = subparsers.add_parser("delete-project")
    delete.add_argument("--project", required=True)
    delete.add_argument("--confirm", required=True, help="Debe ser exactamente igual al ID del proyecto.")
    delete.set_defaults(func=cmd_delete_project)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("Operacion cancelada.")
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
