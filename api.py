import uuid
from typing import Union

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from modelmaker import (
    format_python,
    make_model,
    make_model_from_image,
    suggest_improvements,
    usage_cost,
)

app = FastAPI()


class Question(BaseModel):
    q: str


@app.post("/api/ask")
async def ask(q: str = Form(...)):
    print(q)
    model_code, usage = make_model(q)
    formatted_code = format_python(model_code)
    return {"answer": formatted_code, "cost": usage_cost(usage)}


@app.post("/api/ask_image")
async def ask_image(screenshot: UploadFile = File(...)):
    filename = uuid.uuid4().hex + ".png"
    file_content = await screenshot.read()
    with open(filename, "wb") as file:
        file.write(file_content)
    model_code, usage = make_model_from_image(filename)
    formatted_code = format_python(model_code)
    return {"answer": formatted_code, "cost": usage_cost(usage)}


@app.get("/api/refine")
async def refine(q: Union[str, None] = None):
    refined_description, usage = suggest_improvements(q)
    return {"description": refined_description, "cost": usage_cost(usage)}


@app.get("/")
async def serve_index():
    """Serve index.html"""
    return FileResponse("index.html")


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, workers=1)
