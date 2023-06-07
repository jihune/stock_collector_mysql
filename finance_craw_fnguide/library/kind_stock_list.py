import pandas as pd

def collect_krx_300_list():
    data = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=17', header=0)[0]

    data['종목코드'] = data.종목코드.map('{:06d}'.format)
    data = data[['종목코드', '회사명']]

    code_list = data['종목코드'].tolist()
    name_list = data['회사명'].tolist()

    # KRX300 상장종목 전체
    tickers = dict(list(zip(code_list, name_list)))

    if 'tick' in tickers:
        print('tick')

    return tickers
