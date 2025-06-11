import uvicorn, os, openai, requests
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt

# 'utcnow()'를 대체하기 위해 'timezone'을 import합니다.
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


"""
# 필요한 라이브러리 설치 명령어
pip install "fastapi[all]"
pip install "passlib[bcrypt]"
pip install "python-jose[cryptography]"
pip install openai
pip install requests
"""

# =================================================================
# 1. 보안 설정
# =================================================================

# 비밀번호 암호화를 위한 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT(JSON Web Token) 설정을 위한 비밀 키와 알고리즘
SECRET_KEY = "your-secret-key"  # 실제로는 더 복잡하고 안전한 키를 사용하세요!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# =================================================================
# 2. Pydantic 모델 정의
# =================================================================


class ProverbResponse(BaseModel):
    verse: str
    content: str
    comment: str


class ChatRequest(BaseModel):
    prompt: str  # 사용자가 보낼 메시지


class UserIn(BaseModel):  # 회원가입 시 받을 데이터
    email: str
    password: str
    nickname: str


class Token(BaseModel):  # 로그인 성공 시 보낼 데이터 (토큰)
    access_token: str
    token_type: str
    nickname: str


# =================================================================
# 3. 데이터베이스 대신 사용할 딕셔너리
# =================================================================

proverbs_by_mood = {
    "기쁨": {
        "verse": "잠언 17:22",
        "content": "마음의 즐거움은 양약이라도 심령의 근심은 뼈를 마르게 하느니라",
        "comment": "기쁜일이 있으시군요! 기쁨(행복한 마음)은 몸을 건강하게 합니다. 그 기쁜 순간을 더욱 누리기를 기도합니다.",
    },
    "슬픔": {
        "verse": "잠언 14:13",
        "content": "웃을 때에도 마음에 슬픔이 있고 즐거움의 끝에도 근심이 있느니라",
        "comment": "슬픈 일이 있으시군요.. 슬픔 가운데 에서도 다시 회복되기를 기도합니다.",
    },
    "무기력함": {
        "verse": "잠언 10:4",
        "content": "손을 게으르게 놀리는 자는 가난하게 되고 손이 부지런한 자는 부하게 되느니라",
        "comment": "무기력함은 곧 게으름으로 이어집니다. 게으름에서 벗어나 다시 부지런하게 되기를 기도합니다.",
    },
    "분노": {
        "verse": "잠언 14:29",
        "content": "노하기를 더디 하는 자는 크게 명철하여도 마음이 조급한 자는 어리석음을 나타내느니라",
        "comment": "마음이 조급하여 쉽게 분노하는 것 만큼 자신의 어리석음을 드러내는 일이 없습니다. 크게 심호흡하고 분노를 식힐 수 있기를 기도합니다.",
    },
    "불안": {
        "verse": "잠언 12:25",
        "content": "근심이 사람의 마음에 있으면 그것으로 번뇌하게 되나 선한 말은 그것을 즐겁게 하느니라",
        "comment": "불안할 때에도 선한 말들로 위로를 받아 불안이 조금은 사그라들기를 기도합니다.",
    },
}

# 사용자 정보를 저장할 딕셔너리
user_db = {}
# 채팅 기록을 저장할 딕셔너리
chat_history_db = {}


# =================================================================
# 4. FastAPI 앱 설정 및 인증 헬퍼 함수
# =================================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        # utcnow()를 최신 표준인 now(timezone.utc)로 수정
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # utcnow()를 최신 표준인 now(timezone.utc)로 수정
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception

    user_details = user_db.get(email)
    if user_details is None:
        raise credentials_exception

    return {"email": email, **user_details}


# =================================================================
# 5. API 엔드포인트
# =================================================================


@app.post("/register")
def register_user(user: UserIn):
    if user.email in user_db:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    hashed_password = get_password_hash(user.password)
    user_db[user.email] = {
        "hashed_password": hashed_password,
        "nickname": user.nickname,
    }
    print("현재 user_db 상태:", user_db)
    return {"message": f"{user.nickname}님, 회원가입이 완료되었습니다."}


@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = user_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )

    # user 딕셔너리에서 닉네임을 가져옵니다.
    nickname = user.get("nickname", "")

    # 토큰과 함께 닉네임도 반환합니다.
    return {"access_token": access_token, "token_type": "bearer", "nickname": nickname}


@app.post("/chat", response_model=ProverbResponse)
async def chat_with_ai(
    request: ChatRequest, current_user: dict = Depends(get_current_user)
):
    url = "https://dev.wenivops.co.kr/services/openai-api"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    prompt_for_classification = f"""
    사용자의 다음 문장을 읽고 '기쁨', '슬픔', '분노', '불안', '무기력함' 중 가장 적합한 감정 카테고리 하나만 골라서, 다른 말 없이 딱 그 단어만 출력해줘.
    문장: "{request.prompt}"
    """
    data = [
        {
            "role": "system",
            "content": "You are a helpful assistant that classifies emotions.",
        },
        {"role": "user", "content": prompt_for_classification},
    ]

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        mood_from_ai = response.json()["choices"][0]["message"]["content"].strip()
        print(f"사용자 입력: '{request.prompt}' -> AI 분석 감정: '{mood_from_ai}'")

        default_proverb = {
            "verse": "오류",
            "content": "감정을 분석할 수 없어요. 더 자세히 말씀해주시겠어요?",
            "comment": "",
        }
        proverb_data = proverbs_by_mood.get(mood_from_ai, default_proverb)

        user_email = current_user.get("email")

        # utcnow().isoformat을 최신 표준과 올바른 함수 호출로 수정
        chat_record = {
            "prompt": request.prompt,
            "response": proverb_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if user_email not in chat_history_db:
            chat_history_db[user_email] = []
        chat_history_db[user_email].append(chat_record)

        print(f"채팅 기록 저장됨: {user_email}")
        return proverb_data

    except Exception as e:
        print(f"API 최종 에러: {e}")
        raise HTTPException(status_code=500, detail="API 처리 중 오류가 발생했습니다.")


@app.get("/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    user_email = current_user.get("email")
    history = chat_history_db.get(user_email, [])
    return history


# =================================================================
# 6. 서버 실행
# =================================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
