import os
import datetime
import time
from export_data import ExportToData
from stock.extract_data.extract import Extract
from pystocklib.common import *

def calculate_company_value(net_worth, roe, k, discount_roe=1.0):   # net_worth: 순자산, roe:3년 가중평균 roe, k: BBB- 회사채 금리
    if discount_roe == 1.0:
        # 기업가치 = 자기자본 + (초과이익 / 할인율)
        # 초과이익 = 자기자본 x (가중평균 ROE - 할인율)
        value = net_worth + (net_worth * (roe - k)) / k
    else:
        excess_earning = net_worth * (roe - k) * 0.01
        mul = discount_roe / (1.0 + k * 0.01 - discount_roe)
        value = net_worth + excess_earning * mul

    return value

def make_acode(code):
    '''
    generate acode such as A005930, A000020
    :param code:
    :return: acode
    '''
    acode = None
    if len(code) == 6:
        acode = 'A' + code
    elif len(code) == 7:
        acode = 'A' + code[1:]
    return acode

def get_net_worth(code):
    acode = make_acode(code)
    url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode={acode}"
    selector = "#highlight_D_A > table > tbody > tr:nth-child(10) > td:nth-child(4)"
    ret = get_element_by_css_selector(url, selector)

    # 스크래핑 테스트 시 주석 해제
    # print(f"지배주주자본: {ret}")

    try:
        return ret * 100000000
    except:
        return 0

def get_roe(code):
    acode = make_acode(code)
    url = f"http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode={acode}"
    selector = "#highlight_D_A > table > tbody > tr:nth-child(18) > td"
    tags = get_elements_by_css_selector(url, selector)
    vals = [tag.text for tag in tags]

    roes = []
    for x in vals:
        try:
            x = x.replace(',', '')
            roes.append(float(x))
        except:
            roes.append(0)
    roe3 = roes[:3]

    # 스크래핑 테스트 시 주석 해제
    # print(f"최근 3년 ROE: {roe3}")

    # 기존 제작자 이상한 코드 주석처리
    # if roe3[0] <= roe3[1] <= roe3[2] or roe3[0] >= roe3[1] >= roe3[2]:
    #     roe = roe3[2]
    # else:
    roe = (roe3[0] + roe3[1] * 2 + roe3[2] * 3) / 6     # weighting average

    return roe

def update_and_export_srim_data(BBB_5):

    start = time.time()

    print("--------------")
    print("S-RIM Data 스크래핑을 시작합니다 -------")

    cache_file_path = "./stock/crawling_data/net_worth_roe_cache.pkl"

    # Load cache file if it exists
    cache_data = {}
    if os.path.isfile(cache_file_path):
        try:
            cache_data = pd.read_pickle(cache_file_path)
        except:
            cache_data = {}

    exporter = ExportToData()

    extractor = Extract()
    kospi_data = extractor.factor_data.get_stock_ticker_and_name_list("KOSPI")
    kosdaq_data = extractor.factor_data.get_stock_ticker_and_name_list("KOSDAQ")

    kospi_kosdaq_data = pd.concat([kospi_data, kosdaq_data])

    net_worth_and_roe_list = kospi_kosdaq_data[["종목코드"]]
    net_worth_and_roe_list.reset_index(drop=True, inplace=True)
    require_rate_of_return = [1.0, 0.9, 0.8]

    for i in range(len(net_worth_and_roe_list)):
        print(f'{net_worth_and_roe_list.loc[i, "종목코드"]}, {i + 1}/{len(net_worth_and_roe_list.index.values.tolist())}')

        s_rim_values = []

        stock_code = net_worth_and_roe_list.loc[i, "종목코드"]

        if (stock_code in cache_data
            and cache_data[stock_code]["net_worth"] is not None
            and cache_data[stock_code]["net_worth"] != 0
            and cache_data[stock_code]["roe"] is not None
            and cache_data[stock_code]["roe"] != 0
        ):
            # Use cached data if available
            net_worth = cache_data[stock_code]["net_worth"]
            roe = cache_data[stock_code]["roe"]

        else:
            # Fetch data using pystocklib.srim
            try:
                net_worth = get_net_worth(stock_code)
            except:
                net_worth = 0

            try:
                roe = get_roe(stock_code)
            except:
                roe = 0

            # Update cache
            cache_data[stock_code] = {"net_worth": net_worth, "roe": roe}
            pd.to_pickle(cache_data, cache_file_path)

        for discount_roe in require_rate_of_return:
            s_rim_values.append(calculate_company_value(net_worth, roe, BBB_5, discount_roe))

        net_worth_and_roe_list = net_worth_and_roe_list.copy()

        net_worth_and_roe_list.at[i, "net_worth"] = net_worth
        net_worth_and_roe_list.at[i, "average_roe"] = roe
        net_worth_and_roe_list.at[i, "s-rim_value_1"] = s_rim_values[0]
        net_worth_and_roe_list.at[i, "s-rim_value_2"] = s_rim_values[1]
        net_worth_and_roe_list.at[i, "s-rim_value_3"] = s_rim_values[2]

    folder_path = "./stock/crawling_data"
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, "net_worth_and_roe_list_for_s_rim.xlsx")

    # Check if file already exists and delete it
    if os.path.isfile(file_path):
        os.remove(file_path)
        print("기존 net_worth_and_roe_list_for_s_rim.xlsx 파일 삭제하고 새로 생성")

    exporter.export_to_excel(file_path, "s_rim", net_worth_and_roe_list)

    # Delete cache file after exporting to Excel
    if os.path.isfile(cache_file_path):
        os.remove(cache_file_path)
        print("사용 완료된 캐시 파일 삭제")

    end = time.time()
    sec = (end - start)

    result_list = str(datetime.timedelta(seconds=sec)).split(".")
    print(f"\nTotal extracting time: {result_list[0]} ---------------------")
