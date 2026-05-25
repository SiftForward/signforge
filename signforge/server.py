"""Entry point: python -m signforge.server"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("signforge.web:app", host="0.0.0.0", port=8000, reload=True)
