### xlsx_to_mysql

-----

* 대화형 선택상자로 1개 혹은 여러 개의 *.xlsx 파일을 선택한 뒤 병합 및 중복 제거
* 읽어들인 엑셀파일들의 Sheet들을 MySQL DB Schema내에 각각의 Table로 저장
- Select one or multiple *.xlsx files with the interactive selector, then merge and remove duplicates
- Save the sheets of the read Excel files as individual tables in the MySQL DB Schema

-----

1. library 파일 속 db_config_example.py 파일에 사용할 MySQL DB에 해당하는 값을 넣습니다.

2. db_config_example.py 파일을 db_config.py 로 수정

3. 기존에 DB에 동일한 이름의 Table이 저장되어 있는경우 replace 해서 교체됩니다.

4. DB 상 재무제표에 기입된 금액 단위는 억원입니다.
