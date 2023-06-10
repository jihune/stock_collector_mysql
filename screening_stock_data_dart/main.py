from library import quarter_craw
from library import year_craw
from library.crawling_data_for_s_rim import update_and_export_srim_data

if __name__ == "__main__":

    print("필요로 주식 Data의 종류 선택")
    choice = int(input("연간 재무제표 기반 (빠름): 1 / 분기 재무제표 기반 (느림, 에러 있음): 2"
                       " / S-RIM 최신화 (1년에 1번만): 3 => "))

    if choice == 1:
        year_craw.craw_and_process()

    elif choice == 2:
        quarter_craw.craw_and_process()

    elif choice == 3:

        # S-RIM 적정주가를 계산해서 엑셀 파일로 Export 하는 함수
        # 적정주가는 신규상장 종목을 찾을 때 외에는
        # 어차피 3년간 재무제표 기반이므로 1년에 1회만 업데이트하면 된다.
        # 재무제표 상 초과이익 계산시 BBB- 채권의 금리가 필요하나, 상수값 10.0으로 고정

        # 23년 6월 9일 마지막 갱신

        update_and_export_srim_data()

    else:
        exit(-1)
