import json
import streamlit as st
import re
import requests
import os

# BASE_API_URL = 'http://192.168.0.7:8080'
# BASE_API_URL = 'https://a59e-175-197-237-141.ngrok-free.app'
BASE_API_URL = 'http://172.30.1.100:8080'

class TzzimAPI:
    def __init__(self):
        self.use_sample_data = False # 현진님) 테스트 시 self.use_sample_data = False로 전환
        current_directory = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(current_directory, "data.json")
        with open(data_file_path, "r", encoding='utf-8') as file:
            self.sample_data = json.load(file)
        
    def json_to_data(self, json_string):
        if isinstance(json_string, str):
            json_to_put = json_string
        else:
            json_to_put = json_string.text
        json_raw = json.loads(json_to_put)
        print('json_raw: ', json_raw)
        
        if json_raw['status_code'] == 200:
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
        if self.use_sample_data: # sample data 사용 시
            club_info_list:list[dict] = self.sample_data['clubInfoList']['data']
            
        else:# FastAPI 호출 시
            json_string = requests.post(BASE_API_URL + "/reservation") # FastAPI 함수배치
            club_info_list = self.json_to_data(json_string)
  
        return club_info_list
    
    def get_timeSearch(self, input:dict) -> list[dict]:
        if self.use_sample_data:
            time_search:list[dict] = self.sample_data['timeSearch']['data']
        else:
            input = str(input)
            json_string = requests.post(BASE_API_URL + "/timeSearch", data = input) # FastAPI 함수배치
            time_search = self.json_to_data(json_string)
        return time_search
    
    def get_dateSearch(self) -> list[dict]:
        if self.use_sample_data:
            date_search:list[dict] = self.sample_data['dateSearch']['data']
        else:
            json_string = requests.post(BASE_API_URL + "/dateSearch") # FastAPI 함수배치
            date_search = self.json_to_data(json_string)
        return date_search
    
    def get_reservation(self, input:dict) -> str:
        if self.use_sample_data:
            success_or_fail:str = self.sample_data['reservation']['message']
        else:
            input = str(input)
            encoded_string = input.encode('utf-8')
            json_string = requests.post(BASE_API_URL + "/reservation", data=encoded_string) # FastAPI 함수배치
            json_raw = json.loads(json_string)
            if json_raw['status_code'] == '200':
                success_or_fail:str = json_raw['message']
                return success_or_fail
            else: 
                self.when_api_failed(api_name='reservation')