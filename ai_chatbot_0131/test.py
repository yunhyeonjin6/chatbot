import json
import requests
import streamlit as st
import time

# from api import TzzimAPI
import openai
# ta = TzzimAPI()


# config
BASE_API_URL = 'http://192.168.0.7:8080'
openai.api_key = "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"

# 함수
def chatgpt_return(user_prompt:str, system_prompt:str="당신은 골프장의 예약을 담당하는 직원입니다.") -> str:
    # ChatGPT 사용
    messages = [
        {"role": "user", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0 # top_p는 같이 쓰라고 권장되지 않음
    )

    result = repr(completion.choices[0].message['content']) # ChatGPT 사용결과    

    return result

template = lambda dialogue, instruction: f""" 다음 입력은 손님이 골프장을 예약하기 위해 당신에게 건넨 대화입니다.\n\n{dialogue}\n\n{instruction}"""


# 데이터 
json_string = requests.post(BASE_API_URL + "/dataSearch")
if isinstance(json_string, str):
    json_to_put = json_string
else:
    json_to_put = json_string.text
json_raw = json.loads(json_to_put)
if json_raw['status_code'] == 200:
    data_list:list[dict] = json_raw['data']
    print(data_list)
else:
    pass

# session_state
if 'messages' not in st.session_state.keys():
    st.session_state['messages'] = [{"role": "assistant", "content": "안녕하세요! 골프예약인공지능 티찜AI입니다. 무엇을 도와드릴까요?"}]
if 'dialogue' not in st.session_state.keys():
    st.session_state['dialogue'] = ["티찜AI:안녕하세요! 골프예약인공지능 티찜AI입니다. 무엇을 도와드릴까요?"]

# 새로운 입력이 들어올 때마다 현재까지 누적된 대화를 전부 새로 표기함
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if customer_answer := st.chat_input("티찜 AI에게 부탁하세요! ex) 골프장 예약"):
    st.session_state.messages.append({"role": "user", "content": customer_answer})
    with st.chat_message("user"):
        st.write(customer_answer) # user 답변 바로 표기
    st.session_state.dialogue[-1] += f'사용자:{customer_answer}'

if st.session_state.messages[-1]["role"] != "assistant":
    with st.spinner("대화내용을 분석 중..."):
        dialogue = '\n'.join(st.session_state.dialogue)
        instruction = '사용자에게 적절한 질문을 해주세요.'
        user_prompt = template(dialogue, instruction)
        response = chatgpt_return(dialogue)

    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
    question = response ##
    st.session_state.dialogue.append(f"티찜AI:{question}\n") ##



# if __name__ == "__main__":
#     json_string = requests.post(BASE_API_URL + "/clubInfoList")
#     if isinstance(json_string, str):
#         json_to_put = json_string
#     else:
#         json_to_put = json_string.text
#         # print('json_string_type: ', type(json_string))
#         # print('json_string_text: ', json_string.text)
#     json_raw = json.loads(json_to_put)
#     if json_raw['status_code'] == 200:
#         data_list:list[dict] = json_raw['data']
#         st.write(data_list)
#     else:
#         pass