import datetime
import time
import os
import stock.filter_data as filter_data
from stock.extract_data.extract import Extract
from export_data import ExportToData
import datetime

this_year = datetime.datetime.now().year
years = [this_year-2, this_year-1, this_year]

def filterging_data(choice, data):
    if choice == 1:
        return filter_data.filtering_data_that_market_cap_under(0.3, data)
    elif choice == 2:
        return filter_data.filtering_data_that_market_cap_greater_than(0.8, data)
    elif choice == 3:
        return filter_data.filtering_data_that_market_index_kospi200(data)
    elif choice == 4:
        return filter_data.filtering_data_that_market_index_kosdaq150(data)
    elif choice == 5:
        return filter_data.filtering_data_that_market_index_krx300(data)
    elif choice == 6:
        return filter_data.filtering_data_that_market_index_test(data)

def export_data(category, raw_data, extracted_data):
    exporter = ExportToData()

    directory = os.path.join(os.path.dirname(__file__), 'result_xlsx')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 현재 시간을 파일 이름에 추가합니다.
    current_date = datetime.datetime.today().strftime('%Y%m%d')
    current_time = datetime.datetime.now().strftime('%H%M')

    file_name = f"{current_date}_{current_time}_{category}.xlsx"

    file_path = os.path.join(directory, file_name)

    exporter.export_to_excel_with_many_sheets(
        file_path,
        [
            filter_data.filtering_low_per("ALL_DATA_저PER", raw_data.copy(), True),
            filter_data.filtering_low_pbr_and_per("ALL_DATA_저PBR_저PER", 1.0, 10, raw_data.copy(), True),
            filter_data.filtering_s_rim_disparity_all_data("S-RIM ALL_DATA", raw_data.copy()),
            filter_data.filtering_low_per(f"{category}_저PER", extracted_data.copy()),
            filter_data.filtering_low_pbr_and_per(f"{category}_저PBR_저PER", 1.0, 10, extracted_data.copy()),
            filter_data.filtering_low_psr_and_per(f"{category}_저PSR_저PER", 10, extracted_data.copy()),
            filter_data.filtering_peg(f"{category}_PEG", extracted_data.copy()),
            filter_data.filtering_high_div("고배당률_리스트", raw_data.copy()),
            filter_data.filtering_low_pfcr(f"{category}_저PFCR_시총잉여현금흐름", extracted_data.copy()),
            filter_data.filtering_high_ncav_cap_and_gpa(f"{category}_고NCAV_GPA_저부채비율", extracted_data.copy()),
            filter_data.filtering_s_rim_disparity_and_high_nav(f"{category}_S-RIM_괴리율_고NAV", extracted_data.copy()),
            filter_data.filtering_profit_momentum(f"{category}_모멘텀_전분기대비_영업이익순이익_전략", extracted_data.copy()),
            filter_data.filtering_value_factor(f"{category}_슈퍼가치_4가지_전략", extracted_data.copy()),
            filter_data.filtering_value_and_profit_momentum(f"{category}_성장주모멘텀_전략", extracted_data.copy()),
            filter_data.filtering_value_factor3(f"{category}_6가지_팩터순위합계", extracted_data.copy()),
            filter_data.filtering_value_factor2(f"{category}_12가지_팩터순위합계", extracted_data.copy()),
            filter_data.filtering_value_factor_upgrade(f"{category}_강환국_슈퍼가치전략_업글", extracted_data.copy()),

            ("Extracted_RAW_Data", extracted_data),
            ("RAW_Data", raw_data)
        ]
    )

def craw_and_process(choice=None):

    start = time.time()
    sleep_time = 60

    while True:
        try:
            if choice is None:
                choice = int(
                    input("소형주: 1 / 대형주: 2 / KOSPI200: 3 "
                          "/ KOSDAQ150 : 4 / KRX300 : 5 / TEST: 6 / 번호를 입력하세요 => "))

            extractor = Extract()

            # calling kospi and kosdaq data using pykrx and OpenFinanceReader
            kospi_kosdaq_data = extractor.get_data()

            print("--------------")

            # extract and calculating finance data recent 3 years data

            if choice == 1:
                print("소형주 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(1, kospi_kosdaq_data)
                )
                export_data("소형주", kospi_kosdaq_data, extracted_data)
            elif choice == 2:
                print("대형주 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(2, kospi_kosdaq_data)
                )
                export_data("대형주", kospi_kosdaq_data, extracted_data)

            elif choice == 3:
                print("KOSPI200 구성종목 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(3, kospi_kosdaq_data)
                )
                export_data("KOSPI200", kospi_kosdaq_data, extracted_data)

            elif choice == 4:
                print("KOSDAQ150 구성종목 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(4, kospi_kosdaq_data)
                )
                export_data("KOSDAQ150", kospi_kosdaq_data, extracted_data)

            elif choice == 5:
                print("KRX300 구성종목 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(5, kospi_kosdaq_data)
                )
                export_data("KRX300", kospi_kosdaq_data, extracted_data)

            elif choice == 6:
                print("TEST로 삼성전자의 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(6, kospi_kosdaq_data)
                )
                export_data("TEST", kospi_kosdaq_data, extracted_data)

            else:
                print("올바르지 않은 번호를 입력했습니다. 프로그램을 종료합니다.")
                exit()

            # If the execution reaches this point without errors, break the loop
            break

        except Exception as e:
            print(f"현재시간: {datetime.datetime.now()}")
            print(f"에러 발생으로 {sleep_time/60}분 만큼 대기 시작: {e}")
            time.sleep(sleep_time * 2)

    end = time.time()
    sec = (end - start)

    result_list = str(datetime.timedelta(seconds=sec)).split(".")
    print(f"Total extracting time: {result_list[0]} ---------------------")

if __name__ == "__main__":
    craw_and_process()
