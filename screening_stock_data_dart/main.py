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
        # 적정주가는 3년간의 연간 재무제표를 분석하므로 1년에 1회만 업데이트하면 된다.

        # 단, 초과이익 계산시 BBB- 5년만기 채권의 금리가 필요하며, 이 금리는 변동된다.
        # https://www.kisrating.co.kr/ratingsStatistics/statics_spread.do
        # 위 링크에서 구할 수 있으며 아래 함수 매개변수에 넣어주면 된다.

        # net_worth_and_roe_list_for_s_rim.xlsx
        # 23년 10월 19일 마지막 갱신

        update_and_export_srim_data(11.63) # 2023-10-19

    else:
        exit(-1)
