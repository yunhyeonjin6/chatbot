import copy
from datetime import datetime, timedelta, time
from gtts import gTTS
import base64
import openai
import pandas as pd
import random
import re
import streamlit as st

from api import TzzimAPI
ta = TzzimAPI()

# 데이터
club_info_list = ta.get_clubInfoList()
# self.data_search = ta.get_dateSearch()
num_call_timeSearch = 0

class Tzzim():
    def __init__(self):
        openai.api_key = "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" # openai의 api-key (구글 dahae@ellexi.com 계정) 

        self.clubinfo_column_mapping = {
            'location': 'location',
            'golf_club_name': 'name',
            'course': 'course'
        }
        
        
        self.timesearch_column_mapping = {
            'golf_club_name': 'GC_name',
            'location': 'location',
            'date': 'day',
            'course': 'course',
            'tee_time_for_reservation': 'frame_list' 
        }
        
        self.column_names = {
            'GC_name': '골프장명',
            'location': '지역',
            'day': '날짜',
            'course': '코스',
            'frame_list': '시간 목록'
        }
        
        # 구분자
        self.range_delimeter = '~'
        self.comma_delimeter = ','
        self.answer_delimeter = ':'
        self.or_delimeter = '|'
        
        # 1. 답변 관련
        self.initial_question = "안녕하세요! 골프예약인공지능 티찜AI입니다. 무엇을 도와드릴까요?"
        
        self.template = lambda dialogue, instruction: f""" 다음 입력은 손님이 골프장을 예약하기 위해 당신에게 건넨 대화입니다.\n\n{dialogue}\n\n{instruction}"""
        
        self.task_type = ['골프장 예약', '예약'] # task_type을 '예약'1개만 주면 오류가 남
        
        self.json_obj:dict = {"task": "null",
                              "date": "null",
                              "location": "null",
                              "golf_club_name": "null",
                              "course": "null",
                              "tee_time_for_reservation": "null"}
        
        self.json_condition:dict = {"location": "all",
                                    "golf_club_name": "all",
                                    "course": "all",
                                    "start_date": "all",
                                    "end_date": "all",
                                    "start_time": "all",
                                    "end_time": "all"
                                    }
        
        self.json_keyname:list = {'task': '요청사항',
                                  'date': '날짜',
                                  'location': '지역',
                                  'golf_club_name': '골프장',
                                  'course': '코스',
                                  'tee_time_for_reservation': '시간'
                                  }
        
        self.keys_need_classification = ['location', 'golf_club_name', 'course']
        
        self.question_order:list = ['task', 'date', 'location', 'golf_club_name', 'course', 'tee_time_for_reservation']

        self.ner_conditions = {'basic': ['추가된 대화에 key값에 해당하는 내용이 없다면 "null"으로 유지해주세요.',
                                    'JSON의 value값이 "null"이 아니라면 key값과 value값은 고정입니다.',
                                    'JSON에 새로운 key값과 value값은 추가하지 않습니다.',
                                    '특정 key값에 대해 질문했을 때 "상관없다" 등의 답변이 있다면 해당 key에는 "all"을 생성해주세요.'],
                        'classification': ['여러 선택지를 선택한다면 "A|B|C"의 형식으로 value값을 생성해주세요.'],
                            'task': [f'"task"키의 경우 {", ".join(["예약", "예약취소", "골프정보"])} 중 하나만 선택하여 value 값으로 생성해주세요.'],
                            'location': ['전라도는 호남권에 속하고, 경상도는 영남권에 속합니다.'],
                            'course': ['코스 선택지에는 영어단어를 한국어로 읽은 표현이 있습니다. 이를 고려하여 영어표현, 한글표현을 모두 생성해주세요.'],
                            'date': [f'"date"키의 경우 오늘 날짜인 {datetime.now().strftime("%Y-%m-%d")}에 가까운 날짜로 "yyyy년 mm월 dd일" 형식을 사용하여 value 값으로 생성해주세요.',
                                    '"date"키의 경우 날짜에 대한 범위를 나타내는 말이 있을 때 "yyyy년 mm월 dd일~yyyy년 mm월 dd일"의 형식으로 값을 생성해주세요.',
                                    '"date"키의 경우 "초", "초순"등의 표현이 있다면 "yyyy년 mm월 01일~yyyy년 mm월 10일", "중순"이면 "yyyy년 mm월 11일~yyyy년 mm월 20일", "말"이면 "yyyy년 mm월 21일~yyyy년 mm월 30일"의 형식으로 값을 생성해주세요. "말"의 경우, 월에 따라 마지막 날짜가 변동될 수 있습니다.'],
                            'tee_time_for_reservation': ['"tee_time_for_reservation"키의 경우 24시간 표기와 "%H시 %M분"형식을 사용하여 value 값으로 생성해주세요.',
                                                        '"tee_time_for_reservation"키의 경우 시간의 범위를 나타내는 말이 있을 때 "%H시 %M분~%H시 %M분"의 형식으로 값을 생성해주세요.',
                                                        '"tee_time_for_reservation"키의 경우 "%H시 %M분 이후로"등의 표현이 있다면 "%H시 %M분~23시 59분"의 형식으로, "%H시 이전으로"등의 표현이 있다면 "00시 00분~%H시 %M분"의 형식으로 값을 생성해주세요.']
                            }
        
        self.num_time_candidate = 3
        
    
        # 2. 검증 관련
        self.json_verification:dict = {"json_all_correct": "null", "json_key_not_correct": "null", "json_value_not_correct": "null"}
        
        self.json_completion:dict = {"reservation_complete": "null", "reservation_not_completed_reason": "null"}
        
        self.json_check_init = {
            'completion': str(self.json_completion),
            'verification': self.json_verification, # rule로 처리하여 str() 불필요
            'correction': False
        }

        self.condition_list_format = lambda a_list: '  \n\t- '.join(a_list) # 조건 형식화
        
        self.ask_again_condition = lambda k, v: (k != 'task') and ((self.comma_delimeter in v) or (self.range_delimeter in v) or (self.or_delimeter in v))
        
        # 2-1. 날짜 전처리 함수
        self.remove_space = lambda value: re.sub(r'\s+', '', value)
        self.rest_of_date = lambda value_without_space, date_text: value_without_space.replace(date_text, '')
        
        # 3. 첫 예약질문 시 예시
        initial_golf_list = lambda key_name: list(set([a_dict[key_name].lower() for a_dict in club_info_list]))
        initial_course_list = list(set([a_course.lower() for a_dict in club_info_list for a_course in a_dict['course']]))
        initial_reservation_list = [f'예를 들어, "{datetime.now().strftime("%m월 %d일")}에 {initial_golf_list("name")[random.randint(0,len(initial_golf_list("name"))-1)]} 골프장에서 {datetime.now().hour}시 쯤 예약하고 싶어" 라고 하실 수 있습니다.',
                                    f'지역은 {(self.comma_delimeter+" ").join(initial_golf_list("location"))} 중에서 선택하시면 됩니다.',
                                    f'골프장은 {(self.comma_delimeter+" ").join(initial_golf_list("name"))} 중에서 선택하실 수 있습니다.',
                                    f'코스는 {(self.comma_delimeter+" ").join(initial_course_list)} 등이 있습니다.']
        self.initial_reservation_example = '  \n\t- ' + self.condition_list_format(initial_reservation_list)
        
        
        # session state용 초기값
        self.session_init = {
                'login': {'first_question':False, 'ask_gc':False, 'yes_no': "null"},
                'messages': [{"role": "assistant", "content": self.initial_question}],
                'dialogue': [f"{self.initial_question}\n"],
                'stop_input': False,
                'correction_session': False,
                'json_string': str(self.json_obj),
                'json_check': self.json_check_init,
                'json_condition': self.json_condition,
                'data': list(),
                'visual_info': list(),
                'finished_time_selection': False
            }
        
        # 초기화
        for session_state_key, init_val in self.session_init.items():
            if session_state_key not in st.session_state.keys():
                st.session_state[session_state_key] = init_val
        
        self.key_condition_list = {
            'task': f"현재 티찜AI는 골프장 예약작업만 지원하고 있습니다.",
            'date': '날짜를 계속 물어볼 경우 "월", "일", "날짜", "예약" 등의 단어를 포함한 문장으로 답변해주세요.',
            'location': lambda list_of_choices: f'지역은 {(self.comma_delimeter + " ").join(list_of_choices)}중에서 선택하실 수 있습니다.',
            'golf_club_name': lambda list_of_choices: f'골프장은 {(self.comma_delimeter + " ").join(list_of_choices)} 중에서 선택하실 수 있습니다.',
            'course': lambda list_of_choices: f'선택가능 한 코스는 {(self.comma_delimeter + " ").join(list_of_choices)}입니다.',
            'tee_time_for_reservation': '예약시간을 계속 물어볼 경우 "예약시간"을 포함한 문장으로 답변해주세요.'
        }

        self.choices_list = list()

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
        )

        result = repr(completion.choices[0].message['content']) # ChatGPT 사용결과    

        return result

    def to_json(self, json_string:str)->dict:
        step = re.sub(r"[^\w\s\d\:\,\~\|]|[\n]", '', json_string)
        json_obj = dict()
        for key_value in step.split(self.comma_delimeter):
            temp = key_value.split(self.answer_delimeter)
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
    
    def yes_no(self, dialogue:str) -> str:
        """
        json의 예약정보 입력완료에 따른 사용자의 긍정/부정 답변을 확인하는 함수 
        """
        instruction = f"""위의 대화 중 추가된 대화가 승락의 표현이면 True, 거절의 표현이면 False를 생성해주세요. 출력값만 생성해주세요.
                        출력:\n"""
        
        user_prompt = self.template(dialogue, instruction)
        bool_string = self.chatgpt_return(user_prompt) # 'True'/'False' 따옴표 기호 포함해서 출력됨    
        if  "True" in bool_string:
            bool_data = True
        elif "False" in bool_string:
            bool_data = False
        else:
            bool_data = "null"
        st.session_state.login['yes_no'] = bool_data
    
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
    
    def update_json_verification(self, json_string:str) -> str:
        # self.json_verification:dict = {"json_all_correct": "null", "json_key_not_correct": "null"}
        # self.json_obj:dict = {"task": "null", "date": "null", "golf_club_name": "null", "tee_time_for_reservation": "null"}

        """
        json의 예약정보 잘못되었는 지 확인하는 함수 
        """
        json_obj = self.to_json(json_string)
        # print('json_obj_before_verification: ', json_obj)
        local_json_verification = copy.deepcopy(self.json_verification)
        has_value_not_correct = False
        
        for k, v in json_obj.items():
            if v != 'null':
                if k == 'task':
                    if v not in self.task_type:
                        has_value_not_correct = True
                        break # 윗줄과 항상 같이 있어야 함
                    else:
                        pass
                elif k in ['date', 'tee_time_for_reservation']: # "yyyy년 mm월 dd일 ~ yyyy년 mm월 dd일" 처리하기
                    if k == 'date':
                        # print('date:', v)
                        regex = r'\d{4}년\d{2}월\d{2}일'
                    else:
                        regex = r'\d{2}시\d{2}분'
                    find_date_time:list = re.findall(regex, self.remove_space(v))
                    # print('find_date_time: ', find_date_time)
                    has_rest = False
                    has_value_not_correct = False
                    # 날짜 이외의 문자열이 있는 경우 수정필요
                    if isinstance(find_date_time, list) and (len(find_date_time) == 1):
                        date_text = find_date_time[0]
                        has_rest = self.rest_of_date(self.remove_space(v), date_text)
                        if has_rest:
                            has_value_not_correct = True 
                            break # 윗줄과 항상 같이 있어야 함
                        else:
                            pass
                    elif isinstance(find_date_time, list) and (len(find_date_time) == 2):
                        for value, date_text in zip(v.split(self.range_delimeter), find_date_time):
                            has_rest = self.rest_of_date(self.remove_space(value), date_text)
                            if has_rest:
                                has_value_not_correct = True
                                break # 윗줄과 항상 같이 있어야 함
                    else:
                        has_value_not_correct = True
                        break # 윗줄과 항상 같이 있어야 함
                    
                elif k in ['location', 'golf_club_name', 'course']:
                    if self.or_delimeter in v:
                        iter_values = v.split(self.or_delimeter)
                    else:
                        iter_values = [v]
                    list_of_choices = self.initial_data_choices(k)
                    # print('list_of_choices: ', list_of_choices)
                    for a_value in iter_values:
                        
                        
                        if a_value not in list_of_choices:
                            has_value_not_correct = True
                            break # 윗줄과 항상 같이 있어야 함
            else:
                pass
        
        if has_value_not_correct:        
            local_json_verification["json_all_correct"] = False
            local_json_verification["json_key_not_correct"] = k
        else:
            local_json_verification["json_all_correct"] = True
        
        st.session_state.json_check["verification"] = local_json_verification

    def update_json_condition(self):
        temp_json_obj = self.to_json(st.session_state.json_string)
        for k, v in temp_json_obj.items():
            
            # 날짜 및 시간의 범위에 대한 처리
            if k == 'date':
                if self.range_delimeter in v:
                    start_date, end_date = v.split(self.range_delimeter)
                elif v == 'null':
                    start_date = 'all'
                    end_date = 'all'
                else:
                    start_date = v
                    end_date = None
                st.session_state['json_condition']['start_date'] = start_date
                st.session_state['json_condition']['end_date'] = end_date
                
            elif k == 'tee_time_for_reservation':
                if self.range_delimeter in v:
                    start_time, end_time = v.split(self.range_delimeter)
                elif v == 'null':
                    start_time = 'all'
                    end_time = 'all'
                else:
                    start_time = v
                    end_time = None
                st.session_state['json_condition']['start_time'] = start_time
                st.session_state['json_condition']['end_time'] = end_time
                
            elif k == 'task':
                continue
            else:
                if v == 'null':
                    v = 'all'
                st.session_state['json_condition'][k] = v

    def key_extraction(self, dialogue:str) -> list:
        keys = list()
        key_instruction = f"""위와 같은 대화가 주어졌을 때 추가된 대화의 사용자 답변을 사용하여 아래 선택지에서 수정이 필요한 값을 선택해주세요. 출력값만 생성해주세요.
                선택지: {','.join(list(self.json_obj.keys()))}
                
                조건1: 출력은 파이썬 리스트 형식으로 출력해주세요.
                조건2: 수정이 필요없다면 'null'을 생성해주세요.
                조건3: {','.join(list(set([a_dict['location'] for a_dict in club_info_list])))}이 있다면 'location'를 선택해주세요.
                조건4: {','.join(list(set([a_dict['name'] for a_dict in club_info_list])))}이 있다면 'golf_club_name'을 선택해주세요.
                조건5: {','.join(list(set([a_course for a_dict in club_info_list for a_course in a_dict['course']])))} 이 있다면 'course'를 선택해주세요.
                조건6: 대화 초반에는 'task' key만 생성해주세요.
                
                출력:\n"""
        # ChatGPT결과가 따옴표까지 생성하는 것 조심해야함
        # print('key_instruction: ', key_instruction)
        user_prompt = self.template(dialogue, key_instruction)
        raw_keys = self.chatgpt_return(user_prompt)
        # print('raw_keys:', raw_keys)
        keys = re.sub(r"[^\w\s\d\,]", '', raw_keys)
        if 'null' in keys:
            pass
        else:
            if not keys:
                pass
            else:
                if self.comma_delimeter in keys:
                    keys = keys.split(self.comma_delimeter)
                    keys = [a_key.strip() for a_key in keys]
                else:
                    keys = [keys]

        return keys
    
    def key_generation(self, dialogue:str, keys_to_generate:list) -> dict:
        prompt_condition_list = copy.deepcopy(self.ner_conditions['basic'])
        for a_key in keys_to_generate:
            if a_key in self.ner_conditions:
                prompt_condition_list += self.ner_conditions[a_key]
        prompt_conditions = '\n\t' + '\n\t'.join(prompt_condition_list)
        temp_dict = {k:v for k, v in self.json_obj.items() if k in keys_to_generate}
        ner_instruction = '\n\n'.join([f"위와 같은 대화가 주어졌을 때 추가된 대화를 사용하여 아래의 JSON 데이터의 {','.join(keys_to_generate)} key에 해당하는 value값을 업데이트 해주세요. 출력값만 생성해주세요." +\
                                        f"JSON 데이터: {temp_dict}",
                                        prompt_conditions,
                                        "출력:\n"])
        # print('ner_instruction: ', ner_instruction)
        user_prompt = self.template(dialogue, ner_instruction)
        # print('generation_prompt: ', user_prompt)
        json_string_generated = self.chatgpt_return(user_prompt)
        json_generated = self.to_json(json_string_generated)
        
        return json_generated
    
    def key_classification(self, dialogue:str, keys_to_classify:list) -> dict:
        prompt_condition_list = copy.deepcopy(self.ner_conditions['basic'] + self.ner_conditions['classification'])
        classification_choices_list = list()
        # print('cond_basic: ', self.ner_conditions['basic'])
        # print('cond_classify: ', self.ner_conditions['classification'])
        
        for a_key in keys_to_classify:
            if a_key in self.ner_conditions:
                prompt_condition_list += self.ner_conditions[a_key]
                
            if a_key in ['location', 'golf_club_name', 'course']:
                if st.session_state.data:
                    choices_list = self.session_data_choices(a_key)
                else:
                    choices_list = self.initial_data_choices(a_key)
                choice_phrase = f'{self.json_keyname[a_key]} 선택지: {choices_list}'
                classification_choices_list.append(choice_phrase)
            
        choices = '\n\t' + '\n\t'.join(classification_choices_list)
        prompt_conditions = '\n\t' + '\n\t'.join(prompt_condition_list)
        temp_dict = {k:v for k, v in self.json_obj.items() if k in keys_to_classify}
        classify_instruction = '\n\n'.join([f"위와 같은 대화가 주어졌을 때 추가된 대화를 사용하여 다음 선택지 중에서 JSON데이터의 value값을 생성해주세요. JSON데이터를 출력하고 출력값만 생성해주세요." +\
                                        f"JSON 데이터: {temp_dict}",
                                        choices,
                                        prompt_conditions,
                                        "출력:\n"])
        # print('classify_instruction: ', classify_instruction)
        user_prompt = self.template(dialogue, classify_instruction)
        # print('classification_prompt: ', user_prompt)
        json_string_classified = self.chatgpt_return(user_prompt)
        json_classified = self.to_json(json_string_classified)
        
        return json_classified
        
    def update_json_string(self, dialogue:str) -> str:
        """
        대화문이 주어졌을 때 json의 예약정보를 추가/수정하는 함수 
        """
        # print('dialogue: ', dialogue)
        keys = self.key_extraction(dialogue)
        # print('keys: ', keys)
        
        keys_to_generate = list()
        keys_to_classify = list()
        if keys == 'null':
            pass # 수정할 key가 없으면 아무것도 하지 않음
        else:
            for a_key in keys:
                if a_key in ['location', 'golf_club_name', 'course']:
                    keys_to_classify.append(a_key)
                else:
                    keys_to_generate.append(a_key)
                    
            # print('keys_to_generate: ', keys_to_generate)
            # print('keys_to_classify: ', keys_to_classify)
            
            json_generated = dict()
            json_classified = dict()
            if keys_to_generate:
                json_generated = self.key_generation(dialogue, keys_to_generate)
            else:
                pass
            if keys_to_classify:
                json_classified = self.key_classification(dialogue, keys_to_classify)
            else:
                pass

            json_obj_prior = self.to_json(st.session_state.json_string)
            json_changed = copy.deepcopy(json_obj_prior)
            for k, v in json_changed.items():
                if json_generated and k in json_generated:
                    for k, v in json_generated.items():
                        if k in json_changed: # 새로운 키를 추가하지 않기 위함
                            json_changed[k] = v
                
                if json_classified and k in json_classified:
                    for k, v in json_classified.items():
                        if k in json_changed:
                            json_changed[k] = v
                        
            # print('json_generated: ', json_generated)
            # print('json_classified: ', json_classified)
            # print('json_obj_prior: ', json_obj_prior)
            # print('json_changed: ', json_changed)

            st.session_state.json_string = str(json_changed)
            
            # 데이터 필터링을 위한 json_condition 업데이트
            self.update_json_condition()

    def session_data_choices(self, key_name:str):
        if key_name not in ['location', 'golf_club_name', 'course']:
            raise Exception('key_name must be one of location, golf_club_name, course')
        else:
            list_of_choices = list(set([a_dict[self.timesearch_column_mapping[key_name]] for a_dict in st.session_state.data]))
            return list_of_choices
        
    def initial_data_choices(self, key_name:str):
        if key_name not in ['location', 'golf_club_name', 'course']:
            raise Exception('key_name must be one of location, golf_club_name, course')
        else:
            if key_name == 'course':
                list_of_choices = list(set([a_course for a_dict in club_info_list for a_course in a_dict[self.clubinfo_column_mapping[key_name]]]))
            else:
                list_of_choices = list(set([a_dict[self.clubinfo_column_mapping[key_name]] for a_dict in club_info_list]))
            return list_of_choices

    def question_generation(self, keys_to_ask:list=list(), no_search_result=False) -> str:
        """
        대화문과 session_state.json_string을 이용해서 json의 value값이 null인 예약정보에 대한 질문을 출력으로하는 함수
        """        
        json_obj_question = self.to_json(st.session_state.json_string)
        keys_for_question = list()
        
        if keys_to_ask:
            keys_list = keys_to_ask
        else:
            keys_list = self.question_order
            
        for k in keys_list:
            v = json_obj_question[k]
            if (v == 'null') or (k in keys_to_ask): # value값이 'null'이거나 (아직 질문하지 않은 것), 범위표현으로 인해 다시 물어봐야 하거나
                keys_for_question.append(k)
                
                if k in ['location', 'golf_club_name', 'course']:
                    if st.session_state.data:
                        to_join = self.session_data_choices(k)
                    else:
                        to_join = self.initial_data_choices(k)
                    if random.randint(0, 1):
                        choice_phrase = '고르실 수'
                    else:
                        choice_phrase = '선택하실 수'
                    to_append = (f"{self.json_keyname[k]}의 경우 " + f"{(self.comma_delimeter + ' ').join(list(set(to_join)))} 중에서 {choice_phrase} 있습니다.")
                    self.choices_list.append(to_append)
                else:
                    pass                
        
        if keys_to_ask:
            if no_search_result:
                phrase_to_add = ' 등을 다시 설정해주세요.'
            elif keys_to_ask in [['date'], ['date', 'location', 'golf_club_name'], ['location'], ['golf_club_name'], ['location', 'golf_club_name']]:
                phrase_to_add = ' 등을 먼저 설정해주실 수 있나요?'
            else:
                phrase_to_add = '도 특정하실 수 있습니다.'
        else:
            phrase_to_add = ' 등을 선택해주세요.'
        
        if keys_for_question:
            key_name_list = [self.json_keyname[a_key] for a_key in keys_for_question]
            key_name_list[-1] 
            generated_question = (self.comma_delimeter + " ").join(key_name_list) + phrase_to_add
        else:
            generated_question = ''
        
        return generated_question    

    def clear_chat_history(self):
        st.session_state.messages = [{"role": "assistant", "content": self.initial_question}]
        st.session_state.dialogue = [f"{self.initial_question}\n"]
        st.session_state.stop_input = False
        st.session_state.correction_session = False
        st.session_state.json_string = str(self.json_obj)
        st.session_state.json_check = self.json_check_init
    
    def reservation_validation(self, dialogue):
        self.update_json_completion(dialogue) # 확인 업데이트
                
        json_completion_check = self.to_json(st.session_state.json_check['completion'])
        wrong_key = json_completion_check['reservation_not_completed_reason']
        
        if json_completion_check['reservation_complete']: # case1) 예약이 완료된 경우
            st.session_state.stop_input = True
            response = f"{self.to_json(st.session_state.json_string)['task']} 작업이 완료되었습니다. 티찜AI를 이용해주셔서 감사합니다."
            with st.chat_message('assistant'):
                st.write(response)
                self.text_to_audio(response)
            st.button('다시하기', on_click=self.clear_chat_history)
            json_obj_completion = "완료"
        
        elif not json_completion_check['reservation_complete'] and (wrong_key != 'null'): # case2) 예약 항목을 언급한 경우
            a_condition = self.condition_for_key(wrong_key)
            response = f"{self.json_keyname[wrong_key]} 항목을 수정해드리겠습니다. 다시 말씀해주시겠습니까? 다음 조건을 참고하셔서 답변 부탁드립니다.\n" + '  \n\t- '  + a_condition
            
            # 다시 물어본 예약정보 json 키의 value 값을 "null"로 직접 대체
            json_obj_completion = self.to_json(st.session_state.json_string)
            json_obj_completion[wrong_key] = "null"
            st.session_state.json_string = str(json_obj_completion)
            st.session_state.json_check["correction"] = True # 예약수정 시 중요함
            
        elif not json_completion_check['reservation_complete'] and (wrong_key == 'null'): # case3) 예약완료가 안됐다고만 답한 경우
            response = "예약정보의 어떤 항목을 수정하시겠습니까?"
            
            with st.chat_message('assistant'):
                st.write(response)
                self.text_to_audio(response)
        
        else:
            response = f"오류가 발생하였습니다. 개발자에게 이 결과를 캡쳐하여 보내주세요.\njson_completion: {st.session_state.json_check['completion']}\n개발자 이메일: dahae@ellexi.com"
        
        return response

    def time_confirmation(self, exact_time:datetime, filtered_result:list=None, is_filtered_result:bool=False):
        if is_filtered_result:
            last_data = filtered_result
        else:
            last_data = st.session_state.data
        # print(last_data)
            
        if (len(last_data) == 1) and (
            len(last_data[0]['frame_list']) == 1) and (
            last_data[0]['frame_list'][0] == datetime.strftime(exact_time, '%H:%M')
        ):
            st.session_state.finished_time_selection = True
            # print('last_data[0]: ', last_data[0])
            json_for_comfirmation = self.to_json(st.session_state.json_string)
            json_confirmation_changed = copy.deepcopy(json_for_comfirmation)
            for k1, v1 in json_for_comfirmation.items():
                if (v1 == 'null') or (self.or_delimeter in v1):
                    k2 = self.timesearch_column_mapping[k1]
                    v2 = last_data[0][k2]
                    json_confirmation_changed[k1] = v2
                else:
                    pass
            st.session_state.json_string = str(json_confirmation_changed)
        else:
            pass

    def condition_for_key(self, key_name:str):
        if key_name in self.keys_need_classification:
            if st.session_state.data:
                list_of_choices = self.session_data_choices(key_name)
            else:
                list_of_choices = self.initial_data_choices(key_name)
            a_condition = self.key_condition_list[key_name](list_of_choices)
        else:
            a_condition = self.key_condition_list[key_name]
        return a_condition

    def ask_task_gclist(self, dialogue:str):
        if not st.session_state.login['ask_gc'] and (
            self.to_json(st.session_state.json_string)['task'] != "null" # case1) 회원이 골프장 예약을 한다는 것을 알았고, 가입한 골프장 명단을 아직 안내하지 않은 경우 
        ):
            response = f"네, 알겠습니다! 현재  푸른하늘님은 {len(club_info_list)}개 골프장의 회원이십니다. 자동 로그인이 되었습니다. 골프장 명단을 알려드릴까요?"
            st.session_state.login['ask_gc'] = True

        elif st.session_state.login['ask_gc'] and ( # case2) 골프장 안내여부에 대한 답변을 들은 경우
            st.session_state.login['yes_no'] == 'null'
        ):
            self.yes_no(dialogue)
            
            if st.session_state.login['yes_no']: # 골프장 명단을 알려드릴까요? -> 예
                gc_list = [a_dict['name'] + 'CC' for a_dict in club_info_list]
                response = f"회원이신 골프장은 {', '.join(gc_list)} 입니다. 어떻게 예약을 도와드릴까요?"
            
            else: # 골프장 명단을 알려드릴까요? -> 아니오
                response = "네 알겠습니다, 바로 예약 진행하겠습니다. 어떻게 예약을 도와드릴까요?"  
            st.session_state.visual_info = [(self.initial_reservation_example, 'container')]
        else:
            response = None
        
        return response
    
    def location_gc_confirm(self, key_name:str) -> str:
        """
        지역/골프장이 없거나 범위로 지정된 경우 질문을 좁혀서 질문함
        keys_to_filter, self.keys_ask_again 때문에 클래스 메서드로 빼기 어려움
        """
        if key_name not in self.keys_to_filter:                                                    # 지역/골프장이 없을 경우 지역만 묻도록 좁히기 
            response = self.question_generation(keys_to_ask=[key_name])
        elif key_name in self.keys_ask_again:                                                      # 지역/골프장이 여러 개 주어졌을 경우 한 지역으로 좁히기
            temp_choice_list = st.session_state.json_condition[key_name].split(self.or_delimeter)
            response = f'{(self.comma_delimeter + " ").join(temp_choice_list)} 중에서 한 {self.json_keyname[key_name]}을 설정해주세요.'
        
        return response
    
    def narrow_down_question(self, one_date_condition:bool, one_location_condition:bool, one_gc_condition:bool):
        json_obj_ask = self.to_json(st.session_state.json_string)
        # print('question_tighten: ', 'case1')
        if (json_obj_ask['date']=='null') and (json_obj_ask['location']=='null') and (json_obj_ask['golf_club_name']=='null'):            # 모두 확정이 안된경우
            # print('question_tighten: ', 'case1_1')
            response = self.question_generation(keys_to_ask=['date', 'location', 'golf_club_name'])
            
        else:
            # print('question_tighten: ', 'case1_2')
            if not one_date_condition:                                                                      # 날짜가 하나로 확정이 안되었을 때
                # print('question_tighten: ', 'case1_2_1') 
                if 'date' not in self.keys_to_filter:                                                            # 날짜가 없을 경우 날짜 질문만 묻도록 좁히기
                    # print('question_tighten: ', 'case1_2_1_1')
                    response = self.question_generation(keys_to_ask=['date'])
                elif 'date' in self.keys_ask_again:                                                              # 날짜가 범위로 주어졌을 경우 하루로 날짜 좁히기
                    # print('question_tighten: ', 'case1_2_1_2')
                    # print('dialogue: ', dialogue)
                    start_date_datetime = datetime.strptime(st.session_state.json_condition['start_date'],'%Y년 %m월 %d일')
                    start_date_parse = datetime.strftime(start_date_datetime, '%m월 %d일')
                    end_date_datetime = datetime.strptime(st.session_state.json_condition['end_date'],'%Y년 %m월 %d일')
                    end_date_parse = datetime.strftime(end_date_datetime, '%m월 %d일')
                    response = f'{start_date_parse}부터 {end_date_parse}까지 날짜 중에서 하루를 선택해주실 수 있나요?'
                    
            elif (json_obj_ask['location']=='null') and (json_obj_ask['golf_club_name']=='null'):            # 지역과 골프장이 둘 다 확정되지 않은 경우
                # print('question_tighten: ', 'case1_3')
                response = self.question_generation(keys_to_ask=['location', 'golf_club_name'])
                
            elif (not one_location_condition) or (not one_gc_condition):
                if (json_obj_ask['location']!='null'):                                                       # 지역이 여러 개로 주어진 경우
                    # print('question_tighten: ', 'case1_4')
                    response = self.location_gc_confirm('location')
                    
                if (json_obj_ask['golf_club_name']!='null'):                                                 # 골프장이 여러 개로 주어진 경우
                    # print('question_tighten: ', 'case1_5')
                    response = self.location_gc_confirm('golf_club_name')
        
        return response
    
    def search_for_response(self):
        filter = DataFilter()
        json_obj_ask = self.to_json(st.session_state.json_string)
        print('json_condition: ', st.session_state.json_condition)
        self.filtered_result = filter.search_and_filter(st.session_state.json_condition)

        if self.filtered_result: # 검색결과 있음
            
            time_string_value = json_obj_ask['tee_time_for_reservation']
            if (self.range_delimeter not in time_string_value) and (time_string_value != 'null'):                 # 범위 시간이 아닐 때
                exact_time = datetime.strptime(time_string_value, '%H시 %M분') # 하나의 시간이 입력되었을 경우
                
                for a_dict in self.filtered_result:
                    datetime_list = [datetime.strptime(a_frame, '%H:%M') for a_frame in a_dict['frame_list']]
                    if exact_time in datetime_list:                           # 그 시간이 frame_list에 있으면 해당 시간을 반환
                        a_dict['frame_list'] = [datetime.strftime(exact_time, '%H:%M')]
                    else:                                                     # 그 시간이 없으면 가장 가까운 시간 N개를 반환
                        time_delta_list = [abs(a_datetime - exact_time) for a_datetime in datetime_list]
                        sorted_time_delta = sorted(enumerate(time_delta_list), key=lambda x: x[1])
                        if len(sorted_time_delta) < self.num_time_candidate:
                            top_n_delta = sorted_time_delta
                        else:
                            top_n_delta = sorted_time_delta[:self.num_time_candidate]
                        a_dict['frame_list'] = [datetime.strftime(datetime_list[idx], '%H:%M') for idx, _ in top_n_delta]
            else:
                exact_time = None
            
            st.session_state.data = self.filtered_result # 필터링된 데이터 저장
            if exact_time: # 현재 내보낼 선택지가 1개 있고 그 시간이 정확한 시간이었다면 예약확인
                self.time_confirmation(exact_time, filtered_result=self.filtered_result, is_filtered_result=True)
                                
            if st.session_state.finished_time_selection:
                response = ''
            else:
                response = '검색을 완료하였습니다. '
                response += self.question_generation() # 더 질문해야할 것들 추가

                if self.keys_ask_again:
                    response += (" " + self.question_generation(self.keys_ask_again))
                
                self.filtered_df = pd.DataFrame(self.filtered_result)
            
        else: # 검색결과 없는 경우
            response = '검색결과가 없습니다. '
            response += self.question_generation(keys_to_ask=self.keys_to_filter, no_search_result=True) # 검색결과가 없는 경우 방금 받은 조건으로 재질문

        return response

    def response_generation(self, dialogue):
        self.update_json_string(dialogue) # 예약정보 업데이트
        self.update_json_verification(st.session_state.json_string) # 검증 업데이트
        
        # print(st.session_state.json_check['verification'])
        
        if st.session_state.json_check['verification']['json_all_correct']: # NER값들이 전부 맞았을 때
            # print('response_gen: case1')
                            
            response = self.ask_task_gclist(dialogue) # case 1, 2) 첫 안내 및 골프장 명단 안내 
                
            if response:
                pass
            else:                                       # case3) 예약정보 받기
                # null이 아닌 데이터를 불러와서 필터링 하기
                self.keys_to_filter = [k for k, v in self.to_json(st.session_state.json_string).items() if k != "task" and v != 'null'] 
                
                # 범위 표현에 대한 질문추가
                json_obj_ask = self.to_json(st.session_state.json_string)
                self.keys_ask_again = [k for k, v in json_obj_ask.items() if self.ask_again_condition(k,v)]
                
                # case 3_1,2) 질문범위 축소
                one_date_condition = (json_obj_ask['date']!='null') and (self.range_delimeter not in json_obj_ask['date'])
                one_location_condition = (json_obj_ask['location']!='null') and (self.or_delimeter not in json_obj_ask['location'])
                one_gc_condition = (json_obj_ask['golf_club_name']!='null') and (self.or_delimeter not in json_obj_ask['golf_club_name'])
                
                self.filtered_result = list() # 선택지 출력을 위한 초기화
                # print('keys_to_filter: ', self.keys_to_filter)
                # print('three_conditions: ', one_date_condition, one_location_condition, one_gc_condition)
                # case 3_1) 사용자가 예약 항목에 대한 말을 했거나 / 데이터를 불러올 조건, 날짜 하루 지정 and (지역 1곳 지정 or 골프장 1곳 지정),을 만족하지 못한 경우
                if (len(self.keys_to_filter) > 0) or (not(one_date_condition and (one_location_condition or one_gc_condition))):
                    
                    # case 3_1_1) 데이터를 불러올 조건을 만족하지 못한 경우
                    if not(one_date_condition and (one_location_condition or one_gc_condition)): 
                        # # print('question_tighten: ', 'case1')
                        response = self.narrow_down_question(one_date_condition, one_location_condition, one_gc_condition)
                    
                    # case 3_1_2) 데이터를 불러올 조건을 만족하여 데이터를 불러오는 경우
                    else: 
                        # 골프장이 하나로 확정된 경우 지역을 자동으로 채우기
                        if (json_obj_ask['golf_club_name'] != 'null') and ('golf_club_name' not in self.keys_ask_again): 
                            # print(st.session_state.json_string)
                            location_of_club = [a_dict['location'] for a_dict in club_info_list if a_dict['name'] == json_obj_ask['golf_club_name']][0]
                            json_obj_ask['location'] = location_of_club
                            st.session_state.json_string = str(json_obj_ask)
                            self.update_json_condition()
                        else:
                            pass
                        
                        # 
                        time_string_value = json_obj_ask['tee_time_for_reservation']
                        if (self.range_delimeter not in time_string_value) and (time_string_value != 'null'): # 범위 시간이 아닐 때
                            exact_time = datetime.strptime(time_string_value, '%H시 %M분') # 하나의 시간이 입력되었을 경우
                            # print('time_confirmation_1')
                            self.time_confirmation(exact_time) # 이전에 받은 선택지가 1개였고 그 시간이 정확한 시간이었다면 예약확인
                        
                        if st.session_state.finished_time_selection:
                            response = ''
                        else:
                            # 데이터 필터링
                            response = self.search_for_response()
                
                # case 3_2) 사용자가 예약항목에 대해 말을 안한 경우          
                else: 
                    response = self.question_generation()
                    if self.keys_ask_again: # 범위표현이 있는 경우 특정해달라고 하기
                        response += (" " + self.question_generation(self.keys_ask_again))
                        
                # 시각자료 추가
                # print(self.choices_list)
                if st.session_state.finished_time_selection: # 예약확인 단계로 바로 넘어가기
                    response = ''
                else:
                    if self.choices_list:
                        st.session_state.visual_info.append(('  \n\t- ' + self.condition_list_format(self.choices_list), 'container'))
                    else: 
                        pass
                    
                    if self.filtered_result:
                        st.session_state.visual_info.append((pd.DataFrame(self.filtered_df), 'dataframe'))
                    
        elif st.session_state.json_check["correction"]: # case4) 예약확인 단계에서 수정의사를 밝혔을 경우 response 없음
            # print('response_gen: case2')
            response = ''
        else:                                           # case5) 생성한 내용이 검증기준을 통과하지 못한경우
            # print('response_gen: case3')
            json_obj_check = self.to_json(st.session_state.json_string)
            
            # 검증기준에 통과하지 못한 key, value를 저장
            wrong_key = st.session_state.json_check['verification']['json_key_not_correct']
            wrong_value = json_obj_check[wrong_key]
            st.session_state.json_check['verification']['json_value_not_correct'] = wrong_value
            
            if json_obj_check[wrong_key] == 'null': # verification의 내용이 'null'만 있어도 잘못되었다고 판단하기 때문에 기준을 넣음
                response = self.question_generation()
            else:
                to_append = self.condition_for_key(wrong_key)
                response = f"{self.json_keyname[wrong_key]}에 대해 다시 여쭤봐도 되겠습니까? 다음 조건을 참고하셔서 답변 부탁드립니다.\n" +\
                            '  \n\t- '  + to_append +\
                            '  \n\t- '  + f'티찜 AI는 {self.json_keyname[wrong_key]}에 대해 "{wrong_value}"로 이해하였습니다.'
                
                # 다시 물어본 예약정보 json 키의 value 값을 "null"로 직접 대체
                json_obj_check[wrong_key] = "null"
                st.session_state.json_string = str(json_obj_check)

        return response

    def complete_or_ongoing(self, response, dialogue):
        json_completion = self.to_json(st.session_state.json_check['completion'])
        complete_initial = (json_completion['reservation_complete'] == 'null') and (json_completion['reservation_not_completed_reason'] == 'null') # 예약확인을 하지 않은 상태
        complete_condition1 = json_completion['reservation_complete'] and (json_completion['reservation_complete'] != 'null')                      # 예약 완료
        complete_condition2 = st.session_state.json_check["correction"]                                                                            # 예약수정 의사와 수정된 답변 모두 받음, 예약 수정 시 중요함
        complete_condition3 = not json_completion['reservation_complete'] and (json_completion['reservation_not_completed_reason'] == 'null')      # 예약수정 의사만 밝힌 경우
        json_obj_ask = self.to_json(st.session_state.json_string)# 범위 표현 제외
        
        case1_condition = complete_condition1 or complete_condition3
        case2_condition = ('null' not in st.session_state.json_string) and (st.session_state.finished_time_selection) and (complete_condition2 or complete_initial)
        # print('case2_part1: ', ('null' not in st.session_state.json_string))
        # print('case2_part2: ', st.session_state.finished_time_selection)
        # print('case2_part3_1:', complete_condition2)
        # print('case2_part3_2:', complete_initial)
        
        if case1_condition:                                 # case1) 예약을 완료했거나 예약 수정 의사(수정 O/X)만 밝힌 경우
            # print('complete: case1')
            full_response = response
            
        elif case2_condition:                               # case2) 예약확인 단계 (예약정보를 모두 받았고 예약확인을 한번도 하지 않았거나/수정된 답변을 모두 받음), 범위표현 제외
            # print('complete: case2')
            # self.update_json_string(dialogue)
            # self.update_json_verification(st.session_state.json_string)
            st.session_state.correction_session = True
            
            # 현재까지 예약내역 표시
            json_obj_print = self.to_json(st.session_state.json_string)
            # print('json_obj_print: ', json_obj_print)
            with st.chat_message('assistant'):
                full_response = list()
                for k, v in json_obj_print.items():
                    if k == 'task':
                        full_response.append(f"{json_obj_print[k]}확인 도와드리겠습니다.")
                    elif k == 'location':
                        continue
                    else:
                        full_response.append(f"{self.json_keyname[k]}: {v}")
                full_response.append("이대로 예약을 진행할까요? 혹시 잘못된 정보가 있다면 말씀해주세요.")
                full_response = '  \n'.join(full_response)
                st.write(full_response)
                self.text_to_audio(full_response)
            st.session_state.json_check["correction"] = False # 예약 수정 시 중요함
                
        else:                                                 # case3) 예약 중간수정 및 그 외 모든 경우 (예약 중간수정이 위 case에 안걸리는 이유: 1. st.session_state.json_check["correction"]=True, 2. "null" in 'null' not in st.session_state.json_string )
            # print('complete: case3')
            with st.chat_message("assistant"):
                placeholder = st.empty() # AI 답변받을 때까지 보관
                full_response = ''
                for item in response:
                    full_response += item
                placeholder.markdown(full_response) # AI 답변 바로표기
                self.text_to_audio(full_response)

            if st.session_state.visual_info:
                # contents_for_fullresponse = list()
                for content, type in st.session_state.visual_info:
                    if type == 'container':
                        visual_container = st.container()
                        visual_container.write(content) # content:str
                        
                        # # 선택지 정보를 dialogue에 추가하기 위한 작업(1)
                        # a_content_for_fullresponse = copy.deepcopy(content)
                        # contents_for_fullresponse.append(a_content_for_fullresponse)
                        
                    elif type == 'dataframe':
                        st.dataframe(content, hide_index=True, column_config=self.column_names) # content:DataFrame
                st.session_state.visual_info:list[tuple] = list() # 시각자료 초기화
                self.choices_list = list() # 사용자가 제시해야하는 예약항목들 초기화
                
                # full_response += " ".join(contents_for_fullresponse) # 선택지 정보를 dialogue에 추가하기 위한 작업(2): full_response에 추가
            
        return full_response

    def autoplay_audio(self, file_path: str):
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio controls autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(
                md,
                unsafe_allow_html=True,
            )
    
    def tts_func(self, bot_utterance:str): # 재호님)
        tts = gTTS(text=bot_utterance, lang='ko') 
        
        now = datetime.now()
        now = str(now).split(".")[0].replace("-","").replace(" ","_").replace(":","")
        audio_file = "tts/{}.wav".format(now)
        tts.save(audio_file)
        self.autoplay_audio(audio_file)

    def text_to_audio(self, bot_utterance:str):
        bot_utterance = re.sub(r'[^\w\s\d\.\,\?]', '', bot_utterance)
        bot_utterance = re.sub(r'\s+', ' ', bot_utterance).strip()
        # print('bot_utterance: ', bot_utterance)
        self.tts_func(bot_utterance) # 음성)

class DataFilter:
    def __init__(self):
        self.club_eng_kor = {a_dict['eng_name'] : a_dict['name'] for a_dict in club_info_list}
        self.range_delimeter = '~'
        self.comma_delimeter = ','
        self.answer_delimeter = ':'
        self.or_delimeter = '|'
        self.num_call_timeSearch = 0

    def dates_to_filter(self, start_date:str, end_date:str=None):
        start_date = datetime.strptime(start_date, "%Y년 %m월 %d일")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y년 %m월 %d일")
            delta:timedelta = end_date - start_date
            dates = list()
            for i in range(delta.days + 1):
                a_date = start_date + timedelta(days=i)
                dates.append(a_date.strftime("%Y-%m-%d"))
        else:
            dates = [start_date.strftime("%Y-%m-%d")]
        
        return dates

    def tzzim_time_search(self, date:str, club_list:str, start_time:str, end_time:str): 
        if not ta.use_sample_data:
            input = {"date":  date, "club_list": club_list, "start_time" : start_time, "end_time": end_time}
            if (st.session_state.data) and (num_call_timeSearch):
                filtered_data_raw = st.session_state.data
                club_list:list = [self.club_eng_kor[an_eng_club] for an_eng_club in club_list.split(',')]
                start_time = datetime.strptime(start_time, "%H").time() if start_time else None
                end_time = datetime.strptime(end_time, "%H").time() if end_time else None
                # start_time, end_time의 경우의 수: (value, value), (value, None), (None, value), (None, None)
                    
                filtered_data = list()
                for a_dict in filtered_data_raw:
                    if (a_dict['day'] == date) and (
                        a_dict['GC_name'] in club_list
                    ):  
                        copied_dict = copy.deepcopy(a_dict)
                        if not start_time and not end_time:
                            copied_dict['frame_list'] = a_dict['frame_list']
                        else:
                            filtered_frame_list = list()
                            for frame_string in a_dict['frame_list']:
                                a_frame = datetime.strptime(frame_string, "%H:%M").time()
                                if start_time and end_time and (start_time < a_frame < end_time):
                                    filtered_frame_list.append(frame_string)
                                elif start_time and not end_time and (a_frame > start_time):
                                    filtered_frame_list.append(frame_string)
                                elif not start_time and end_time and (a_frame < end_time):
                                    filtered_frame_list.append(frame_string)
                                    
                            if filtered_frame_list:
                                copied_dict['frame_list'] = filtered_frame_list
                            else:
                                continue

                        filtered_data.append(copied_dict)
            else:
                filtered_data = ta.get_timeSearch(input=input)
                self.num_call_timeSearch += 1
                
        return filtered_data
    
    def location_place_clublist(self, location:str, golf_club_name:str):
        club_kor_eng:dict = {a_dict['name'] : a_dict['eng_name'] for a_dict in club_info_list}
        club_per_location = dict()
        for a_dict in club_info_list:
            a_location = a_dict['location']
            if a_location in club_per_location:
                club_per_location[a_location].append(a_dict['name'])
            else:
                club_per_location[a_location] = [a_dict['name']]

        if (location == 'all') and (golf_club_name == 'all'): # 지역, 골프장 모두 상관없음
            club_list = self.comma_delimeter.join([a_dict['eng_name'] for a_dict in club_info_list])
            
        elif (location != 'all') and (golf_club_name == 'all'): # 지역만 조건있고 골프장은 상관없음
            # 복수의 지역
            if self.or_delimeter in location:
                locations =  location.split(self.or_delimeter) # [제주도, 영남권]
                golf_club_names = list()
                for a_location in locations:
                    golf_club_names += [a_golf_club for a_golf_club in club_per_location[a_location]] # [라온, 사이프러스,아난티남해]
            # 하나의 지역
            else:
                golf_club_names = [a_golf_club for a_golf_club in club_per_location[location]] # key값을 a_location으로 쓰지 않도록 주의
            
            club_list = self.comma_delimeter.join([club_kor_eng[a_golf_club] for a_golf_club in golf_club_names]) # raon,cypress,ananti

        else: # 지역, 골프장 모두 있는 경우, 골프장만 고려함
            # 복수의 골프장
            if self.or_delimeter in golf_club_name:
                golf_club_names =  golf_club_name.split(self.or_delimeter) # [라온, 사이프러스]
                club_list = self.comma_delimeter.join([club_kor_eng[a_golf_club] for a_golf_club in golf_club_names]) # raon,cypress
            # 하나의 골프장
            else:
                club_list = club_kor_eng[golf_club_name]
        
        return club_list
    
    def time_processing(self, start_time:str, end_time:str):
        
        if (start_time and (start_time != 'all')) and (end_time and (end_time != 'all')): # 시간이 범위로 주어진 경우
            # start_time_hour, end_time_hour
            start_time = datetime.strptime(start_time, "%H시 %M분")
            start_time_hour = str(start_time.hour)
            end_time = datetime.strptime(end_time, "%H시 %M분")
            if end_time.minute == 0:
                pass
            else:
                end_time = (end_time + timedelta(hours=1)) # '분'후처리 ex) end_time = "9시 45분"이면, 10시까지 시간을 받아야 함
            end_time_hour = str(end_time.hour)
            
            # self.start_time, self.end_time
            self.start_time = start_time.time()
            
        elif (start_time and (start_time != 'all')) and not end_time: # start_time만 있는 경우
            
            # start_time_hour, end_time_hour
            start_time = datetime.strptime(start_time, "%H시 %M분") # 시작시간 = 입력된 시간 1시간 전
            start_time_for_hour = (start_time - timedelta(hours=1))
            start_time_hour = str(start_time_for_hour.hour)
            if start_time.minute == 0:
                end_time = (start_time + timedelta(hours=1)) # 끝시간 = 입력된 시간 1시간 후
            else:
                end_time = (start_time + timedelta(hours=2)) # " + '분' 후처리 (입력시간이 9시 반이면 끝시간을 10시 반까지 나타낼 때 11시까지 받아놔야 함)
            end_time_hour = str(end_time.hour)
            
            # self.start_time, self.end_time 저장
            # print('start_time: ', start_time)
            self.start_time = (start_time - timedelta(hours=1)).time() # 시작시간 = 입력된 시간 1시간 전
            self.end_time = (start_time + timedelta(hours=1)).time() # 끝시간 = 입력된 시간 1시간 후
            
        elif (start_time == 'all') and (end_time == 'all'):
            # start_time_hour, end_time_hour
            start_time_hour = None
            end_time_hour = None

            # self.start_time, self.end_time 저장
            self.start_time = time(hour=0, minute=0, second=0)
            self.end_time = time(hour=23, minute=59, second=59)
        
        return start_time_hour, end_time_hour
    
    def date_place_processing(self, json_condition):
        # phase1:전처리 = date가 여러 개일 경우(V), 지역만 들어왔을 때 club_list처리(V)
        # 1. location, place to club_list
        club_list = self.location_place_clublist(json_condition['location'], json_condition['golf_club_name'])
        
        # print('club_list: ', club_list)
        # 2. date and hour
        dates = self.dates_to_filter(start_date=json_condition['start_date'], end_date=json_condition['end_date'])
        start_time_hour, end_time_hour = self.time_processing(json_condition['start_time'], json_condition['end_time'])
            
        # final: 데이터 가져오기
        if len(dates) > 1:
            date_place_result = list()
            for a_date in dates:
                date_place_result += self.tzzim_time_search(date=a_date,
                                        club_list=club_list,
                                        start_time=start_time_hour, # 아무것도 들어가지 않으면 모든 시간이 들어감
                                        end_time=end_time_hour)
        elif len(dates) == 1:
            a_date = dates[0]
            date_place_result = self.tzzim_time_search(date=a_date,
                                    club_list=club_list,
                                    start_time=start_time_hour,
                                    end_time=end_time_hour)
        else:
            raise ValueError('start_date must exist.')
    
        return date_place_result
    
    def course_miniute_processing(self, date_place_result:list[dict], json_condition):
        # phase2:후처리 = 세부적인 '분' 시간처리, 코스 처리
        course_minute_result = list()
        for a_dict in date_place_result:
            copied_dict = copy.deepcopy(a_dict)
            
            # 코스처리
            course:str = json_condition['course']
            if self.or_delimeter in course: # 복수의 코스
                courses:list = course.split(self.or_delimeter)
            else:                              # 하나의 코스
                courses:list = [course]
                
            if (json_condition['course'] != 'all') and (copied_dict['course'] not in courses): # 코스 중 일부를 선택해야하는데, 주어진 자료에 이는 코스가 선택지와 일치하지 않는다면
                continue
            else:
                if (self.start_time.minute == 0) and (self.end_time.minute == 0):
                    # print('self.start_time: ', self.start_time)
                    # print('self.end_time: ', self.end_time)
                    pass
                else:
                    # print('self.start_time: ', self.start_time)
                    # print('self.end_time: ', self.end_time)
                    
                    # '분' 후처리
                    filtered_frame_list = list()
                    for a_frame in copied_dict['frame_list']:
                        a_frame_datetime = datetime.strptime(a_frame, "%H:%M").time()
                        if self.start_time <= a_frame_datetime <= self.end_time:
                            filtered_frame_list.append(a_frame)
                                                
                    if filtered_frame_list:
                        copied_dict['frame_list'] = filtered_frame_list
                    else:
                        continue
                    
                course_minute_result.append(copied_dict)
                
        return course_minute_result
    
    def search_and_filter(self, json_condition):
        date_place_result = self.date_place_processing(json_condition)
        course_minute_result = self.course_miniute_processing(date_place_result, json_condition)
    
        return course_minute_result