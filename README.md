### screening_stock_data_dart

-----

* DART OpenAPI 키를 사용해서 주식 종목별 Data를 받고
* 여러 조건들로 가공한 Data를 Sheet 별로 나누어 저장하고 엑셀 파일로 Export
- Receive data by stock item using DART OpenAPI key
- Data processed under various conditions is divided and saved by sheet and exported as an Excel file

-----

1. requirements.txt에 적힌 모듈들을 설치하세요.

2. config 폴더 속 api_key_example.py 파일에 DART API 키를 넣습니다.

3. api_key_example.py 파일의 이름을 api_key.py 수정하여 사용하세요.

4. 1회 프로그램 정상 종료까지의 시간이 매우 길기 때문에 사전에 TEST를 수행하세요.

5. csv파일로 확장자를 지정하고 저장하면 오류가 발생합니다.

6. KOSPI200, KOSDAQ150은 정상적으로 크롤링 되지만 종목이 200개가 넘어가면 오류가 발생합니다.

7. 결과물을 MySQL로 전송하기 위해 xlsx_to_mysql를 만들었으니 같이 사용하시면 좋습니다.
