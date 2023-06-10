import time
from stock.extract_data.extract import Extract
import datetime
from library.many_sheets_export import simple_export_data

def craw_and_process():

    start = time.time()
    sleep_time = 60
    try_count = 0

    while True:
        try:
            extractor = Extract()

            # calling kospi and kosdaq data using pykrx and OpenFinanceReader
            kospi_kosdaq_data = extractor.get_data()

            print("--------------")
            print("스크래핑을 시작합니다 -------")

            simple_export_data(kospi_kosdaq_data)

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
