import copy
from datetime import datetime, timedelta, time

from init import InitValues
from api import TzzimAPI
init = InitValues()
ta = TzzimAPI()

class DataFilter:
    def __init__(self):
        self.club_info_list = init.club_info_list
        self.club_eng_kor = {a_dict['eng_name'] : a_dict['name'] for a_dict in self.club_info_list}

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
            filtered_data = ta.get_timeSearch(input=input)
        else:
            time_search = ta.get_timeSearch(input=None)
            club_list:list = [self.club_eng_kor[an_eng_club] for an_eng_club in club_list.split(',')]
            start_time = datetime.strptime(start_time, "%H").time() if start_time else None
            end_time = datetime.strptime(end_time, "%H").time() if end_time else None
            # start_time, end_time의 경우의 수: (value, value), (value, None), (None, value), (None, None)
                
            filtered_data = list()
            for a_dict in time_search:
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
                
        return filtered_data
    
    def location_place_clublist(self, location:str, golf_club_name:str):
        club_kor_eng:dict = {a_dict['name'] : a_dict['eng_name'] for a_dict in self.club_info_list}
        club_per_location = dict()
        for a_dict in self.club_info_list:
            a_location = a_dict['location']
            if a_location in club_per_location:
                club_per_location[a_location].append(a_dict['name'])
            else:
                club_per_location[a_location] = [a_dict['name']]

        if (location == 'all') and (golf_club_name == 'all'): # 지역, 골프장 모두 상관없음
            club_list = init.comma_delimeter.join([a_dict['eng_name'] for a_dict in self.club_info_list])
            
        elif (location != 'all') and (golf_club_name == 'all'): # 지역만 조건있고 골프장은 상관없음
            # 복수의 지역
            if init.or_delimeter in location:
                locations =  location.split(init.or_delimeter) # [제주도, 영남권]
                golf_club_names = list()
                for a_location in locations:
                    golf_club_names += [a_golf_club for a_golf_club in club_per_location[a_location]] # [라온, 사이프러스,아난티남해]
            # 하나의 지역
            else:
                golf_club_names = [a_golf_club for a_golf_club in club_per_location[location]] # key값을 a_location으로 쓰지 않도록 주의
            
            club_list = init.comma_delimeter.join([club_kor_eng[a_golf_club] for a_golf_club in golf_club_names]) # raon,cypress,ananti

        else: # 지역, 골프장 모두 있는 경우, 골프장만 고려함
            # 복수의 골프장
            if init.or_delimeter in golf_club_name:
                golf_club_names =  golf_club_name.split(init.or_delimeter) # [라온, 사이프러스]
                club_list = init.comma_delimeter.join([club_kor_eng[a_golf_club] for a_golf_club in golf_club_names]) # raon,cypress
            # 하나의 골프장
            else:
                club_list = club_kor_eng[golf_club_name]
        
        return club_list
    
    def time_processing(self, start_time:str, end_time:str):
        
        # start_time_hour, end_time_hour 반환
        if start_time and (start_time != 'all'):
            start_time = datetime.strptime(start_time, "%H%Y시 %M분")
            start_time_hour = str(start_time.hour)
        else:
            start_time_hour = None
            
        if end_time and (end_time != 'all'):
            end_time = datetime.strptime(end_time, "%H시 %M분")
            if end_time.minute == 0:
                pass
            else:
                end_time = (end_time + timedelta(hours=1)) # '분'후처리 ex) end_time = "9시 45분"이면, 10시까지 시간을 받아야 함
            end_time_hour = str(end_time.hour)
        else:
            end_time_hour = None
        
        # self.start_time, self.end_time 저장
        if start_time == 'all':
            self.start_time = time(hour=0, minute=0, second=0)
        else:
            self.start_time = start_time.time()

        if end_time == 'all':
            self.end_time = time(hour=23, minute=59, second=59)
        elif not end_time: # end_time이 None일 경우 start_time에서 1시간 추가한 것을 end_time으로 지정
            self.end_time = (start_time + timedelta(hours=1)).time()
        else:
            self.end_time = (end_time - timedelta(hours=1)).time() # '분'후처리에 정확한 끝시간 설정을 위해 되돌리기

        return start_time_hour, end_time_hour
    
    def date_place_processing(self, json_condition):
        # phase1:전처리 = date가 여러 개일 경우(V), 지역만 들어왔을 때 club_list처리(V)
        # 1. location, place to club_list
        club_list = self.location_place_clublist(json_condition['location'], json_condition['golf_club_name'])
        
        print('club_list: ', club_list)
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
            if init.or_delimeter in course: # 복수의 코스
                courses:list = course.split(init.or_delimeter)
            else:                              # 하나의 코스
                courses:list = [course]
                
            if (json_condition['course'] != 'all') and (copied_dict['course'] not in courses): # 코스 중 일부를 선택해야하는데, 주어진 자료에 이는 코스가 선택지와 일치하지 않는다면
                continue
            else:
                if (self.start_time.minute == 0) and (self.end_time.minute == 0):
                    pass
                else:
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