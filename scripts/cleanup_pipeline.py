import argparse
import os
import shutil


INPUT_CLEAN_EXTENSIONS = {".mp4", ".mov", ".gpx"}


def normalize(path):
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def is_inside(root, path):
    root_abs = normalize(root)
    path_abs = normalize(path)
    try:
        return os.path.commonpath([root_abs, path_abs]) == root_abs
    except ValueError:
        return False


def require_safe_target(root, path):
    if not is_inside(root, path):
        raise Exception(f"Path outside project. Not cleaning: {path}")

    root_abs = normalize(root)
    path_abs = normalize(path)
    protected = {
        root_abs,
        normalize(os.path.join(root, ".git")),
        normalize(os.path.join(root, "scripts")),
        normalize(os.path.join(root, "resources")),
        normalize(os.path.join(root, "resources", "font")),
        normalize(os.path.join(root, "input", "pipeline_config.json")),
        normalize(os.path.join(root, "run_mts_overlay_pipeline.ps1")),
        normalize(os.path.join(root, ".gitignore")),
    }

    if path_abs in protected:
        raise Exception(f"Protected path. Not cleaning: {path}")


def remove_file(root, path):
    require_safe_target(root, path)
    if not os.path.exists(path):
        print("Does not exist:", path)
        return
    if os.path.isdir(path):
        raise Exception(f"Expected file, not folder: {path}")
    os.remove(path)
    print("Deleted file:", path)


def remove_dir(root, path):
    require_safe_target(root, path)
    if not os.path.exists(path):
        print("Does not exist:", path)
        return
    if not os.path.isdir(path):
        raise Exception(f"Expected folder, not file: {path}")
    shutil.rmtree(path)
    print("Deleted folder:", path)


def cleanup_auto_after_render(root):
    print("")
    print("Automatic cleanup after render...")
    remove_dir(root, os.path.join(root, "output", "frames"))
    remove_dir(root, os.path.join(root, "output", "data"))
    remove_dir(root, os.path.join(root, "temp"))
    print("Automatic cleanup OK.")


def cleanup_manual(root):
    print("")
    print("Manual project cleanup...")

    input_dir = os.path.join(root, "input")
    require_safe_target(root, input_dir)

    if os.path.isdir(input_dir):
        for name in os.listdir(input_dir):
            path = os.path.join(input_dir, name)
            if os.path.isfile(path) and os.path.splitext(name)[1].lower() in INPUT_CLEAN_EXTENSIONS:
                remove_file(root, path)
    else:
        print("Does not exist:", input_dir)

    remove_dir(root, os.path.join(root, "output", "frames"))
    remove_dir(root, os.path.join(root, "output", "previews"))
    remove_dir(root, os.path.join(root, "output", "final"))
    remove_dir(root, os.path.join(root, "output", "data"))
    remove_dir(root, os.path.join(root, "temp"))
    print("Manual cleanup OK.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", choices=["manual", "auto"], required=True)
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        raise Exception(f"Project root does not exist: {root}")

    if args.mode == "manual":
        cleanup_manual(root)
    else:
        cleanup_auto_after_render(root)


if __name__ == "__main__":
    main()




