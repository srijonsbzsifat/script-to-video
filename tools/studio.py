"""Run commands inside the cinema-2D studio with the right environment (browser and libraries are kept inside the studio folder).

  python -I tools/studio.py where                          print the studio folder in use
  python -I tools/studio.py run node render.mjs --project projects/X --sheet --scale 0.5
  python -I tools/studio.py run python audio/mix.py --project projects/X

Studio folder: --dir, else env STUDIO_DIR, else <repo>/studio, else N:/AI/aitrends-2d-studio (the original install).
Set up a new one with tools/setup_studio.py.
"""
import os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent.parent


def studio_dir(arg=None):
    for c in (arg, os.environ.get("STUDIO_DIR"), HERE / "studio", "N:/AI/aitrends-2d-studio"):
        if c and (pathlib.Path(c) / "render.mjs").exists():
            return pathlib.Path(c).resolve()
    return pathlib.Path(arg or os.environ.get("STUDIO_DIR") or HERE / "studio").resolve()   # not installed yet


def studio_env(studio):
    studio = pathlib.Path(studio)
    env = dict(os.environ)
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(studio / ".cache" / "pw")
    env["npm_config_cache"] = str(studio / ".cache" / "npm")
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(studio / "pylibs"), env.get("PYTHONPATH")]))
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def main(argv):
    a, d = list(argv), None
    if a[:1] == ["--dir"]:
        d, a = a[1], a[2:]
    studio = studio_dir(d)
    if a[:1] == ["where"]:
        print(studio, "(installed)" if (studio / "render.mjs").exists() else "(NOT installed: run tools/setup_studio.py)")
        return 0
    if a[:1] == ["run"] and len(a) > 1:
        if not (studio / "render.mjs").exists():
            sys.exit(f"studio not installed at {studio}: run  python -I tools/setup_studio.py --go")
        cmd = [sys.executable if a[1] == "python" else a[1]] + a[2:]
        return subprocess.run(cmd, cwd=studio, env=studio_env(studio), shell=(os.name == "nt" and a[1] in ("npm", "npx"))).returncode
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
