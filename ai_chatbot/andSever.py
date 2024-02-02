import requests

url = 'http://172.30.1.78:8080'  # Android 기기의 IP 주소와 포트를 적절히 설정
response = requests.get(url)

if response.status_code == 200:
    print('서버 응답:', response.text)
else:
    print('서버 응답 실패:', response.status_code)