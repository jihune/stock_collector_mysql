
##### all_craw_and_process_dart
* Receive and process stock data using the DART OpenAPI key and convert it into an Excel file
* DART OpenAPI 키를 사용해서 정보를 받고 다량의 정보로 산출하고 엑셀 파일로 변환

-----

##### daily_craw_kiwoom_32
* 키움증권 API로 종목의 일별 데이터를 수집하고 MySQL에 Schema 및 Table로 저장

-----


##### finance_craw_fnguide
* FnGuide의 특정종목, 전종목 재무제표 데이터를 수집하고 MySQL에 Table화

-----

##### xlsx-to-mysql
* Select one or multiple *.xlsx files with the interactive selector, merge and remove duplicates
* Each sheet is converted into a table with MySQL DB and stored
* 대화형 선택상자로 1개 혹은 여러 개의 *.xlsx 파일을 선택한 뒤 병합 및 중복 제거
* MySQL DB로 각 Sheet를 Table화 하여 저장

---

##### 프로젝트 환경
* Pycharm, Anaconda 32bit 및 Anaconda 64bit (2022년 이후 버전)
* 각 폴더 requirements.txt 모듈 설치

----

* 더욱 자세한 내용은 각 프로그램 폴더 내부 README.txt 참조
* 각 폴더 속 초기 실행파일은 main.py 파일로 모두 동일함
