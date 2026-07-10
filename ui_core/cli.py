from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ui_core.models.project_model import touch_project
from ui_core.services.engine_config_builder import build_engine_config
from ui_core.services.export_presets import apply_export_preset, list_export_presets
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
    print("Project validation")
    print(f"Project: {report['project_id']}")
    print(f"Videos: {report['videos']}")
    print(f"Timelines: {report['timelines']}")
    print(f"Detected gaps: {len(report['gaps'])}")
    coverage = report.get("coverage", {})
    if coverage:
        print(f"GPX coverage: {coverage.get('percent')}% ({coverage.get('overlap_seconds')} s)")
    if report.get("long_gaps"):
        print(f"Long gaps: {len(report['long_gaps'])}")

    if report["warnings"]:
        print("")
        print("Warnings:")
        for warning in report["warnings"]:
            print(f" - {warning}")

    if report["errors"]:
        print("")
        print("Errors:")
        for error in report["errors"]:
            print(f" - {error}")


def print_project_list(projects: list[dict]) -> None:
    if not projects:
        print("No projects found.")
        return

    print("Projects")
    for project in projects:
        print("")
        print(f"ID: {project['id']}")
        print(f"Name: {project['name']}")
        print(f"GPX: {project['gpx_start_utc']} -> {project['gpx_end_utc']}")
        print(f"Videos: {project['videos']}")
        print(f"Updated: {project['updated_at_utc']}")


def print_project_summary(summary: dict) -> None:
    project = summary["project"]
    gpx = summary["gpx"]
    videos = summary["videos"]
    engine = summary["engine"]

    print("Project summary")
    print(f"ID: {project['id']}")
    print(f"Name: {project['name']}")
    print(f"Updated: {project['updated_at_utc']}")
    print("")
    print("GPX")
    print(f"Start: {gpx.get('start_utc')}")
    print(f"End: {gpx.get('end_utc')}")
    print(f"Duration: {summary['duration_text']['gpx']}")
    print(f"Distance: {round(float(gpx.get('distance_m') or 0) / 1000, 3)} km")
    print(f"Elevation: {gpx.get('min_altitude_m')} m -> {gpx.get('max_altitude_m')} m")
    print("")
    print("Videos")
    print(f"Count: {videos['count']}")
    print(f"File duration: {summary['duration_text']['videos_file']}")
    print(f"Real duration: {summary['duration_text']['videos_real']}")
    if videos["statuses"]:
        print("Statuses: " + ", ".join(f"{key}={value}" for key, value in sorted(videos["statuses"].items())))
    print(f"Timelines: {summary['timelines']['count']}")
    print(f"Gaps: {len(summary['gaps'])}")
    if summary.get("coverage"):
        print(f"GPX coverage: {summary['coverage'].get('percent')}%")
    print("")
    print("Export")
    export = summary["export"]
    print(f"Output: {export.get('output_dir')}")
    print(f"Resolution: {export.get('resolution')}")
    print(f"FPS: {export.get('fps')}")
    print(f"Final speed: {export.get('output_hyperlapse_speed')}x")
    print(f"Preset: {export.get('preset_id') or 'custom'}")
    print(f"Remove audio: {export.get('remove_audio')}")
    print(f"Single final video: {export.get('single_final_video')}")
    print(f"Transitions: {export.get('apply_transitions')}")
    closing = export.get("closing_screen", {})
    print(f"Closing: {closing.get('enabled')} - {closing.get('seconds')}s - {closing.get('message')}")

    if videos["items"]:
        print("")
        print("Video list")
        for index, video in enumerate(videos["items"], start=1):
            timeline = video["timeline_id"] if video["timeline_id"] is not None else "N/D"
            print(f"{index}. {video['name']} | {video['gpx_status']} | timeline {timeline}")

    if summary["warnings"]:
        print("")
        print("Warnings:")
        for warning in summary["warnings"]:
            print(f" - {warning}")

    if summary["errors"]:
        print("")
        print("Errors:")
        for error in summary["errors"]:
            print(f" - {error}")

    print("")
    print("Engine")
    print(f"Temporary config: {engine['generated_config_path'] or 'N/D'}")
    print(f"Manifest: {engine['last_manifest_path'] or 'N/D'}")
    print(f"Manifest exists: {engine['manifest_exists']}")
    if engine["previews"]:
        print("Previews:")
        for preview in engine["previews"]:
            print(f" - {preview}")
    else:
        print("Previews: none detected")
    if engine["finals"]:
        print("Finals:")
        for final in engine["finals"]:
            print(f" - {final}")
    else:
        print("Finals: none detected")
    if engine["render_reports"]:
        print("Reports:")
        for report in engine["render_reports"]:
            print(f" - {report}")
    if engine["logs"]:
        print("Logs:")
        for log in engine["logs"][-5:]:
            print(f" - {log}")


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
    print("Project created:")
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
    print("Video added")
    print(f"Project: {project['project']['id']} - {project['project']['name']}")
    print(f"GPX: {project['gpx_summary']['start_utc']} -> {project['gpx_summary']['end_utc']}")
    print(f"Video: {video['name']}")
    print(f"Video start: {video['creation_time_utc'] or 'NO TIME'}")
    print(f"File duration: {video['duration_file_seconds']} s")
    print(f"Real duration: {video['duration_real_seconds']} s")
    print(f"GPX status: {video['gpx_status']}")
    if video["gpx_status"] == "FUERA_DEL_GPX":
        print("")
        print("Warning: the video is outside this project GPX range.")
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

    print("Folder import")
    print(f"Project: {project['project']['id']} - {project['project']['name']}")
    print(f"Folder: {result['folder']}")
    print(f"Videos found: {result['candidates']}")
    print(f"Added: {len(result['added'])}")
    print(f"Skipped: {len(result['skipped'])}")
    print(f"Failed: {len(result['failed'])}")
    if result["statuses"]:
        print("Statuses: " + ", ".join(f"{key}={value}" for key, value in sorted(result["statuses"].items())))

    if result["added"]:
        print("")
        print("Added videos:")
        for video in result["added"]:
            print(f" - {video['name']} | {video['gpx_status']} | {video['creation_time_utc'] or 'NO TIME'}")

    if result["failed"]:
        print("")
        print("Failed:")
        for item in result["failed"]:
            print(f" - {item['path']}: {item['error']}")

    if result["skipped"]:
        print("")
        print("Skipped:")
        for item in result["skipped"]:
            print(f" - {item['path']}: {item['reason']}")

    return 1 if result["failed"] else 0


def cmd_build_engine_config(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    config_path = build_engine_config(project)
    print("Temporary config generated:")
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
    print("Export settings updated")
    print_json(export)
    return 0


def cmd_list_export_presets(args: argparse.Namespace) -> int:
    print("Export presets")
    for preset in list_export_presets():
        settings = preset["settings"]
        print("")
        print(f"ID: {preset['id']}")
        print(f"Name: {preset['name']}")
        print(f"Description: {preset['description']}")
        print(
            "Settings: "
            f"{settings['resolution']}, {settings['fps']} fps, "
            f"{settings['output_hyperlapse_speed']}x, "
            f"remove_audio={settings['remove_audio']}, "
            f"transitions={settings['apply_transitions']}, "
            f"closing={settings['closing_enabled']}"
        )
    return 0


def cmd_apply_export_preset(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    result = apply_export_preset(project, args.preset)
    print("Export preset applied")
    print(f"Project: {project['project']['id']} - {project['project']['name']}")
    print(f"Preset: {result['preset_id']} - {result['preset_name']}")
    print_json(result["export"])
    return 0


def cmd_engine_validate(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    return run_engine_validate(project, quiet=args.quiet)


def cmd_engine_preview(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    return run_engine_preview(project, seconds=args.seconds, quiet=args.quiet)


def cmd_engine_render_final(args: argparse.Namespace) -> int:
    if args.confirm != "RENDER_FINAL":
        raise ValueError('For final render you must pass --confirm "RENDER_FINAL".')
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    return run_engine_render_final(project, quiet=args.quiet)


def open_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Path to open does not exist: {path}")
    subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", "Start-Process", "-LiteralPath", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def cmd_open_output(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    output_dir = Path(project["export"]["output_dir"])
    target = output_dir / args.subdir if args.subdir else output_dir
    open_path(target)
    print(f"Opening: {target}")
    return 0


def cmd_open_project_data(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    target = Path(project["workspace"]["project_data_dir"])
    open_path(target)
    print(f"Opening: {target}")
    return 0


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
        raise SystemExit(f"Video not found by ID or name: {args.video}")

    matched["manual_creation_time_utc"] = args.time
    touch_project(project)
    save_project(project)
    print("Manual date assigned:")
    print_json({
        "video_id": matched["id"],
        "name": matched["name"],
        "manual_creation_time_utc": matched["manual_creation_time_utc"],
    })
    return 0


def cmd_remove_video(args: argparse.Namespace) -> int:
    project = load_project(args.project, Path(args.app_data) if args.app_data else None)
    removed = remove_video(project, args.video)
    print("Video removed from project:")
    print(f"Project: {project['project']['id']} - {project['project']['name']}")
    print(f"Video: {removed['name']}")
    return 0


def cmd_delete_project(args: argparse.Namespace) -> int:
    if args.confirm != args.project:
        raise ValueError("To delete the project, --confirm must exactly match --project.")

    deleted = delete_project(args.project, Path(args.app_data) if args.app_data else None)
    print("Project deleted:")
    print(f"ID: {deleted['id']}")
    print(f"Name: {deleted['name']}")
    print(f"Deleted folder: {deleted['deleted_dir']}")
    print("Note: original GPX, videos, and audio files referenced by the project were not deleted.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=".\\mts.ps1")
    parser.add_argument("--app-data", help="Central app data folder.")

    subparsers = parser.add_subparsers(required=True)

    create = subparsers.add_parser("create-project")
    create.add_argument("--name", required=True)
    create.add_argument("--gpx", required=True)
    create.add_argument("--output", required=True)
    create.add_argument("--engine-root", help="Engine folder. If omitted, uses the current folder.")
    create.add_argument("--timezone", default="America/Bogota")
    create.set_defaults(func=cmd_create_project)

    inspect = subparsers.add_parser("inspect-project")
    inspect.add_argument("--project", required=True, help="ID, folder, or project.overlayproject.json file.")
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

    list_presets = subparsers.add_parser("list-export-presets")
    list_presets.set_defaults(func=cmd_list_export_presets)

    apply_preset = subparsers.add_parser("apply-export-preset")
    apply_preset.add_argument("--project", required=True)
    apply_preset.add_argument(
        "--preset",
        required=True,
        choices=[preset["id"] for preset in list_export_presets()],
    )
    apply_preset.set_defaults(func=cmd_apply_export_preset)

    engine_validate = subparsers.add_parser("engine-validate")
    engine_validate.add_argument("--project", required=True)
    engine_validate.add_argument("--quiet", action="store_true")
    engine_validate.set_defaults(func=cmd_engine_validate)

    engine_preview = subparsers.add_parser("engine-preview")
    engine_preview.add_argument("--project", required=True)
    engine_preview.add_argument("--seconds", type=int, default=10)
    engine_preview.add_argument("--quiet", action="store_true")
    engine_preview.set_defaults(func=cmd_engine_preview)

    engine_render = subparsers.add_parser("engine-render-final")
    engine_render.add_argument("--project", required=True)
    engine_render.add_argument("--confirm", required=True, help='Must be exactly "RENDER_FINAL".')
    engine_render.add_argument("--quiet", action="store_true")
    engine_render.set_defaults(func=cmd_engine_render_final)

    open_output = subparsers.add_parser("open-output")
    open_output.add_argument("--project", required=True)
    open_output.add_argument("--subdir", choices=["previews", "final", "data", "frames"])
    open_output.set_defaults(func=cmd_open_output)

    open_project_data = subparsers.add_parser("open-project-data")
    open_project_data.add_argument("--project", required=True)
    open_project_data.set_defaults(func=cmd_open_project_data)

    validate = subparsers.add_parser("validate-project")
    validate.add_argument("--project", required=True)
    validate.set_defaults(func=cmd_validate_project)

    set_time = subparsers.add_parser("set-video-time")
    set_time.add_argument("--project", required=True)
    set_time.add_argument("--video", required=True, help="Video ID or name.")
    set_time.add_argument("--time", required=True, help="UTC ISO date, for example 2026-07-09T12:00:00Z.")
    set_time.set_defaults(func=cmd_set_video_time)

    remove = subparsers.add_parser("remove-video")
    remove.add_argument("--project", required=True)
    remove.add_argument("--video", required=True, help="Video ID or name.")
    remove.set_defaults(func=cmd_remove_video)

    delete = subparsers.add_parser("delete-project")
    delete.add_argument("--project", required=True)
    delete.add_argument("--confirm", required=True, help="Must exactly match the project ID.")
    delete.set_defaults(func=cmd_delete_project)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("Operation canceled.")
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


