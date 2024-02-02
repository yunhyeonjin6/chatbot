import pandas as pd
import streamlit as st
from tzzim import Tzzim
tzzim = Tzzim() # InitValues 클래스에서 session_state 초기화

# 탭 제목
st.set_page_config(page_title="⛳티찜 AI")

# 첫 질문
if not st.session_state.login['first_question']:
    tzzim.text_to_audio(st.session_state.messages[0]['content']) 
    st.session_state.login['first_question'] = True

# 새로운 입력이 들어올 때마다 현재까지 누적된 대화를 전부 새로 표기함
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
            
# try:
# 3. 입력 및 답변
# 3-1. 입력
if customer_answer := st.chat_input("티찜 AI에게 부탁하세요! ex) 골프장 예약", disabled=st.session_state.stop_input):
    st.session_state.messages.append({"role": "user", "content": customer_answer})
    with st.chat_message("user"):
        st.write(customer_answer) # user 답변 바로 표기
    st.session_state.dialogue[-1] += f'사용자:{customer_answer}' # dialogue 한 element 형식: [question]\n:[customer_answer]

# 3-2. 답변; 모든 경우에 대해 response 변수를 채우기
if st.session_state.messages[-1]["role"] != "assistant":
    with st.spinner("답변 준비 중..."):
        ##
        prior_dialogue = st.session_state.dialogue[:-1] 
        add_dialogue = st.session_state.dialogue[-1]
        dialogue = f"기존 대화:\n\t{prior_dialogue}\n" +\
                    f"추가된 대화:\n\t{add_dialogue}"
        ##
        # print(dialogue)
        # 예약확인 후 사용자의 답변에 따라 예약내용을 수정하는 질문을하거나 / 예약을 완료함
        if st.session_state.correction_session and not st.session_state.json_check["correction"]: # "correction" 조건 예약 수정 시 중요함
            # print('reservation_validation')
            response = tzzim.reservation_validation(dialogue)

        # 예약 정보를 받는 단계
        else:
            response = tzzim.response_generation(dialogue)
            
    # # 디버깅용: 활성화 시 대화문 중복해서 뜨지만 비활성화 시 뜨지 않음
    # st.write(f"dialogue: {dialogue}") ## 누적된 대화추적, 질문 생성 전까지의 대화내역 표시
    st.write('대화내역에서 NER을 한 json 데이터 (ChatGPT):')
    st.json(tzzim.to_json(st.session_state.json_string), expanded=False) ## json_string 추적, 질문 생성 후 json_sring 내용표시
    # st.write(f"verification: {st.session_state.json_check['verification']}") ## verification 추적
    st.write('데이터 필터링에 사용되는 json 데이터 (규칙기반):')
    st.json(st.session_state.json_condition, expanded=False)
    st.write('response: ', response)

    ## 4. 예약완료 확인단계
    full_response = tzzim.complete_or_ongoing(response)
    
    # 메시지 저장 및 대화내용을 누적하여 업데이트
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
    question = full_response ##
    st.session_state.dialogue.append(f"티찜AI:{question}\n") ##
# except:
#     st.write(st.session_state.json_condition)