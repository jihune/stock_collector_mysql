import pandas as pd

def collect_stock_list():
    data = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]

    data['종목코드'] = data.종목코드.map('{:06d}'.format)
    data = data[['종목코드', '회사명']]

    code_list = data['종목코드'].tolist()
    name_list = data['회사명'].tolist()

    # 상장종목 전체에 대한 tickers
    tickers = dict(list(zip(code_list, name_list)))

    return tickers

def collect_many_stock_list():
    kospi200_data = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=06', header=0)[0]
    kosdaq150_data = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=16', header=0)[0]
    krx300_data = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=17', header=0)[0]

    # 합치기
    data = pd.concat([kospi200_data, kosdaq150_data, krx300_data])

    # 중복 행 제거
    data.drop_duplicates(inplace=True)

    data['종목코드'] = data.종목코드.map('{:06d}'.format)
    data = data[['종목코드', '회사명']]

    code_list = data['종목코드'].tolist()
    name_list = data['회사명'].tolist()

    # KOSPI200, KOSDAQ, KRX300 상장종목 전체
    tickers = dict(list(zip(code_list, name_list)))

    code_list_last_index = len(code_list) - 1
    print(f"\n수집할 종목에 대한 리스트를 최신화 했습니다.")
    print(f"재무제표를 수집할 종목은 총 {code_list_last_index}개 입니다.")

    return tickers
