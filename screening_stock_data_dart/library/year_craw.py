import time
from stock.extract_data.extract import Extract
import datetime
from library.many_sheets_export import simple_export_data

def craw_and_process():

    start = time.time()

    print("--------------")
    print("스크래핑을 시작합니다 -------")

    extractor = Extract()

    # calling kospi and kosdaq data using pykrx and OpenFinanceReader
    kospi_kosdaq_data = extractor.get_data()

    simple_export_data(kospi_kosdaq_data)

    end = time.time()
    sec = (end - start)

    result_list = str(datetime.timedelta(seconds=sec)).split(".")
    print(f"\n현재시간 => {datetime.datetime.now()}")
    print(f"Total extracting time: {result_list[0]} ---------------------")
