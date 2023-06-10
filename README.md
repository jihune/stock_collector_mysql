
## stock_collector_mysql

#### [collect_stock_data_kiwoom_32](https://github.com/jihune/collect_stock_data_kiwoom_32)

* 키움증권 API로 종목의 최신 일별 데이터를 수집하고 MySQL에 Schema 생성 및 Table로 저장
- Collect the latest daily data of stocks with Kiwoom API, create a schema in MySQL and save it as a table

-----

#### [finance_craw_fnguide](https://github.com/jihune/finance_craw_fnguide)

* FnGuide 사이트에서 주식 종목의 재무제표 데이터를 수집, MySQL에 Table로 저장
- Collect financial statement data of stock items from the FnGuide site and save them as tables in MySQL

-----

#### [screening_stock_data_dart](https://github.com/jihune/screening_stock_data_dart)

* DART OpenAPI 키를 사용해서 주식 종목별 Data를 받고
* 여러 조건들로 가공한 Data를 Sheet 별로 나누어 저장하고 엑셀 파일로 Export
- Receive data by stock item using DART OpenAPI key
- Data processed under various conditions is divided and saved by sheet and exported as an Excel file

---

#### [xlsx_to_mysql](https://github.com/jihune/xlsx_to_mysql)

* 대화형 선택상자로 1개 혹은 여러 개의 *.xlsx 파일을 선택한 뒤 병합 및 중복 제거
* 읽어들인 엑셀파일들의 Sheet들을 MySQL DB Schema내에 각각의 Table로 저장
- Select one or multiple *.xlsx files with the interactive selector, then merge and remove duplicates
- Save the sheets of the read Excel files as individual tables in the MySQL DB Schema

----

* 더욱 자세한 내용은 각 프로그램 폴더 내부 README.md 참조
* 각 폴더 속 초기 실행파일은 main.py 파일로 모두 동일
