from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="LinkedIn Jobs API",
    description="API for accessing scraped LinkedIn job listings.",
    version="1.0.0"
)

# CORS config to allow frontend to fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "API is running. Visit /docs for Swagger."}
