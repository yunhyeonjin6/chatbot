from datetime import datetime
import openai
import jsonlines
import random
import re
import streamlit as st

from api import TzzimAPI
ta = TzzimAPI()


class InitValues:
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

        self.choices_init = {
            'location':list(),
            'golf_club_name': list(),
            'course': list()
        }

        for k1, k2 in zip(self.choices_init, ['location', 'name', 'course']):
            for a_dict in self.club_info_list:
                if k2 == 'course':
                    self.choices_init[k1] += a_dict[k2]
                else:
                    self.choices_init[k1].append(a_dict[k2])
            self.choices_init[k1] = list(set(self.choices_init[k1]))
        
        self.choices_dict = self.choices_init
        
        self.num_time_candidate = 3
        
    
        # 2. 검증 관련
        self.json_verification:dict = {"json_all_correct": "null", "json_key_not_correct": "null"}
        
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
        initial_golf_list = lambda key_name: list(set([a_dict[key_name].lower() for a_dict in self.club_info_list]))
        initial_course_list = list(set([a_course.lower() for a_dict in self.club_info_list for a_course in a_dict['course']]))
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
            'task': [f"현재 티찜AI는 골프장 예약작업만 지원하고 있습니다."],
            'date': ['티찜AI가 날짜를 계속 물어볼 경우 "날짜", "예약" 등의 단어를 포함한 문장으로 답변해주세요.'],
            'location': [f'지역은  중에서 선택하실 수 있습니다.'],
            'place': [f'골프장은  중에서 선택하실 수 있습니다.'],
            'course': ['현재 선택하신 골프장 중 선택가능 한 코스는 다음과 같습니다.'],
            'tee_time_for_reservation': ['티찜AI가 예약시간을 계속 물어볼 경우 "예약시간"을 포함한 문장으로 답변해주세요.']
        }

        self.key_condition_list = {k : '  \n\t- ' + self.condition_list_format(v) for k, v in self.key_condition_list.items()}

