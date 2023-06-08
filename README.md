### collect_stock_data_kiwoom_32

-----

- Collect the latest daily data of stocks with Kiwoom API, create a schema in MySQL and save it as a table
* 키움증권 API로 종목의 최신 일별 데이터를 수집하고 MySQL에 Schema 생성 및 Table로 저장

-----

1. 32bit Anaconda3 환경에서 requirements_32.txt에 적힌 모듈들을 설치하세요.

2. 라이브러리 폴더 속 cf_example.py 파일의 내용과 이름을 수정하여 cf.py 파일로 사용하세요.

3. 키움증권API에 1000회 이상 쿼리문을 요청할 경우 중간에 강제적으로 끊어질 수 있으므로  
999회까지만 요청하도록 cf.py 파일에 설정되어 있습니다.

4. 999회 쿼리문을 보내고 프로그램이 종료된 후에 다시 main.py를 가동하여도  
처음부터 재시작하지 않고 끊어진 중간 지점부터 Data Collecting을 시작합니다.
