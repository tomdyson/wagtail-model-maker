from typing import Union

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

from modelmaker import format_python, make_model

app = FastAPI()


@app.get("/api/ask")
async def ask(q: Union[str, None] = None):
    model_code = make_model(q)
    formatted_code = format_python(model_code)
    return {"response": formatted_code}


@app.get("/")
async def serve_index():
    """Serve index.html"""
    return FileResponse("index.html")


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, workers=1)
