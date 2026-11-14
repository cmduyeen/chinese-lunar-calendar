"""Publish only a complete, checksum-verified artifact from the trusted build job."""

import argparse
import json
import shutil
import tempfile
from pathlib import Path

if __package__:
    from .files import obsolete_exports, publish_staged, safe_filename
    from .output_lock import output_lock
    from .release_state import fingerprint, is_current
else:
    from files import obsolete_exports, publish_staged, safe_filename
    from output_lock import output_lock
    from release_state import fingerprint, is_current


def publish_release(staging, output, *, custom_configs=()):
    staging, output = Path(staging), Path(output)
    expected = fingerprint(custom_configs=custom_configs)
    if not is_current(staging, expected):
        raise ValueError("Refusing an incomplete, stale or modified release artifact")
    state = json.loads((staging / ".build-state.json").read_text(encoding="utf-8"))
    names = [*state["files"], ".build-state.json"]
    if not all(safe_filename(name) for name in names):
        raise ValueError("Invalid artifact filename")
    # Copy only checksum-recorded files, never unrecorded artifact extras.
    with tempfile.TemporaryDirectory(prefix="lunar-verified-") as temp:
        verified = Path(temp)
        for name in names:
            shutil.copyfile(staging / name, verified / name)
        if not is_current(verified, expected):
            raise ValueError("Artifact changed during verification")
        inventory = json.loads((verified / "index.json").read_text(encoding="utf-8"))
        with output_lock(output):
            obsolete = obsolete_exports(output, verified, inventory)
            return publish_staged(verified, output, obsolete)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("output"), type=Path)
    parser.add_argument("--custom-config", action="append", default=[], type=Path)
    args = parser.parse_args(argv)
    try:
        changed = publish_release(args.staging, args.output_dir, custom_configs=args.custom_config)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"{len(changed)} verified files updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
