"""signforge web interface — FastAPI app.

Run locally:
    uvicorn signforge.web:app --reload
or:
    python -m signforge.server

Deployment: all generated files are returned as base64 in the JSON response
so the app is fully stateless (works on Vercel serverless, Railway, etc.).
"""
from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Annotated, Optional

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from .render import render
from .sign import Sign

app = FastAPI(title="SignForge", docs_url=None, redoc_url=None)

_TEMPLATE_DIR = Path(__file__).parent / "templates"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse((_TEMPLATE_DIR / "index.html").read_text(encoding="utf-8"))


@app.post("/api/generate")
async def generate(
    style: Annotated[str, Form()] = "cyberpunk",
    emblem: Annotated[Optional[str], Form()] = None,
    header: Annotated[Optional[str], Form()] = None,
    line1: Annotated[Optional[str], Form()] = None,
    line2: Annotated[Optional[str], Form()] = None,
    line3: Annotated[Optional[str], Form()] = None,
    sub: Annotated[Optional[str], Form()] = None,
    width: Annotated[float, Form()] = 24.0,
    height: Annotated[float, Form()] = 8.0,
    border: Annotated[bool, Form()] = True,
    cap_main_max: Annotated[float, Form()] = 1.25,
    emblem_zone: Annotated[float, Form()] = 8.0,
):
    lines = [ln for ln in [line1, line2, line3] if ln and ln.strip()]

    sign = Sign(
        style=style,
        emblem=emblem or None,
        header=header or None,
        lines=lines,
        sub=sub or None,
        width=width,
        height=height,
        border=border,
        cap_main_max=cap_main_max,
        emblem_zone_width=emblem_zone,
    )

    # Use a per-request temp dir; cleaned up after we've read the files.
    with tempfile.TemporaryDirectory(prefix="signforge_") as tmp:
        base = Path(tmp) / "sign"
        svg_path = base.with_suffix(".svg")
        dxf_path = base.with_suffix(".dxf")
        png_path = base.with_suffix(".png")

        try:
            render(sign, svg_path, dxf_path=dxf_path, png_preview=str(png_path))
        except Exception as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        def _b64(p: Path) -> Optional[str]:
            return base64.b64encode(p.read_bytes()).decode() if p.exists() else None

        return JSONResponse({
            "png_b64": _b64(png_path),
            "svg_b64": _b64(svg_path),
            "dxf_b64": _b64(dxf_path),
        })
