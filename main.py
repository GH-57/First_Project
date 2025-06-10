import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 1. FastAPI 애플리케이션 생성
app = FastAPI()

# 2. CORS 미들웨어 설정
# 프론트엔드(HTML/JS)가 다른 주소(e.g., http://127.0.0.1:5500)에서 실행될 때
# 백엔드(http://127.0.0.1:8000)와 통신할 수 있도록 허용해주는 설정입니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중에는 모든 출처를 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

# 3. 데이터베이스 대신 사용할 Python 딕셔너리
# 프로젝트 초기에 DB 설정 없이 빠르게 핵심 기능을 테스트하기 위함입니다.
proverbs_by_mood = {
    "기쁨": {
        "verse": "잠언 17:22",
        "content": "마음의 즐거움은 양약이라도 심령의 근심은 뼈를 마르게 하느니라",
        "comment": "기쁨(행복한 마음)은 몸을 건강하게 합니다. 그 기쁜 순간을 더욱 누리기를 기도합니다."
    },
    "슬픔": {
        "verse": "잠언 14:13",
        "content": "웃을 때에도 마음에 슬픔이 있고 즐거움의 끝에도 근심이 있느니라",
        "comment": "슬픔 가운데 에서도 다시 회복되기를 기도합니다."
    },
    "무기력함": {
        "verse": "잠언 10:4",
        "content": "손을 게으르게 놀리는 자는 가난하게 되고 손이 부지런한 자는 부하게 되느니라",
        "comment": "무기력함은 곧 게으름으로 이어집니다. 게으름에서 벗어나 다시 부지런하게 되기를 기도합니다."
    },
    "분노": {
        "verse": "잠언 14:29",
        "content": "노하기를 더디 하는 자는 크게 명철하여도 마음이 조급한 자는 어리석음을 나타내느니라",
        "comment": "마음이 조급하여 쉽게 분노하는 것 만큼 자신의 어리석음을 드러내는 일이 없습니다. 크게 심호흡하고 분노를 식힐 수 있기를 기도합니다."
    },
    "불안": {
        "verse": "잠언 12:25",
        "content": "근심이 사람의 마음에 있으면 그것으로 번뇌하게 되나 선한 말은 그것을 즐겁게 하느니라",
        "comment": "불안할 때에도 선한 말들로 위로를 받아 불안이 조금은 사그라들기를 기도합니다."
    }
}


# 4. Pydantic 모델 정의
# 프론트엔드에서 보낼 요청(Request)과 백엔드에서 보낼 응답(Response)의 데이터 형식을 지정합니다.
# 이렇게 하면 FastAPI가 데이터 유효성 검사를 자동으로 해줍니다.

class MoodRequest(BaseModel):
    mood: str

class ProverbResponse(BaseModel):
    verse: str
    content: str
    comment: str


# 5. API 엔드포인트 생성
# @app.post("/recommend-proverb")는 /recommend-proverb 주소로 POST 요청이 왔을 때
# 아래 함수를 실행하라는 의미입니다.
@app.post("/recommend-proverb", response_model=ProverbResponse)
def recommend_proverb(request: MoodRequest):
    """
    사용자의 기분을 입력받아 그에 맞는 잠언과 해설을 반환합니다.
    """
    mood = request.mood
    
    # 사용자가 보낸 기분이 딕셔너리에 있는지 확인하고, 없으면 기본 메시지를 보냅니다.
    default_response = {
        "verse": "오류",
        "content": "해당하는 기분을 찾을 수 없습니다. 다른 기분을 선택해주세요.",
        "comment": ""
    }
    recommendation = proverbs_by_mood.get(mood, default_response)
    
    return recommendation

# 6. 서버 실행을 위한 설정 (개발용)
# 이 파일을 직접 실행할 때 (예: python main.py) uvicorn 서버를 구동합니다.
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)