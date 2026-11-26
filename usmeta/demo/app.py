"""Local research-demo UI for ultrasound draft generation and reference scoring."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from email.parser import BytesParser
from email.policy import default
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[1]
USMETA_ROOT = REPO_ROOT / "usmeta"
MAX_UPLOAD = 12 * 1024 * 1024
ALLOWED_IMAGES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
MODEL_PYTHON = Path(os.environ.get("USMETA_MLX_VLM_PY", "~/venvs/mlx312/bin/python")).expanduser()
MODEL_SCRIPT = USMETA_ROOT / "usmeta" / "medgemma_mlx.py"
MODEL_PATH = Path.home() / ".cache/usmeta/medgemma-1.5-4b-it-4bit"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DEMO_DIR), **kwargs)

    def log_message(self, fmt, *args):
        print("[demo] " + fmt % args, flush=True)

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        route = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_UPLOAD + 64_000:
            return self._json(413, {"error": "Upload is empty or exceeds the 12 MB limit."})
        body = self.rfile.read(length)
        if route == "/api/generate":
            return self._generate(body)
        if route == "/api/score":
            return self._score(body)
        return self._json(404, {"error": "Unknown endpoint."})

    def _multipart(self, body):
        content_type = self.headers.get("Content-Type", "")
        message = BytesParser(policy=default).parsebytes(
            b"Content-Type: " + content_type.encode("ascii", "replace") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
        )
        values = {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if not name:
                continue
            data = part.get_payload(decode=True) or b""
            values[name] = {
                "filename": part.get_filename(),
                "type": part.get_content_type(),
                "data": data,
            }
        return values

    def _generate(self, body):
        fields = self._multipart(body)
        image = fields.get("image", {})
        organ = fields.get("organ", {}).get("data", b"").decode("utf-8", "replace")
        if organ not in {"breast", "thyroid", "fetal"}:
            return self._json(400, {"error": "Choose breast, thyroid, or fetal head."})
        if image.get("type") not in ALLOWED_IMAGES or not image.get("data"):
            return self._json(400, {"error": "Upload a PNG, JPEG, or WebP ultrasound image."})
        if not MODEL_PYTHON.exists() or not MODEL_SCRIPT.exists() or not MODEL_PATH.exists():
            return self._json(503, {"error": "Local MedGemma runtime or model files were not found. See the demo README."})

        from usmeta import generate

        prompt = generate.PROMPT.format(organ=generate.ORGAN_WORD[organ])
        with tempfile.TemporaryDirectory(prefix="usmeta-demo-") as temp_dir:
            temp = Path(temp_dir)
            suffix = ALLOWED_IMAGES[image["type"]]
            image_path = temp / ("upload" + suffix)
            image_path.write_bytes(image["data"])
            jobs_path = temp / "jobs.json"
            output_path = temp / "output.jsonl"
            jobs_path.write_text(
                json.dumps(
                    [
                        {
                            "id": "demo-report",
                            "key": "demo-report",
                            "kind": "report",
                            "image": str(image_path),
                            "flip": False,
                            "prompt": prompt,
                            "max_tokens": 220,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            try:
                result = subprocess.run(
                    [str(MODEL_PYTHON), str(MODEL_SCRIPT), str(jobs_path), str(output_path)],
                    capture_output=True,
                    text=True,
                    timeout=600,
                    cwd=str(USMETA_ROOT),
                )
            except subprocess.TimeoutExpired:
                return self._json(504, {"error": "Report generation exceeded the 10-minute demo limit."})
            if result.returncode != 0 or not output_path.exists():
                return self._json(500, {"error": "MedGemma generation failed. Check the local model setup and server log."})
            generated = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])
            return self._json(
                200,
                {
                    "report": generated.get("text", ""),
                    "model": "MedGemma 1.5 4B, local 4-bit MLX-VLM",
                    "seconds": generated.get("seconds"),
                    "notice": "Research draft only. It is not a diagnosis or a clinically validated report.",
                },
            )

    def _score(self, body):
        try:
            request = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"error": "Send valid JSON."})
        organ = request.get("organ")
        candidate = str(request.get("candidate", "")).strip()
        reference = str(request.get("reference", "")).strip()
        if organ not in {"breast", "thyroid", "fetal"}:
            return self._json(400, {"error": "Choose breast, thyroid, or fetal head."})
        if not candidate or not reference:
            return self._json(400, {"error": "A candidate and a reference report are both required for comparison."})
        if max(len(candidate), len(reference)) > 30_000:
            return self._json(413, {"error": "Reports must be 30,000 characters or fewer."})

        sys.path.insert(0, str(USMETA_ROOT))
        from usmeta import schema, step27_extractor, step45_extractor_v5 as v5, step46_eval

        cache_dir = Path.home() / ".cache/usmeta"
        cache_dir.mkdir(parents=True, exist_ok=True)
        step27_extractor.CACHE = str(cache_dir / "demo_extractor_v5.jsonl")
        row = {
            "organ": organ,
            "ref": reference,
            "cand": candidate,
            "gold": schema.extract_rule(reference, organ),
            "severity": None,
        }
        try:
            extractor = step27_extractor.Extractor("v5")
            raw = extractor.raw(organ, candidate)
            flat, parse_ok, _ = v5.facts_v5(organ, raw, candidate)
            differences = step46_eval.rule_result(row, flat)
        except Exception as exc:
            return self._json(500, {"error": "Could not run the local report extractor: " + str(exc)[:240]})

        penalties = {"critical": 0.6, "major": 0.3, "minor": 0.1}
        flags = []
        score = 1.0
        for field, detector in differences.items():
            severity = step46_eval.severity_for(organ, field, row)
            score -= penalties[severity]
            flags.append(
                {
                    "field": field,
                    "detected_by": detector,
                    "severity": severity,
                    "reference_value": row["gold"].get(field),
                    "candidate_value": flat.get(field),
                }
            )
        score = max(0.0, score)
        return self._json(
            200,
            {
                "score": round(score, 3),
                "flags": flags,
                "extracted_facts": flat,
                "parse_ok": bool(parse_ok),
                "scorer": "UScore rules preview",
                "notice": "Reference-based research preview; it does not run the holistic judge or image check and is not clinically validated. A high score does not establish correctness.",
            },
        )


def main():
    sys.path.insert(0, str(USMETA_ROOT))
    host = os.environ.get("USMETA_DEMO_HOST", "127.0.0.1")
    port = int(os.environ.get("USMETA_DEMO_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Ultrasound scorer demo: http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
