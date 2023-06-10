import time
import stock.filter_data as filter_data
from stock.extract_data.extract import Extract
import datetime
from library.many_sheets_export import complex_export_data, make_file_path
from export_data.export_to_excel import ExportToData

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

def craw_and_process(choice=None):
    this_year = datetime.datetime.now().year
    years = [this_year - 2, this_year - 1, this_year]

    start = time.time()
    sleep_time = 60
    try_count = 0

    while True:
        try:
            if choice is None:
                choice = int(
                    input("소형주: 1 / 대형주: 2 / KOSPI200: 3 "
                          "/ KOSDAQ150 : 4 / KRX300 : 5 / TEST: 6 => "))

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
                complex_export_data("소형주", kospi_kosdaq_data, extracted_data)
            elif choice == 2:
                print("대형주 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(2, kospi_kosdaq_data)
                )
                complex_export_data("대형주", kospi_kosdaq_data, extracted_data)

            elif choice == 3:
                print("KOSPI200 구성종목 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(3, kospi_kosdaq_data)
                )
                complex_export_data("KOSPI200", kospi_kosdaq_data, extracted_data)

            elif choice == 4:
                print("KOSDAQ150 구성종목 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(4, kospi_kosdaq_data)
                )
                complex_export_data("KOSDAQ150", kospi_kosdaq_data, extracted_data)

            elif choice == 5:
                print("KRX300 구성종목 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filterging_data(5, kospi_kosdaq_data)
                )
                complex_export_data("KRX300", kospi_kosdaq_data, extracted_data)

            elif choice == 6:
                print("TEST로 삼성전자의 스크래핑을 시작합니다 -------")
                extracted_data = extractor.extract_finance_data(
                    years,
                    filter_data.filtering_data_that_specific_data(
                        # ['316140', '086790', '017670'],
                        ['005930'],
                        kospi_kosdaq_data
                    )
                )
                complex_export_data("TEST_1", kospi_kosdaq_data, extracted_data)

                file_path = make_file_path("TEST_2")

                exporter = ExportToData()
                exporter.export_to_excel(
                    file_path,
                    "specific_data",
                    extracted_data
                )

            else:
                print("올바르지 않은 번호를 입력했습니다. 프로그램을 종료합니다.")
                exit()

            # If the execution reaches this point without errors, break the loop
            break

        except Exception as e:
            print(f"현재시간 => {datetime.datetime.now()}")
            print(f"크롤링 반복횟수: {try_count}회 (0회가 최초 반복의 시작점)")
            print(f"에러 발생으로 {int(sleep_time / 60)}분 만큼 대기 시작: {e}")
            time.sleep(sleep_time)
            try_count += 1
            sleep_time *= 2

    end = time.time()
    sec = (end - start)

    result_list = str(datetime.timedelta(seconds=sec)).split(".")
    print(f"\n현재시간 => {datetime.datetime.now()}")
    print(f"크롤링 반복횟수: {try_count}회 (0회일 경우 에러 없이 크롤링 성공)")
    print(f"Total extracting time: {result_list[0]} ---------------------")
