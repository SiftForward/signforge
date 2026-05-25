"""signforge web interface — FastAPI app.

Run:
    uvicorn signforge.web:app --reload
or:
    python -m signforge.server
"""
from __future__ import annotations

import base64
import tempfile
import uuid
from pathlib import Path
from typing import Annotated, Optional

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from .render import render
from .sign import Sign

app = FastAPI(title="SignForge", docs_url=None, redoc_url=None)

_TEMPLATE_DIR = Path(__file__).parent / "templates"

# Temp dir for generated files — scoped to process lifetime.
_TMP_DIR = Path(tempfile.mkdtemp(prefix="signforge_"))


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
    lines = [l for l in [line1, line2, line3] if l and l.strip()]

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

    token = uuid.uuid4().hex
    base = _TMP_DIR / token
    svg_path = base.with_suffix(".svg")
    dxf_path = base.with_suffix(".dxf")
    png_path = base.with_suffix(".png")

    try:
        render(sign, svg_path, dxf_path=dxf_path, png_preview=str(png_path))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Encode PNG as base64 for inline display
    png_b64: Optional[str] = None
    if png_path.exists():
        png_b64 = base64.b64encode(png_path.read_bytes()).decode()

    return JSONResponse({
        "token": token,
        "png_b64": png_b64,
        "has_svg": svg_path.exists(),
        "has_dxf": dxf_path.exists(),
    })


@app.get("/api/download/{token}/{fmt}")
async def download(token: str, fmt: str):
    if fmt not in ("svg", "dxf"):
        raise HTTPException(status_code=400, detail="fmt must be svg or dxf")
    # Sanitise token — must be hex only
    if not all(c in "0123456789abcdef" for c in token) or len(token) != 32:
        raise HTTPException(status_code=400, detail="invalid token")
    path = _TMP_DIR / f"{token}.{fmt}"
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found or expired")
    media = "image/svg+xml" if fmt == "svg" else "application/dxf"
    return FileResponse(str(path), media_type=media,
                        filename=f"sign.{fmt}")
