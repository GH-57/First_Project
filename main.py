import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- 사용자 인증에 필요한 라이브러리 추가 ---
from typing import Optional
from passlib.context import CryptContext  # 비밀번호 암호화를 위함
from jose import JWTError, jwt  # JWT 토큰 생성을 위함
from datetime import datetime, timedelta
'''
# 비밀번호 암호화 라이브러리 (bcrypt 추가 설치)
pip install "passlib[bcrypt]"

# JWT 토큰 라이브러리 (cryptography 추가 설치)
pip install "python-jose[cryptography]"
'''
# =================================================================
# 1. 보안 설정
# =================================================================

# 비밀번호 암호화를 위한 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT(JSON Web Token) 설정을 위한 비밀 키와 알고리즘
# 이 SECRET_KEY는 외부에 노출되면 안 됩니다. 실제 프로젝트에서는 환경 변수로 관리해야 합니다.
SECRET_KEY = "your-secret-key"  # <-- 실제로는 더 복잡하고 안전한 키를 사용하세요!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# =================================================================
# 2. Pydantic 모델 정의
# =================================================================


# --- 기존 모델 ---
class MoodRequest(BaseModel):
    mood: str


class ProverbResponse(BaseModel):
    verse: str
    content: str
    comment: str


# --- 사용자 인증을 위한 모델 추가 ---
class UserIn(BaseModel):  # 회원가입 시 받을 데이터
    email: str
    password: str
    nickname: str


class UserLogin(BaseModel):  # 로그인 시 받을 데이터
    email: str
    password: str


class Token(BaseModel):  # 로그인 성공 시 보낼 데이터 (토큰)
    access_token: str
    token_type: str


# =================================================================
# 3. 데이터베이스 대신 사용할 딕셔너리
# =================================================================

# DB를 대신할 딕셔너리
proverbs_by_mood = {
    "기쁨": {
        "verse": "잠언 17:22",
        "content": "마음의 즐거움은 양약이라도 심령의 근심은 뼈를 마르게 하느니라",
        "comment": "기쁨(행복한 마음)은 몸을 건강하게 합니다. 그 기쁜 순간을 더욱 누리기를 기도합니다.",
    },
    "슬픔": {
        "verse": "잠언 14:13",
        "content": "웃을 때에도 마음에 슬픔이 있고 즐거움의 끝에도 근심이 있느니라",
        "comment": "슬픔 가운데 에서도 다시 회복되기를 기도합니다.",
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

# 사용자 정보를 저장할 딕셔너리 (In-memory DB)
# key: email, value: { "hashed_password": "...", "nickname": "..." }
user_db = {}


# =================================================================
# 4. FastAPI 앱 설정 및 인증 헬퍼 함수
# =================================================================
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 인증 헬퍼 함수 ---
def verify_password(plain_password, hashed_password):
    """입력된 비밀번호와 저장된 해시 비밀번호를 비교합니다."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """비밀번호를 해시하여 반환합니다."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT 액세스 토큰을 생성합니다."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# =================================================================
# 5. API 엔드포인트
# =================================================================


# --- 기존 엔드포인트 (아직 수정 안 함) ---
@app.post("/recommend-proverb", response_model=ProverbResponse)
def recommend_proverb(request: MoodRequest):
    recommendation = proverbs_by_mood.get(
        request.mood,
        {
            "verse": "오류",
            "content": "해당하는 기분을 찾을 수 없습니다.",
            "comment": "",
        },
    )
    return recommendation


# --- 사용자 인증 엔드포인트 추가 ---
@app.post("/register")
def register_user(user: UserIn):
    """회원가입 엔드포인트"""
    if user.email in user_db:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    hashed_password = get_password_hash(user.password)
    user_db[user.email] = {
        "hashed_password": hashed_password,
        "nickname": user.nickname,
    }

    # 디버깅을 위해 DB 상태 출력 (실제 운영에서는 삭제)
    print("현재 user_db 상태:", user_db)

    return {"message": f"{user.nickname}님, 회원가입이 완료되었습니다."}


@app.post("/login", response_model=Token)
def login_for_access_token(user_login: UserLogin):
    """로그인 엔드포인트, 성공 시 액세스 토큰 반환"""
    user = user_db.get(user_login.email)
    if not user or not verify_password(user_login.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 토큰에 담을 데이터 (sub는 보통 사용자를 식별하는 값으로 사용)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_login.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# =================================================================
# 6. 서버 실행
# =================================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
