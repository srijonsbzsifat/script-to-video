"""One-time setup: install the pinned HyperFrames, make sure its Chrome exists, check the rest.

  python -I setup.py
"""
import os, pathlib, shutil, subprocess, sys

HERE = pathlib.Path(__file__).parent
CACHE = HERE / ".cache"
env = dict(os.environ, npm_config_cache=str(CACHE / "npm"), npm_config_update_notifier="false")
ok = True


def need(cond, msg):
    global ok
    print(("ok   " if cond else "MISSING ") + msg)
    ok &= bool(cond)


def sh(cmd):
    return subprocess.run(cmd, cwd=HERE, env=env).returncode == 0


need(sys.version_info >= (3, 11), f"Python 3.11+ (have {sys.version.split()[0]})")
node = shutil.which("node")
nv = subprocess.run([node, "-v"], capture_output=True, text=True).stdout.strip() if node else ""
need(node and int(nv.lstrip("v").split(".")[0]) >= 22, f"Node 22+ (have {nv or 'none'})")
need(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg + ffprobe on PATH")
models = os.environ.get("WHISPER_MODELS") or os.path.expandvars(r"%LOCALAPPDATA%\app.concat.editor\whisper-models")
need((pathlib.Path(models) / "ggml-small.en.bin").exists(), f"whisper model ggml-small.en.bin in {models} (set WHISPER_MODELS)")
if not ok:
    sys.exit("fix the MISSING items above, then re-run setup.py")

npm = shutil.which("npm")
need(sh([npm, "ci", "--no-audit", "--no-fund"]) if (HERE / "package-lock.json").exists() else sh([npm, "install", "--no-audit", "--no-fund"]), "npm dependencies (pinned hyperframes)")
hf = str(HERE / "node_modules" / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes"))
need(sh([hf, "browser", "ensure"]), "HyperFrames headless Chrome (cached once, ~270 MB, outside this repo)")
sh([hf, "doctor"])
print("\nready. try:  python -I build.py episodes/test-pops" if ok else "\nsetup incomplete")
