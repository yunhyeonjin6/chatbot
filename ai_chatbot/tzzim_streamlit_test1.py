import streamlit as st
from tzzim import Tzzim
from streamlit.components.v1 import html
import requests
from io import BytesIO

tzzim = Tzzim()

# 제목
st.set_page_config(page_title="⛳티찜 AI")

# def callAndroidMethod():
#     st.components.v1.html("""
#         <script>
#         function getDataFromAndroid() {
#             return new Promise((resolve, reject) => {
#             if (window.AndroidBridge) {
#                 resolve(window.AndroidBridge.getData());
#             } else {
#                 reject("No data");
#             }
#             });
#         }
#         getDataFromAndroid()
#             .then((data) => {
#             console.log("data : ", data);
#             localStorage.setItem("myKey", data);
#             console.log(localStorage.getItem("myKey"));
#             })
#             .catch((error) => {
#             console.log("error!!! ", error);
#             });
#         </script>
#     """)


# 웹브라우저에 stt 구현
def stt_component():
    st.components.v1.html("""
        <h2>음성을 텍스트로 변환하기</h2>

        <button id="startBtn">음성 입력 시작</button>
        <p id="outputText">여기에 변환된 텍스트가 나타납니다.</p>

        <script>
            document.addEventListener('DOMContentLoaded', function () {
                const startBtn = document.getElementById('startBtn');
                const outputText = document.getElementById('outputText');
                let recognition;

                if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
                    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                    recognition.continuous = true;
                    recognition.interimResults = true;

                    recognition.onstart = function () {
                        console.log('음성 입력 시작');
                    };

                    recognition.onresult = function (event) {
                        const result = event.results[event.resultIndex];
                        const transcript = result[0].transcript;
                        outputText.innerText = transcript;
                    };

                    recognition.onend = function () {
                        console.log('음성 입력 종료');
                    };

                    recognition.onerror = function (event) {
                        console.error('음성 인식 에러', event.error);
                    };

                    startBtn.addEventListener('click', function () {
                        recognition.start();
                    });
                } else {
                    outputText.innerText = '죄송합니다. 현재 이 브라우저는 음성 인식을 지원하지 않습니다.';
                    startBtn.disabled = true;
                }
            });
        </script>
    """)


# st.setComponentValue('update_session_state', transcript);

# # JavaScript로부터 전달받은 텍스트(transcript)를 st.session_state.text_result에 저장하는 역할
# def update_session_state(transcript):
#     st.session_state.text_result = transcript

# Streamlit 애플리케이션 시작
stt_component()

# # 세션 상태에서 변환된 텍스트를 가져와서 화면에 출력
# if 'text_result' in st.session_state:
#     print("print : ", st.session_state.text_result)
    


# 파이썬으로 stt 구현
# # Google Web Speech API 키 (본인의 키로 교체 필요)
# API_KEY = "YOUR_GOOGLE_API_KEY"

# def stt_component():
#     st.header("음성을 텍스트로 변환하기")
    
#     # 음성 입력 및 텍스트 출력 영역
#     text_result = st.empty()
#     start_button = st.button("음성 입력 시작")
    
#     if start_button:
#         # 음성 입력 시작 버튼이 클릭되면 음성을 텍스트로 변환
#         audio_data = perform_audio_recording()
#         transcript = perform_speech_to_text(audio_data)
#         text_result.text(f"음성 입력 결과: {transcript}")
        
#         # 변환된 텍스트를 Streamlit 세션 상태에 저장
#         st.session_state.text_result = transcript

# # Streamlit 세션에서 음성을 텍스트로 변환하는 Python 함수
# def perform_speech_to_text(audio_data):
#     api_url = "https://speech.googleapis.com/v1/speech:recognize"
#     params = {
#         "key": API_KEY,
#     }

#     # 음성 데이터를 API에 전송
#     response = requests.post(api_url, params=params, json={
#         "config": {
#             "encoding": "LINEAR16",
#             "sampleRateHertz": 16000,
#             "languageCode": "ko-KR",
#         },
#         "audio": {
#             "content": audio_data,
#         }
#     })

#     # API 응답에서 텍스트 추출
#     result = response.json()
#     transcript = result.get("results", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")

#     return transcript

# # Streamlit 세션에서 음성을 녹음하는 Python 함수
# def perform_audio_recording():
#     # 여기에 실제 음성 녹음 로직을 구현합니다.
#     # Microphone 라이브러리 등을 사용하여 음성을 녹음하고, 바이너리 데이터로 변환합니다.
#     # 실제 녹음된 음성 데이터를 반환합니다.
#     return b""

# # Streamlit 애플리케이션 시작
# stt_component()

# # 세션 상태에서 변환된 텍스트를 가져와서 화면에 출력
# if 'text_result' in st.session_state:
#     st.write("세션 상태에서 가져온 결과:", st.session_state.text_result)


# 음성 추가를 위한 공간
with st.sidebar:
    st.sidebar.button('초기화', on_click=tzzim.clear_chat_history) # 임시로 다른 함수를 인수로 넣음
    
# 주석이 '##'로 시작하면 전부 streamlit용 로직이 아닌 골프 예약용 로직입니다.
# 1. 초기화
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": tzzim.initial_question}]

if "dialogue" not in st.session_state.keys(): ##
    st.session_state.dialogue = [f"{tzzim.initial_question}\n"]
    
if "stop_input" not in st.session_state.keys():
    st.session_state.stop_input = False
    
if "correction_session" not in st.session_state.keys():
    st.session_state.correction_session = False
    
if "json_string" not in st.session_state.keys():
    st.session_state.json_string = str(tzzim.json_obj)
    
if "json_check" not in st.session_state.keys():
    st.session_state.json_check = tzzim.json_check_init
    
# 2. 새로운 입력이 들어올 때마다 현재까지 누적된 대화를 전부 새로 표기함
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
# 3. 입력 및 답변
# 3-1. 입력
if customer_answer := st.chat_input("티찜 AI에게 부탁하세요! ex) 골프장 예약을 하고 싶어", disabled=st.session_state.stop_input):
    st.session_state.messages.append({"role": "user", "content": customer_answer})
    with st.chat_message("user"):
        st.write(customer_answer) # user 답변 바로 표기
    st.session_state.dialogue[-1] += f':{customer_answer}' ##

# 3-2. 답변; 모든 경우에 대해 response 변수를 채우기
if st.session_state.messages[-1]["role"] != "assistant":
    with st.spinner("답변 준비 중..."):
        ##
        prior_dialogue = st.session_state.dialogue[:-1] 
        add_dialogue = st.session_state.dialogue[-1]
        dialogue = f"기존 대화:\n\t{prior_dialogue}\n" +\
                    f"추가된 대화:\n\t{add_dialogue}"
        ##
        
        if st.session_state.correction_session and not st.session_state.json_check["correction"]: # "correction" 조건 예약 수정 시 중요함
            tzzim.update_json_completion(dialogue) # 확인 업데이트
            json_completion_check = tzzim.to_json(st.session_state.json_check['completion'])
            wrong_key = json_completion_check['reservation_not_completed_reason']
                
            # st.write(f"completion: {json_completion_check}") ## completion 추적
            
            if json_completion_check['reservation_complete']:
                st.session_state.stop_input = True
                response = f"{tzzim.to_json(st.session_state.json_string)['task']} 작업이 완료되었습니다. 티찜AI를 이용해주셔서 감사합니다."
                with st.chat_message('assistant'):
                    st.write(response)
                st.button('다시하기', on_click=tzzim.clear_chat_history)
                json_obj_completion = "완료"
                
            elif not json_completion_check['reservation_complete'] and (wrong_key != 'null'):
                response = f"{tzzim.json_keyname[wrong_key]} 항목을 수정해드리겠습니다. 다시 말씀해주시겠습니까? 다음 조건을 참고하셔서 답변 부탁드립니다.\n" + tzzim.key_condition_list[wrong_key]
                
                # 다시 물어본 예약정보 json 키의 value 값을 "null"로 직접 대체
                json_obj_completion = tzzim.to_json(st.session_state.json_string)
                json_obj_completion[wrong_key] = "null"
                st.session_state.json_string = str(json_obj_completion)
                st.session_state.json_check["correction"] = True # 예약 수정 시 중요함
                
            elif not json_completion_check['reservation_complete'] and (wrong_key == 'null'):
                response = "예약정보의 어떤 항목을 수정하시겠습니까?"
                
                with st.chat_message('assistant'):
                    st.write(response)
            
            else:
                response = f"오류가 발생하였습니다. 개발자에게 이 결과를 캡쳐하여 보내주세요.\njson_completion: {st.session_state.json_check['completion']}\n개발자 이메일: dahae@ellexi.com"

            # st.write(f"json_obj_completion: {json_obj_completion}") ## json 추적

        else:
            tzzim.update_json_string(dialogue) # 예약정보 업데이트
            tzzim.update_json_verification(dialogue) # 검증 업데이트
            json_obj_check = tzzim.to_json(st.session_state.json_string)
            json_verification_check = st.session_state.json_check['verification']
            
            if json_verification_check['json_all_correct']:
                response = tzzim.question_from_null(dialogue)
            elif st.session_state.json_check["correction"]:
                pass
            else:
                wrong_key = json_verification_check['json_key_not_correct']
                if json_obj_check[wrong_key] == 'null': # verification의 내용이 'null'만 있어도 잘못되었다고 판단하기 때문에 기준을 넣음
                    response = tzzim.question_from_null(dialogue)
                else:
                    response = f"{tzzim.json_keyname[wrong_key]}에 대해 다시 여쭤봐도 되겠습니까? 다음 조건을 참고하셔서 답변 부탁드립니다.\n" + tzzim.key_condition_list[wrong_key]
                    
                    # 다시 물어본 예약정보 json 키의 value 값을 "null"로 직접 대체
                    json_obj_check[wrong_key] = "null"
                    st.session_state.json_string = str(json_obj_check)
            
    # # 디버깅용: 활성화 시 대화문 중복해서 뜨지만 비활성화 시 뜨지 않음
    # st.write(f"dialogue: {dialogue}") ## 누적된 대화추적, 질문 생성 전까지의 대화내역 표시
    # st.write(f"json: {st.session_state.json_string}") ## json_string 추적, 질문 생성 후 json_sring 내용표시
    # st.write(f"verification: {st.session_state.json_check['verification']}") ## verification 추적
        
    ## 4. 질문 가공
    json_completion = tzzim.to_json(st.session_state.json_check['completion'])
    complete_initial = (json_completion['reservation_complete'] == 'null') and (json_completion['reservation_not_completed_reason'] == 'null')
    complete_condition1 = json_completion['reservation_complete'] and (json_completion['reservation_complete'] != 'null') # 예약 완료
    complete_condition2 = st.session_state.json_check["correction"] # 예약수정 의사와 수정된 답변 모두 받은 경우, 예약 수정 시 중요함
    complete_condition3 = not json_completion['reservation_complete'] and (json_completion['reservation_not_completed_reason'] == 'null') # 예약수정 의사만 밝힌 경우
    
    if complete_condition1 or complete_condition3:
        full_response = response
    elif 'null' not in st.session_state.json_string and (
        complete_condition2 or complete_initial
        ): ##
        st.session_state.correction_session = True
        json_obj_print = tzzim.to_json(st.session_state.json_string)
        with st.chat_message('assistant'):
            full_response = list()
            for k, v in json_obj_print.items():
                if k == 'task':
                    full_response.append(f"{json_obj_print[k]}확인 도와드리겠습니다.")
                else:
                    full_response.append(f"{tzzim.json_keyname[k]}: {v}")
            full_response.append("이대로 예약을 진행할까요? 혹시 잘못된 정보가 있다면 말씀해주세요.")
            full_response = '  \n'.join(full_response)
            st.write(full_response)
        st.session_state.json_check["correction"] = False # 예약 수정 시 중요함
    else:
        with st.chat_message("assistant"):
            placeholder = st.empty() # AI 답변받을 때까지 보관
            full_response = ''
            for item in response:
                full_response += item
            placeholder.markdown(full_response) # AI 답변 바로표기
            
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
    question = full_response ##
    st.session_state.dialogue.append(f"{question}\n") ##

# # 안드로이드 함수 실행
# callAndroidMethod()