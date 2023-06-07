from library.collector_api import *

class Collector:
    def __init__(self):
        self.collector_api = collector_api()

    def collecting(self):
        self.collector_api.code_update_check()

if __name__ == "__main__":

    # library 폴더 속 cf파일 속에 DB설정을 해주고, 키움증권API가 허가된 계좌번호가 있어야 한다.
    app = QApplication(sys.argv)
    c = Collector()

    # 데이터 수집 시작 -> 주식 종목, 종목별 금융 데이터 모두 데이터베이스에 저장.
    c.collecting()

    print("종목별 일별 Data Colleting 완료 및 프로그램 정상종료")