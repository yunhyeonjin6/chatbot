import copy
from datetime import datetime
import openai
import re
import streamlit as st

class Tzzim:
    
    def __init__(self):
        openai.api_key = "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" # openai의 api-key (구글 dahae@ellexi.com 계정) 
        self.initial_question = "안녕하세요! 골프예약인공지능 티찜AI입니다. 무엇을 도와드릴까요?"
        self.template = lambda dialogue, instruction: f""" 다음 입력은 손님이 골프장을 예약하기 위해 당신에게 건넨 대화입니다.\n\n{dialogue}\n\n{instruction}"""
        self.task_type = ['예약', '예약취소', '골프정보']
        self.json_obj:dict = {"task": "null", "date": "null", "place": "null", "tee_time_for_reservation": "null"}
        self.json_keyname:list = {'task': '요청사항', 'date': '날짜', 'place': '골프장', 'tee_time_for_reservation': '예약시간'}

        # 검증목록
        self.json_verification:dict = {"json_all_correct": "null", "json_key_not_correct": "null"}
        self.json_completion:dict = {"reservation_complete": "null", "reservation_not_completed_reason": "null"}
        self.json_check_init = {
            'completion': str(self.json_completion),
            'verification': self.json_verification, # rule로 처리하여 str() 불필요
            'correction': False
        }
        self.key_condition_list = {
            'task': [f"{', '.join(self.task_type)} 중 하나여야 합니다."],
            'date': ['현재 티찜AI는 하나의 날짜만 입력받을 수 있습니다.',
                     '티찜AI가 날짜를 계속 물어볼 경우 "날짜", "예약" 등의 단어를 포함한 문장으로 답변해주세요.'],
            'place': ['현재 티찜AI는 장소 선택지를 제공하지 않아 장소를 자유롭게 답변 가능합니다.'],
            'tee_time_for_reservation': ['현재 티찜AI는 하나의 시간만 입력받을 수 있습니다.',
                                         '티찜AI가 예약시간을 계속 물어볼 경우 "예약시간"을 포함한 문장으로 답변해주세요.']
        }
        condition_list_format = lambda a_list: '  \n\t- '.join(a_list) # 조건 형식화
        self.key_condition_list = {k : '  \n\t- ' + condition_list_format(v) for k, v in self.key_condition_list.items()}

    def chatgpt_return(self, user_prompt:str, system_prompt:str="당신은 골프장의 예약을 담당하는 직원입니다.") -> str:
        # ChatGPT 사용
        messages = [
            {"role": "user", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0 # top_p는 같이 쓰라고 권장되지 않음
            # user=a_dict['service_uuid'] # end-user-id
        )

        result = repr(completion.choices[0].message['content']) # ChatGPT 사용결과    

        return result

    def to_json(self, json_string:str)->dict:
        step = re.sub(r"[^\w\s\d\:\,]|[\n]", '', json_string)
        json_obj = dict()
        for key_value in step.split(','):
            temp = key_value.split(':')
            key, value = temp[0].strip(), temp[-1].strip()
            
            if key in ['json_all_correct', 'reservation_complete']:
                if value == 'False':
                    json_obj[key] = False
                elif value == 'True':
                    json_obj[key] = True
                else:
                    json_obj[key] = value 
            else:
                json_obj[key] = value
        return json_obj
    
    def update_json_completion(self, dialogue:str) -> str:
        # self.json_completion:dict = {"reservation_complete": "null", "reservation_not_completed_reason": "null"}

        """
        json의 예약정보 입력완료에 따른 사용자의 긍정/부정 답변을 확인하는 함수 
        """
        instruction = f"""위와 같은 대화가 주어졌을 때 확인 JSON 데이터를 생성해주세요. 출력값만 생성해주세요.
                        확인 JSON 데이터: {st.session_state.json_check['completion']}
                        
                        조건1: JSON의 value값이 'null'이 아니라면 key값과 value값은 고정입니다.
                        조건2: JSON의 새로운 key값과 value값은 추가하지 않습니다.
                        조건3: 추가된 대화에 key값에 해당하는 내용이 없다면 "null"으로 유지해주세요.
                        조건4: 추가된 대화가 예약을 확인하는 내용이고 손님의 대답이 긍정이면 "reservation_complete"키에 "True"를, 손님의 대답이 부정이면 "reservation_complete"키에 "False"를 생성해주세요.
                        조건5: 추가된 대화가 예약을 확인하는 내용이고 손님의 대답이 부정일 때 부정인 이유와 관련된 단어를 {', '.join(list(self.json_obj.keys()))} 중에서 하나를 선택해 'reservation_not_completed_reason'키의 value 값에 생성해주세요.

                        출력:\n"""
        
        user_prompt = self.template(dialogue, instruction)
        st.session_state.json_check['completion'] = self.chatgpt_return(user_prompt)
    
    def update_json_verification(self, dialogue:str) -> str:
        # self.json_verification:dict = {"json_all_correct": "null", "json_key_not_correct": "null"}
        # self.json_obj:dict = {"task": "null", "date": "null", "place": "null", "tee_time_for_reservation": "null"}

        """
        json의 예약정보 잘못되었는 지 확인하는 함수 
        """
        json_obj = self.to_json(st.session_state.json_string)
        local_json_verification = copy.deepcopy(self.json_verification)
        has_value_not_correct = False
        
        for k, v in json_obj.items():
            if v != 'null':
                if k == 'task':
                    if v not in self.task_type:
                        has_value_not_correct = True
                        break
                    else:
                        pass
                elif k in ['date', 'tee_time_for_reservation']:
                    if k == 'date':
                        regex = r'\d{4}년\d{2}월\d{2}일'
                    else:
                        regex = r'\d{2}시\d{2}분'
                    value_without_space = re.sub(r'\s+', '', v)
                    date_find_result = re.findall(regex, value_without_space)
                    if isinstance(date_find_result, list) and (len(date_find_result) == 1):
                        rest_of_date = value_without_space.replace(date_find_result[0], '')
                        if rest_of_date:
                            has_value_not_correct = True
                            break
                        else:
                            pass
                    else:
                        has_value_not_correct = True
                        break                        
            else:
                pass
        
        if has_value_not_correct:        
            local_json_verification["json_all_correct"] = False
            local_json_verification["json_key_not_correct"] = k
        else:
            local_json_verification["json_all_correct"] = True
        
        st.session_state.json_check["verification"] = local_json_verification

    def update_json_string(self, dialogue:str) -> str:
        """
        대화문이 주어졌을 때 json의 예약정보를 추가/수정하는 함수 
        """
        instruction = """위와 같은 대화가 주어졌을 때 추가된 대화를 사용하여 아래의 JSON 데이터를 업데이트 해주세요. 출력값만 생성해주세요.
                JSON 데이터: {}
                조건1: 추가된 대화에 key값에 해당하는 내용이 없다면 'null'으로 유지해주세요.
                조건2: 'task'키의 경우 {} 중 하나만 선택하여 value 값으로 생성해주세요.
                조건3: 'date'키의 경우 오늘 날짜인 {}에 가까운 날짜로 "yyyy년 mm월 dd일" 형식을 사용하여 value 값으로 생성해주세요.
                조건3: 'date'키의 경우 '중순'같이 한 날짜로 특정할 수 없는 표현이 있는 경우 이를 포함하여 value 값으로 생성해주세요.
                조건4: JSON의 value값이 'null'이 아니라면 key값과 value값은 고정입니다.
                조건5: JSON의 새로운 key값과 value값은 추가하지 않습니다.
                조건6: 키에 'time'이 포함되어 있다면 24시간 표기와 "%H시 %M분"형식을 사용하여 value 값으로 생성해주세요.
                출력:\n""".format(st.session_state.json_string, ', '.join(self.task_type), datetime.now().strftime('%Y-%m-%d'))
        
        user_prompt = self.template(dialogue, instruction)
        st.session_state.json_string = self.chatgpt_return(user_prompt)

    def question_from_null(self, dialogue:str) -> str:
        """
        대화문과 session_state.json_string을 이용해서 json의 value값이 null인 예약정보에 대한 질문을 출력으로하는 함수
        """          
        instruction = 'JSON 데이터: ' + st.session_state.json_string + "\n\n" +\
                    """위에 나온 대화와 JSON 형식을 이용하여 손님의 골프장 예약을 위한 질문을 하려고 합니다.
                        출력으로 나온 JSON  데이터에서 'null'값을 가지는 key를 1개를 사용하여 손님에게 골프장 예약을 위해 구체적으로 질문을 해보세요.
                        조건1: JSON 데이터의 key값 순서대로 생성해주세요.
                        
                        출력:\n"""
                        
        user_prompt = self.template(dialogue, instruction)
        raw_question_from_null = self.chatgpt_return(user_prompt)
        return re.sub(r"[^\w\s\d\?\.\!]", '', raw_question_from_null)

    def clear_chat_history(self):
        st.session_state.messages = [{"role": "assistant", "content": self.initial_question}]
        st.session_state.dialogue = [f"{self.initial_question}\n"]
        st.session_state.stop_input = False
        st.session_state.correction_session = False
        st.session_state.json_string = str(self.json_obj)
        st.session_state.json_check = self.json_check_init