from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
MAX_DURATION = 60 * 60
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
DEPS = ROOT / ".deps"
QUALITY_HEIGHTS = {"baixa": 360, "media": 480, "boa": 720}


def yt_dlp_options():
    node = shutil.which("node")
    bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
    if not node and bundled.exists():
        node = str(bundled)
    if not node:
        raise ValueError("Node.js não encontrado. Instale Node.js para processar vídeos do YouTube.")
    return ["--js-runtimes", f"node:{node}", "--remote-components", "ejs:github"]


def ffmpeg_exe():
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    binaries = DEPS / "imageio_ffmpeg" / "binaries"
    matches = list(binaries.glob("ffmpeg*.exe"))
    if not matches:
        raise ValueError("FFmpeg não encontrado. Execute iniciar.cmd para instalar as dependências.")
    return str(matches[0])


def yt_dlp_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(DEPS) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def normalized_url(raw):
    parsed = urlparse(raw.strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or host not in (
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"
    ):
        raise ValueError("Cole um link válido do YouTube.")
    if host == "youtu.be":
        video_id = parsed.path.strip("/")
    elif parsed.path == "/watch":
        from urllib.parse import parse_qs
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    elif parsed.path.startswith("/shorts/") or parsed.path.startswith("/live/"):
        video_id = parsed.path.split("/")[2]
    else:
        raise ValueError("Use o link de um vídeo individual.")
    if not VIDEO_ID.fullmatch(video_id):
        raise ValueError("O identificador do vídeo é inválido.")
    return f"https://www.youtube.com/watch?v={video_id}"


def inspect_video(url):
    result = subprocess.run(
        [sys.executable, "-m", "yt_dlp", *yt_dlp_options(), "--dump-single-json", "--no-playlist", "--no-warnings", url],
        capture_output=True, text=True, timeout=45, env=yt_dlp_env(),
    )
    if result.returncode:
        raise ValueError("Não foi possível acessar este vídeo. Verifique se ele é público e tente novamente.")
    data = json.loads(result.stdout)
    duration = data.get("duration") or 0
    if duration > MAX_DURATION:
        raise ValueError("Este MVP aceita vídeos de até 1 hora.")
    return {"title": data.get("title") or "Vídeo", "channel": data.get("uploader") or "Canal não informado",
            "duration": int(duration), "thumbnail": data.get("thumbnail"), "url": url}


class Handler(BaseHTTPRequestHandler):
    def respond_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_request(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > 4096:
            raise ValueError("Envie um link válido.")
        data = json.loads(self.rfile.read(length))
        return normalized_url(data.get("url", "")), data.get("quality")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        assets = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/styles.css": ("styles.css", "text/css; charset=utf-8"),
                  "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/favicon.svg": ("favicon.svg", "image/svg+xml")}
        if path not in assets:
            self.send_error(404)
            return
        name, mime = assets[path]
        body = (ROOT / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path not in ("/api/inspect", "/api/download"):
            self.send_error(404)
            return
        try:
            url, quality = self.read_request()
            video = inspect_video(url)
            if self.path == "/api/inspect":
                self.respond_json(200, video)
                return
            if quality not in QUALITY_HEIGHTS:
                raise ValueError("Selecione uma qualidade: baixa, média ou boa.")
            max_height = QUALITY_HEIGHTS[quality]
            with tempfile.TemporaryDirectory() as folder:
                output = str(Path(folder) / "video.%(ext)s")
                result = subprocess.run(
                    [sys.executable, "-m", "yt_dlp", *yt_dlp_options(), "--no-playlist", "--no-warnings",
                     "--ffmpeg-location", ffmpeg_exe(), "--merge-output-format", "mp4", "-f",
                     f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={max_height}][ext=mp4]", "-o", output, url],
                    capture_output=True, text=True, timeout=3600, env=yt_dlp_env(),
                )
                files = list(Path(folder).glob("video.*"))
                if result.returncode or not files:
                    detail = result.stderr.lower()
                    if "requested format is not available" in detail:
                        raise ValueError("Este vídeo não oferece um formato MP4 compatível.")
                    if "sign in" in detail or "private" in detail:
                        raise ValueError("Este vídeo exige acesso ou não está disponível publicamente.")
                    raise ValueError("O download falhou. Tente novamente ou use outro vídeo público.")
                file = files[0]
                safe_title = re.sub(r"[^A-Za-z0-9_-]+", "-", video["title"]).strip("-")[:70] or "video"
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4" if file.suffix == ".mp4" else "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{safe_title}{file.suffix}"')
                self.send_header("Content-Length", str(file.stat().st_size))
                self.end_headers()
                with file.open("rb") as source:
                    while chunk := source.read(1024 * 1024):
                        self.wfile.write(chunk)
        except (ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            self.respond_json(400, {"error": str(exc) if not isinstance(exc, subprocess.TimeoutExpired) else "A operação demorou demais. Tente novamente."})
        except BrokenPipeError:
            pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = "0.0.0.0" if os.environ.get("CLOUDFLARE_CONTAINER") == "1" else "127.0.0.1"
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Servidor em http://{host}:{port}")
    server.serve_forever()
