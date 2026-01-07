from fastapi import FastAPI
import time

app = FastAPI()

@app.get("/sleep")
def sleep_endpoint(seconds: int = 60):
    time.sleep(seconds)
    return {"status": "ok", "slept": seconds}