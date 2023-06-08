### all_craw_and_process_dart

- Receive data by stock item using DART OpenAPI key
- Data processed under various conditions is divided and saved by sheet and exported as an Excel file
* DART OpenAPI 키를 사용해서 주식 종목별 Data를 받고
* 여러 조건들로 가공한 Data를 Sheet 별로 나누어 저장하고 엑셀 파일로 Export

-----

1. requirements.txt에 적힌 모듈들을 설치하세요.

2. config 폴더 속 api_key_example.py 파일에 DART API 키를 넣습니다.

3. api_key_example.py 파일의 이름을 api_key.py 수정하여 사용하세요.

4. csv파일로 저장하면 현재 오류가 납니다.

5. KOSPI200, KOSDAQ150은 잘 크롤링 합니다. 현재 종목이 200개가 넘어가면 오류가 발생합니다.

6. 결과물을 MySQL로 전송하기 위해 xlsx_to_mysql를 만들었으니 같이 사용하시면 좋습니다.
