# Vercel entry point — imports the FastAPI app from the signforge package.
from signforge.web import app  # noqa: F401 — Vercel looks for `app`
