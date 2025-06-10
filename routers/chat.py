from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 1. API가 받을 데이터의 형식을 Pydantic으로 정의합니다.
class ChatRequest(BaseModel):
    mood: str

# 2. 데이터베이스 역할을 할 Python 딕셔너리를 만듭니다.
PROVERBS = {
    "기쁨": {
        "verse": "(잠언 17:22) 마음의 즐거움은 양약이라도 심령의 근심은 뼈를 마르게 하느니라.",
        "message": "그 기쁜 순간을 더욱 누리기를 기도합니다."
    },
    "슬픔": {
        "verse": "(잠언 14:13) 웃을 때에도 마음에 슬픔이 있고 즐거움의 끝에도 근심이 있느니라.",
        "message": "슬픔 가운데에서도 다시 회복되기를 기도합니다."
    },
    "무기력함": {
        "verse": "(잠언 10:4) 손을 게으르게 놀리는 자는 가난하게 되고 손이 부지런한 자는 부하게 되느니라.",
        "message": "무기력함은 곧 게으름으로 이어집니다. 게으름에서 벗어나 다시 부지런하게 되기를 기도합니다."
    },
    "분노": {
        "verse": "(잠언 14:29) 노하기를 더디 하는 자는 크게 명철하여도 마음이 조급한 자는 어리석음을 나타내느니라. ",
        "message": "마음이 조급하여 쉽게 분노하는 것 만큼 자신의 어리석음을 드러내는 일이 없습니다. 크게 심호흡하고 분노를 식힐 수 있기를 기도합니다."
    },
    "불안": {
        "verse": "(잠언 12:25) 근심이 사람의 마음에 있으면 그것으로 번뇌하게 되나 선한 말은 그것을 즐겁게 하느니라.",
        "message": "불안할 때에도 선한 말들로 위로를 받아 불안이 조금은 사그라들기를 기도합니다."
    }
}

# 3. APIRouter 객체를 생성합니다.
router = APIRouter()

# 4. API 엔드포인트를 정의합니다.
@router.post("/chat")
async def get_proverb_for_mood(request: ChatRequest):
    """
    사용자의 기분(mood)을 받아 해당하는 잠언과 메시지를 반환합니다.
    """
    mood = request.mood
    
    # 딕셔너리에서 기분에 해당하는 잠언을 찾습니다.
    response_data = PROVERBS.get(mood)
    
    # 만약 해당하는 기분이 딕셔너리에 없으면 404 에러를 반환합니다.
    if not response_data:
        raise HTTPException(status_code=404, detail=f"'{mood}'에 해당하는 잠언을 찾을 수 없습니다.")
        
    # 찾았다면 해당 데이터를 반환합니다.
    return response_data