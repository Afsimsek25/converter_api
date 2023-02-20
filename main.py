from fastapi import FastAPI
from routers import converter
app = FastAPI()

app.include_router(converter.router)
@app.get("/")
async def root():
    return {"message": "Hello World"}
