
## screening_stock_data_dart

-----

* DART OpenAPI 키를 사용해서 주식 종목별 Data를 받고
* 여러 조건들로 가공한 Data를 Sheet 별로 나누어 저장하고 엑셀 파일로 Export

- Receive data by stock item using DART OpenAPI key
- Data processed under various conditions is divided and saved by sheet and exported as an Excel file

-----

1. requirements.txt에 적힌 패키지들을 설치하세요.
    * 가급적 패키지의 버전을 맞춰주세요.
    * FinanceDataReader 같은 패키지는 버전이 다를 경우  
      Setor, Dept, Sec 이런 식으로 같은 항목에 대해 버전마다 다른 변수명을 사용하기에 오류가 발생합니다.

2. config 폴더 속 api_key_example.py 파일에 DART API 키를 넣습니다.
   * 이후 api_key_example.py 파일의 이름을 api_key.py 수정하여 사용하세요.

3. csv파일로 저장하면 현재 오류가 발생합니다.

4. 연간 재무제표 기반의 Data는 빠르게 잘 받아옵니다.
   * 분기 재무제표 기반의 Data는 크롤링 중간에 끊기는 경우가 발생합니다.
   * 현재 분기 재무제표 기반 크롤링 시 대상으로 KOSPI200, KOSDAQ150 지수만 크롤링 해야 합니다.
   * S-RIM 적정주가 계산의 산출근거가 되는 Data는 1년에 1번만 갱신하면 됩니다.

5. 결과물을 MySQL로 전송하기 위해 xlsx_to_mysql를 만들었으니 같이 사용하시면 좋습니다.
