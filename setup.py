"""Setup check: finds what you already have, reports what is missing, installs only the pinned npm packages.

  python -I setup.py

It NEVER installs or downloads ffmpeg, Node or whisper models. If something is missing it prints the command to
get it. Existing installs are reused as they are (ffmpeg on PATH, a whisper model in any known folder).
"""
import importlib.util, json, os, pathlib, platform, shutil, subprocess, sys

HERE = pathlib.Path(__file__).parent
CACHE = HERE / ".cache"
env = dict(os.environ, npm_config_cache=str(CACHE / "npm"), npm_config_update_notifier="false")
OS = {"Darwin": "mac", "Windows": "win"}.get(platform.system(), "linux")
HINT = {
    "node": {"mac": "brew install node", "win": "winget install OpenJS.NodeJS.LTS", "linux": "install Node 22+ (https://nodejs.org)"},
    "ffmpeg": {"mac": "brew install ffmpeg", "win": "winget install Gyan.FFmpeg", "linux": "install ffmpeg 8+ from your package manager or https://ffmpeg.org"},
}
ok = True


def need(cond, msg, hint=""):
    global ok
    print(("ok       " if cond else "MISSING  ") + msg)
    if not cond and hint:
        print("         -> " + hint)
    ok &= bool(cond)


def sh(cmd):
    return subprocess.run(cmd, cwd=HERE, env=env).returncode == 0


def out(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout


need(sys.version_info >= (3, 11), f"Python 3.11+ (have {sys.version.split()[0]})", "install Python 3.11+")
node = shutil.which("node")
nv = out([node, "-v"]).strip() if node else ""
need(node and int(nv.lstrip("v").split(".")[0]) >= 22, f"Node 22+ (have {nv or 'none'})", HINT["node"][OS])

ff, fp = shutil.which("ffmpeg"), shutil.which("ffprobe")
ver = (out([ff, "-version"]).splitlines() or [""])[0] if ff else ""
need(ff and fp, f"ffmpeg + ffprobe already installed: {ver or 'not found'}", HINT["ffmpeg"][OS])
flt = out([ff, "-hide_banner", "-filters"]) if ff else ""
need(" whisper " in flt, "that ffmpeg includes the `whisper` filter (this is the only whisper component needed; no separate whisper install)",
     "your ffmpeg is too old or built without it: get ffmpeg 8+ with whisper support (" + HINT["ffmpeg"][OS] + ")")

# reuse a whisper model from any known folder (same search the builder uses)
spec = importlib.util.spec_from_file_location("whisper_words", HERE / "tools" / "whisper_words.py")
ww = importlib.util.module_from_spec(spec); spec.loader.exec_module(ww)
models = ww.find_models_dir()
have_model = (pathlib.Path(models) / "ggml-small.en.bin").is_file()
need(have_model, f"whisper model ggml-small.en.bin already present in {models}" if have_model else "whisper model ggml-small.en.bin (looked in WHISPER_MODELS, ~/whisper-models, ~/.cache/whisper*, ~/whisper.cpp/models, FilmCraft's folder)",
     f'mkdir -p "{models}" && curl -L -o "{models}/ggml-small.en.bin" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin   (or set WHISPER_MODELS to the folder you already have)')
if not ok:
    sys.exit("\nfix the MISSING items above (only those), then re-run setup.py")

# pinned npm packages: skip when the exact versions are already installed
want = json.load(open(HERE / "package.json"))["devDependencies"]
def installed(pkg):
    f = HERE / "node_modules" / pkg / "package.json"
    return json.load(open(f))["version"] if f.exists() else None
if all(installed(k) == v for k, v in want.items()):
    need(True, "npm packages already installed at the pinned versions: " + ", ".join(f"{k}@{v}" for k, v in want.items()))
else:
    npm = shutil.which("npm")
    need(sh([npm, "ci", "--no-audit", "--no-fund"]) if (HERE / "package-lock.json").exists() else sh([npm, "install", "--no-audit", "--no-fund"]), "npm packages installed (pinned hyperframes + gsap)")
hf = str(HERE / "node_modules" / ".bin" / ("hyperframes.cmd" if os.name == "nt" else "hyperframes"))
need(sh([hf, "browser", "ensure"]), "HyperFrames headless Chrome (reused if already cached, else downloaded once, ~270 MB, outside this repo)")
sh([hf, "doctor"])
print("\nready. try:  python -I build.py episodes/test-pops" if ok else "\nsetup incomplete")
