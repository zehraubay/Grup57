from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import auth, greenscan, crisis, user_router
from routers.greenscan import router as greenlens_router
from database import Base, engine
from dotenv import load_dotenv
import os


load_dotenv()

app = FastAPI(title="GreenLens Earth API")

frontend_path = os.path.abspath(r"C:\Users\lerha\OneDrive\Masaüstü\hack\frontend")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/frontend", StaticFiles(directory=r"C:\Users\lerha\OneDrive\Masaüstü\hack\frontend"), name="frontend")

@app.get("/")
def login_page():
    return FileResponse(os.path.join(frontend_path, "login.html"))

@app.get("/home")
def home_page():
    return FileResponse(os.path.join(frontend_path, "index.html"))

app.include_router(auth.router)
app.include_router(greenscan.router)
app.include_router(crisis.router)
app.include_router(user_router.router)
app.include_router(greenlens_router)

Base.metadata.create_all(bind=engine)
