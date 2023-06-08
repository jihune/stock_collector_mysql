from library.craw_start import craw_and_process
from library.crawling_data_for_s_rim import update_and_export_srim_data

if __name__ == "__main__":
    
    # S-RIM 적정주가를 계산해서 엑셀 파일로 Export 하는 함수
    # 적정주가는 신규상장 종목을 찾을 때 외에는
    # 어차피 3년간 재무제표 기반이므로 1년에 1회만 업데이트하면 된다.
    # 재무제표 상 초과이익 계산시 BBB- 채권의 금리가 필요하나, 상수값 10.0으로 고정

    # update_and_export_srim_data()

    # 크롤링 및 프로세싱을 시작하는 함수.
    # 함수가 위치한 파일은 library 폴더의 craw_start.py

    craw_and_process()
