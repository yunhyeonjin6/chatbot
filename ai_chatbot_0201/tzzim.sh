# tzzim_demo.sh가 있는 디렉토리까지 이동 후 실행
conda activate tzzim
streamlit run ./my_streamlit.py --server.sslCertFile=server.crt --server.sslKeyFile=server.key
# --server.runOnSave=True # 중간 수정 후 바로 실행을 하고 싶다면 위 코드에 추가