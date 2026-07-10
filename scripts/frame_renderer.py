import os
from concurrent.futures import ProcessPoolExecutor

from gpx_track import sample_at
from overlay_renderer import build_overlay_context, render_closing_frame, render_overlay_frame


_WORKER = {}


def resolve_worker_count(value):
    workers = int(value or 0)
    if workers == 0:
        cpu_count = os.cpu_count() or 2
        return max(1, min(cpu_count - 1, 8))
    return max(1, workers)


def _init_worker(W, H, config, gpx_points, font_path, route_name=None, stats=None):
    _WORKER.clear()
    _WORKER.update({
        "W": W,
        "H": H,
        "config": config,
        "gpx_points": gpx_points,
        "font_path": font_path,
        "route_name": route_name,
        "stats": stats,
        "context": build_overlay_context(W, H, gpx_points, font_path),
    })


def _render_frame_task(task):
    frame, kind, current_time, out_path = task
    W = _WORKER["W"]
    H = _WORKER["H"]
    config = _WORKER["config"]
    gpx_points = _WORKER["gpx_points"]
    font_path = _WORKER["font_path"]

    if kind == "closing":
        img = render_closing_frame(W, H, config, _WORKER["route_name"], _WORKER["stats"], font_path)
    else:
        current = sample_at(gpx_points, current_time)
        img = render_overlay_frame(W, H, config, gpx_points, current_time, current, frame, _WORKER["context"])

    img.save(out_path)
    return frame


def frame_exists(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def render_frames_parallel(W, H, config, gpx_points, font_path, tasks, progress_label, route_name=None, stats=None, resume=False):
    if resume:
        pending_tasks = [task for task in tasks if not frame_exists(task[3])]
        skipped = len(tasks) - len(pending_tasks)
        if skipped:
            print("Existing frames reused:", skipped)
        tasks = pending_tasks

    workers = resolve_worker_count(config["setting"]["performance"].get("frame_workers", 0))
    total_frames = len(tasks)

    if total_frames == 0:
        print(f"{progress_label}: todos los frames ya existen.")
        return

    if workers == 1 or total_frames <= 1:
        _init_worker(W, H, config, gpx_points, font_path, route_name, stats)
        for index, task in enumerate(tasks, start=1):
            _render_frame_task(task)
            if index == 1 or index == total_frames or index % max(1, int(config["setting"]["layout"]["overlay_fps"])) == 0:
                pct = (index / total_frames) * 100
                print(f"\r{progress_label}: {index}/{total_frames} ({pct:.1f}%)", end="")
        print("")
        return

    print("Workers frames:", workers)

    chunksize = max(1, total_frames // (workers * 8))
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_worker,
        initargs=(W, H, config, gpx_points, font_path, route_name, stats)
    ) as executor:
        for completed, _ in enumerate(executor.map(_render_frame_task, tasks, chunksize=chunksize), start=1):
            if completed == 1 or completed == total_frames or completed % max(1, int(config["setting"]["layout"]["overlay_fps"])) == 0:
                pct = (completed / total_frames) * 100
                print(f"\r{progress_label}: {completed}/{total_frames} ({pct:.1f}%)", end="")

    print("")


