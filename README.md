# all_craw_and_process_dart

-----

* DART OpenAPI 키를 사용해서 주식 Data를 받고 가공하여 엑셀 파일로 변환
* Receive and process stock data using the DART OpenAPI key and convert it into an Excel file

-----

1. requirements.txt에 적힌 모듈들을 설치하세요.

2. config 폴더 속 api_key_example.py 파일에
DART API 키를 넣습니다.

3. api_key_example.py 파일의 이름을 api_key.py 수정하여 사용하세요.

4. csv파일로 저장하면 현재 오류가 납니다.

5. KOSPI200, KOSDAQ150은 잘 크롤링 해 올 종목이 200개가 넘어가면 현재 오류가 발생합니다.

6. 결과물을 MySQL로 전송하기 위해 xlsx_to_mysql를 개발했으니 같이 사용하시면 좋습니다.
