from fastapi import FastAPI
from .routers import chat
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],  # PE가 실행되는 origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "오늘의 기분에 따른 잠언 추천 챗봇 API"}


