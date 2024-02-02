import copy
from datetime import datetime
import openai
import pandas as pd
import re
import streamlit as st

from init import InitValues # session_state 초기화
from data_filter import DataFilter
filter = DataFilter()

class Tzzim(InitValues):
    def __init__(self):
        super().__init__()
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
                elif k in ['date', 'tee_time_for_reservation']: # "yyyy년 mm월 dd일 ~ yyyy년 mm월 dd일" 처리하기
                    if k == 'date':
                        regex = r'\d{4}년\d{2}월\d{2}일'
                    else:
                        regex = r'\d{2}시\d{2}분'
                    find_date_time:list = re.findall(regex, self.remove_space(v))
                    has_rest = False
                    has_value_not_correct = False
                    # 날짜 이외의 문자열이 있는 경우 수정필요
                    if isinstance(find_date_time, list) and (len(find_date_time) == 1):
                        date_text = find_date_time[0]
                        has_rest = self.rest_of_date(self.remove_space(v), date_text)
                        if has_rest:
                            has_value_not_correct = True
                        else:
                            pass
                    elif isinstance(find_date_time, list) and (len(find_date_time) == 2):
                        for value, date_text in zip(v.split(self.range_delimeter), find_date_time):
                            has_rest = self.rest_of_date(self.remove_space(value), date_text)
                            if has_rest:
                                has_value_not_correct = True
                                break
                    else:
                        has_value_not_correct = True                     
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
        key_instruction = f"""위와 같은 대화가 주어졌을 때 추가된 대화를 사용하여 아래 선택지에서 수정이 필요한 값을 선택해주세요. 출력형식에 따라 출력값만 생성해주세요.
                선택지: {','.join(list(self.json_obj.keys()))}
                출력형식: A,B,C
                조건1: 수정이 필요없다면 'null'을 생성해주세요.
                조건2: {','.join(self.choices_dict['location'])}이 있다면 'location'를 선택해주세요.
                
                출력:\n"""
        # ChatGPT결과가 따옴표까지 생성하는 것 조심해야함   
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
                else:
                    keys = [keys]

        return keys
    
    def key_generation(self, dialogue:str, keys_to_generate:list) -> dict:
        prompt_condition_list = self.ner_conditions['basic']
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
        json_string_generated = self.chatgpt_return(user_prompt)
        json_generated = self.to_json(json_string_generated)
        
        return json_generated
    
    def key_classification(self, dialogue:str, keys_to_classify:list) -> dict:
        prompt_condition_list = self.ner_conditions['basic'] + self.ner_conditions['classification']
        classification_choices_list = list()

        for a_key in keys_to_classify:
            if a_key in self.ner_conditions:
                prompt_condition_list += self.ner_conditions[a_key]
                
            if a_key in ['location', 'golf_club_name', 'course']:
                choice_phrase = f'{self.json_keyname[a_key]} 선택지: {self.choices_dict[a_key]}'
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
        json_string_classified = self.chatgpt_return(user_prompt)
        json_classified = self.to_json(json_string_classified)
        
        return json_classified
        
    def update_json_string(self, dialogue:str) -> str:
        """
        대화문이 주어졌을 때 json의 예약정보를 추가/수정하는 함수 
        """
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
                        json_changed[k] = v
                
                if json_classified and k in json_classified:
                    for k, v in json_classified.items():
                        json_changed[k] = v
                        
            # print('json_generated: ', json_generated)
            # print('json_classified: ', json_classified)
            # print('json_obj_prior: ', json_obj_prior)
            # print('json_changed: ', json_changed)

            st.session_state.json_string = str(json_changed)
            
            # 데이터 필터링을 위한 json_condition 업데이트
            self.update_json_condition()


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
                        to_append = (f"{self.json_keyname[k]}의 경우 " + f"{(self.comma_delimeter + ' ').join(list(set([a_dict[self.column_mapping[k]].lower() for a_dict in st.session_state.data])))} 중에서 고르실 수 있습니다.")
                        self.choices_list.append(to_append)
                    else:
                        pass
                else:
                    pass                
        
        if keys_to_ask:
            if no_search_result:
                phrase_to_add = '등을 다시 설정해주세요.'
            else:
                phrase_to_add = '도 특정하실 수 있습니다.'
        else:
            phrase_to_add = ' 등을 선택해주세요.'
        
        if keys_for_question: 
            generated_question = (self.comma_delimeter + " ").join([self.json_keyname[a_key] for a_key in keys_for_question]) + phrase_to_add
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
            response = f"{self.json_keyname[wrong_key]} 항목을 수정해드리겠습니다. 다시 말씀해주시겠습니까? 다음 조건을 참고하셔서 답변 부탁드립니다.\n" + self.key_condition_list[wrong_key]
            
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
    
    def response_generation(self, dialogue):
        self.update_json_string(dialogue) # 예약정보 업데이트
        self.update_json_verification(st.session_state.json_string) # 검증 업데이트
        
        json_verification_check = st.session_state.json_check['verification']
        
        if json_verification_check['json_all_correct']: # NER값들이 전부 맞았을 때
            print('response_gen: case1')
                            
            if not st.session_state.login['ask_gc'] and (
                self.to_json(st.session_state.json_string)['task'] != "null" # case1) 회원이 골프장 예약을 한다는 것을 알았고, 가입한 골프장 명단을 아직 안내하지 않은 경우 
            ):
                # self.update_json_string(dialogue) # 예약정보 업데이트
                # self.update_json_verification(dialogue) # 검증 업데이트
                response = f"네, 알겠습니다! 현재  푸른하늘님은 {len(self.club_info_list)}개 골프장의 회원이십니다. 골프장 명단을 알려드릴까요?"
                st.session_state.login['ask_gc'] = True

            elif st.session_state.login['ask_gc'] and ( # case2) 골프장 안내여부에 대한 답변을 들은 경우
                st.session_state.login['yes_no'] == 'null'
            ):
                self.yes_no(dialogue)
                
                if st.session_state.login['yes_no']: # 골프장 명단을 알려드릴까요? -> 예
                    gc_list = [a_dict['name'] + 'CC' for a_dict in self.club_info_list]
                    response = f"회원이신 골프장은 {', '.join(gc_list)} 입니다. 어떻게 예약을 도와드릴까요?"
                
                else: # 골프장 명단을 알려드릴까요? -> 아니오
                    response = "네 알겠습니다, 바로 예약 진행하겠습니다. 어떻게 예약을 도와드릴까요?"  
                st.session_state.visual_info = [(self.initial_reservation_example, 'container')]
                    
            else:                                       # case3) 예약정보 받기
                keys_to_filter = [k for k, v in self.to_json(st.session_state.json_string).items() if k != "task" and v != 'null'] # null이 아닌 데이터를 불러와서 필터링 하기
                json_obj_ask = self.to_json(st.session_state.json_string)# 범위 표현에 대한 질문추가
                keys_ask_again = [k for k, v in json_obj_ask.items() if self.ask_again_condition(k,v)]

                if len(keys_to_filter) > 0:
                    if 'date' not in keys_to_filter: # 날짜가 없을 경우 날짜질문으로 좁히기
                        response = self.question_generation()
                    elif 'date' in keys_ask_again:
                        start_date_parse = datetime.strptime(st.session_state.json_condition['start_date'],'%Y년 %m월 %d일').strpftime('%m월 %d일')
                        end_date_parse = datetime.strptime(st.session_state.json_condition['end_date'],'%Y년 %m월 %d일').strpftime('%m월 %d일')
                        response = f'{start_date_parse}부터 {end_date_parse}까지 날짜 중에서 하루를 선택해주실 수 있나요?'
                    # elif ('location' in keys_ask_again) or ('golf_club_name' in keys_ask_again): # 지역이나 골프장이 정해진 경우 
                    #     pass
                    else: 
                        if (json_obj_ask['golf_club_name'] != 'null') and ('golf_club_name' not in keys_ask_again): # 골프장이 하나로 확정된 경우
                            location_of_club = [a_dict['location'] for a_dict in self.club_info_list if a_dict['name'] == json_obj_ask['golf_club_name']][0]
                            json_obj_ask['location'] = location_of_club
                            st.session_state.json_string = str(json_obj_ask)
                            self.update_json_string(dialogue)
                        else:
                            pass
                          
                        filtered_result = filter.search_and_filter(st.session_state.json_condition)

                        if filtered_result: # 검색결과 있음
                            st.session_state.data = filtered_result # 필터링된 데이터 저장                            
                            response = '검색을 완료하였습니다. '
                            response += self.question_generation() # 더 질문해야할 것들 추가

                            if keys_ask_again:
                                response += (" " + self.question_generation(keys_ask_again))
                            
                            # 시각자료 추가
                            if self.choices_list:
                                st.session_state.visual_info.append(('  \n\t- ' + self.condition_list_format(self.choices_list), 'container'))
                            else:
                                pass
                            filtered_df = pd.DataFrame(filtered_result)
                            st.session_state.visual_info.append((filtered_df, 'dataframe'))
                            
                        else: # 검색결과 없는 경우
                            response = '검색결과가 없습니다. '
                            response += self.question_generation(keys_to_ask=keys_to_filter, no_search_result=True) # 검색결과가 없는 경우 방금 받은 조건으로 재질문
                else:
                    response = self.question_generation()
                    if keys_ask_again:
                        response += (" " + self.question_generation(keys_ask_again))
                    
        elif st.session_state.json_check["correction"]: # case5) 예약확인 단계에서 수정의사를 밝혔을 경우 response 없음
            print('response_gen: case2')
            response = ''
        else:
            print('response_gen: case3')
            json_obj_check = self.to_json(st.session_state.json_string)
            wrong_key = json_verification_check['json_key_not_correct']
            if json_obj_check[wrong_key] == 'null': # verification의 내용이 'null'만 있어도 잘못되었다고 판단하기 때문에 기준을 넣음
                response = self.question_generation()
            else:
                response = f"{self.json_keyname[wrong_key]}에 대해 다시 여쭤봐도 되겠습니까? 다음 조건을 참고하셔서 답변 부탁드립니다.\n" + self.key_condition_list[wrong_key]
                
                # 다시 물어본 예약정보 json 키의 value 값을 "null"로 직접 대체
                json_obj_check[wrong_key] = "null"
                st.session_state.json_string = str(json_obj_check)
        
        return response

    def complete_or_ongoing(self, response):
        json_completion = self.to_json(st.session_state.json_check['completion'])
        complete_initial = (json_completion['reservation_complete'] == 'null') and (json_completion['reservation_not_completed_reason'] == 'null') # 예약확인을 하지 않은 상태
        complete_condition1 = json_completion['reservation_complete'] and (json_completion['reservation_complete'] != 'null')                      # 예약 완료
        complete_condition2 = st.session_state.json_check["correction"]                                                                            # 예약수정 의사와 수정된 답변 모두 받음, 예약 수정 시 중요함
        complete_condition3 = not json_completion['reservation_complete'] and (json_completion['reservation_not_completed_reason'] == 'null')      # 예약수정 의사만 밝힌 경우
        json_obj_ask = self.to_json(st.session_state.json_string)# 범위 표현 제외
        keys_ask_again = [k for k, v in json_obj_ask.items() if self.ask_again_condition(k,v)]
        
        case1_condition = complete_condition1 or complete_condition3
        case2_condition = 'null' not in st.session_state.json_string and (not keys_ask_again) and (complete_condition2 or complete_initial)
        
        if case1_condition:                                 # case1) 예약을 완료했거나 예약 수정 의사(수정 O/X)만 밝힌 경우
            print('complete: case1')
            full_response = response
            
        elif case2_condition:                               # case2) 예약확인 단계 (예약정보를 모두 받았고 예약확인을 한번도 하지 않았거나/수정된 답변을 모두 받음), 범위표현 제외
            print('complete: case2')
            st.session_state.correction_session = True
            
            # 현재까지 예약내역 표시
            json_obj_print = self.to_json(st.session_state.json_string)
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
            print('complete: case3')
            with st.chat_message("assistant"):
                placeholder = st.empty() # AI 답변받을 때까지 보관
                full_response = ''
                for item in response:
                    full_response += item
                placeholder.markdown(full_response) # AI 답변 바로표기
                self.text_to_audio(full_response)

            if st.session_state.visual_info:
                for content, type in st.session_state.visual_info:
                    if type == 'container':
                        visual_container = st.container()
                        visual_container.write(content) # content:str
                        self.text_to_audio(content)
                    elif type == 'dataframe':
                        st.dataframe(content, hide_index=True, column_config=self.column_names) # content:DataFrame
                st.session_state.visual_info:list[tuple] = list() # 시각자료 초기화
                self.choices_list = list() # 사용자가 제시해야하는 예약항목들 초기화
            
        return full_response

    def tts_func(self, bot_utterance:str): # 재호님)
        pass

    def text_to_audio(self, bot_utterance:str):
        bot_utterance = re.sub(r'[^\w\s\d\.\,\?]|[\n\t]', '', bot_utterance)
        bot_utterance = re.sub(r'\s+', ' ', bot_utterance).strip()
        # print('bot_utterance: ', bot_utterance)
        self.tts_func(bot_utterance) # 음성읽기
        