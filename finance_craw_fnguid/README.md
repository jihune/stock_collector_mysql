
### finance_craw_fnguide

-----

* FnGuide 사이트에서 주식 종목의 재무제표 데이터를 수집, MySQL에 Table로 저장
- Collect financial statement data of stock items from the FnGuide site and save them as tables in MySQL

-----

1. library 폴더 속 db_config_example.py 파일에 사용할 MySQL DB에 해당하는 값을 넣고, db_config.py 로 이름 변경

2. 현재 모든 종목 = KOSPI200 + KOSDAQ150 + KRX300 지수의 구성종목. 수정을 원하면 kind_stock_list.py 수정

3. 기존에 DB에 동일한 이름의 Table이 저장되어 있는경우 replace 해서 교체됩니다.

4. DB 상 재무제표에 기입된 금액 단위는 억원입니다.

5. API 키 없이 쉽게 사용 가능하지만 너무 많은 데이터를 크롤링 시도하면 IP차단 당할 수 있습니다.
