from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class Message(BaseModel):
    message: str

@app.get("/echo")
async def echo_get(message: str):
    return {"echo": message}

@app.post("/echo")
async def echo_post(msg: Message):
    return {"echo": msg.message}

@app.post("/echo/raw")
async def echo_raw(request: Request):
    body = await request.body()
    return {"echo_raw": body.decode("utf-8")}
