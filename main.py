from fastapi import FastAPI
from routers import converter
app = FastAPI()

app.include_router(converter.router)

