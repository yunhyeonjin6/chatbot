from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel

app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)


class Item(BaseModel):
    name: str
    description: str
    price: float

@app.get("/items/")
async def read_items():
    # This is just an example; you would fetch and return your actual data here
    return [
        {"name": "Item 1", "description": "Description 1", "price": 10.0},
        {"name": "Item 2", "description": "Description 2", "price": 20.0}
    ]


class Event(BaseModel):
    name: str
    eng_name: str
    date_list: List[str]

class Response(BaseModel):
    status_code: int
    message: str
    data: List[Event]

@app.post("/dateSearch")
def receive_events(response: Response):
    print(type(response))
    if isinstance(response, list):
        if response:
            print(type(response[0]))
    return {"status": "success"}


# class DataModel(BaseModel):
#     data: str

# @app.post("/dateSearch")
# def submit_data(data: DataModel):
#     print(data.data)
#     a = data
#     print(type(a))
#     if isinstance(a, list):
#         if a:
#             print(type(a[0]))
		
#     return {"status": "success"}

@app.get("/")
async def root():
    return {"message": "Hello World"}


# class DataModel(BaseModel):
#     code: str
#     password: str

# @app.post("/submit_data")
# def restore(data: DataModel):
#     # 요청 데이터 처리
#     print("Code:", data.code)
#     print("Password:", data.password)

#     # 파일에 데이터 저장
#     with open("data.txt", "w") as file:
#         file.write(data.code)

#     # 처리 결과 반환
#     return {"status": "success"}