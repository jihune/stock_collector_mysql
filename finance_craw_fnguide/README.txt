
1. library 파일 속 db_config_example.py 파일에
사용할 MySQL DB에 해당하는 값을 넣고
db_config.py 라는 원래 이름으로 수정

2. 현재 모든 종목 = KRX300 지수의 구성종목 입니다. 수정을 원하시면 kind_stock_list.py 파일 수정

3. 기존에 DB에 동일한 이름의 Table이 저장되어 있는경우 replace 해서 교체됩니다.

4. DB 상 재무제표에 기입된 금액 단위는 억원입니다.