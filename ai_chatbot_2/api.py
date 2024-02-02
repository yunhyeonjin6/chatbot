import json
import streamlit as st
import re
import requests

BASE_API_URL = 'http://192.168.0.7:8080'

class TzzimAPI:
    def __init__(self):
        self.use_sample_data = True # 현진님) 테스트 시 self.use_sample_data = False로 전환
        with open(r"C:\Users\mnemosyne\Desktop\teezzim\ai_chatbot_2\data.json", "r", encoding='utf-8') as file:
            self.sample_data = json.load(file)
        
    def json_to_data(self, json_string):
        json_raw = json.loads(json_string)
        if json_raw['status_code'] == '200':
            data_list:list[dict] = json_raw['data']
            return data_list
        else: 
            self.when_api_failed()
            
    def tts_func(self, bot_utterance:str): # 재호님)
        pass

    def text_to_audio(self, bot_utterance:str):
        bot_utterance = re.sub(r'[^\w\s\d\.\,\?]|[\n\t]', '', bot_utterance)
        bot_utterance = re.sub(r'\s+', ' ', bot_utterance).strip()
        # print('bot_utterance: ', bot_utterance)
        self.tts_func(bot_utterance) # 음성읽기
            
    def when_api_failed(self, api_name:str=None):
        if api_name == 'reservation':
            failed_message = '예약할 수 없는 티입니다. 이전 조건으로 돌아갑니다!'
        else:  
            failed_message = '티찜AI가 회원님의 골프장 정보를 다시 불러올 수 있도록 새로고침 해주세요!'
            
        with st.chat_message('assistant'):
            st.write(failed_message)
            self.text_to_audio(failed_message)
    
    def get_clubInfoList(self):
        # response = requests.post(BASE_API_URL + "/clubInfoList")
        # response = requests.post(BASE_API_URL + "/autoLogin")
        # response = requests.post(BASE_API_URL + "/dateSearch")
        # # response = requests.post(BASE_API_URL + "/timeSearch")
        # # response = requests.post(BASE_API_URL + "/reserve")
        # json_string = response.text # FastAPI 함수배치
        # club_info_list = self.json_to_data(json_string)
        
        # if self.use_sample_data: # sample data 사용 시
        #     club_info_list:list[dict] = self.sample_data['clubInfoList']['data']
            
        # else:# FastAPI 호출 시
        response = requests.post(BASE_API_URL + "/clubInfoList")
        club_info_list = self.json_to_data(response)
        return club_info_list
    
    def get_timeSearch(self, input:dict) -> list[dict]:
        if self.use_sample_data:
            time_search:list[dict] = self.sample_data['timeSearch']['data']
        else:
            input = str(input)
            response = requests.post(BASE_API_URL + "/timeSearch")
            json_string = response.text # FastAPI 함수배치
            time_search = self.json_to_data(json_string)
            print("===============")
            print(time_search)
        return time_search
    
    def get_dateSearch(self) -> list[dict]:
        if self.use_sample_data:
            date_search:list[dict] = self.sample_data['dateSearch']['data']
        else:
            response = requests.post(BASE_API_URL + "/dateSearch")
            json_string = response.text # FastAPI 함수배치
            date_search = self.json_to_data(json_string)
            print("===============")
            print(date_search)
        return date_search
    
    def get_reservation(self, input:dict) -> str:
        if self.use_sample_data:
            success_or_fail:str = self.sample_data['reservation']['message']
        else:
            input = str(input)
            response = requests.post(BASE_API_URL + "/reserve")
            json_string = response.text # FastAPI 함수배치
            json_raw = json.loads(json_string)
            print("===============")
            print(json_raw)
            if json_raw['status_code'] == '200':
                success_or_fail:str = json_raw['message']
                return success_or_fail
            else: 
                self.when_api_failed(api_name='reservation')