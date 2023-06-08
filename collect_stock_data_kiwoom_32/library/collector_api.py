from collections import OrderedDict
from sqlalchemy import Integer, Text, String
import numpy
import pathlib
from library.open_api import *
import os
import time
from PyQt5.QtWidgets import *
from library.daily_buy_list import *
from pandas import DataFrame

ver = "#version 1.5.0"
print(f"collector_api Version: {ver}")

MARKET_KOSPI = 0
MARKET_KOSDAQ = 10

# 콜렉팅에 사용되는 메서드를 모아 놓은 클래스
class collector_api():
    def __init__(self):
        self.open_api = open_api()
        self.engine_JB = self.open_api.engine_JB
        self.variable_setting()

    def variable_setting(self):
        self.open_api.py_gubun = "collector"
        self.dc = daily_crawler(self.open_api.cf.real_db_name, self.open_api.cf.real_daily_craw_db_name,
                                self.open_api.cf.real_daily_buy_list_db_name)
        self.dbl = daily_buy_list()

    # 콜렉팅을 실행하는 함수
    def code_update_check(self):
        logger.debug("code_update_check 함수에 들어왔습니다.")
        sql = "select code_update,jango_data_db_check, possessed_item, today_profit, final_chegyul_check, db_to_buy_list,today_buy_list, daily_crawler, daily_buy_list from setting_data limit 1"

        rows = self.engine_JB.execute(sql).fetchall()

        # stock_item_all(kospi,kosdaq,konex)
        # kospi(stock_kospi), kosdaq(stock_kosdaq), konex(stock_konex)
        # 관리종목(stock_managing), 불성실법인종목(stock_insincerity) 업데이트
        if rows[0][0] != self.open_api.today: # 오늘 날짜와 DB마지막 날짜 비교해서 오늘 날짜와 다르면 아래코드 실행
            self.get_code_list()  # KOSPI, KOSDAQ, KONEX 리스트를 API 통해서 DB 업데이트

        # daily_craw db 업데이트
        if rows[0][7] != self.open_api.today:
            self.daily_crawler_check()

        logger.debug("Collecting 작업을 모두 정상적으로 마쳤습니다.")

    def db_to_daily_craw(self):
        logger.debug("db_to_daily_craw 함수에 들어왔습니다!")
        sql = "select code,code_name, check_daily_crawler from stock_item_all"

        # 데이타 Fetch
        # rows 는 list안에 튜플이 있는 [()] 형태로 받아온다

        target_code = self.open_api.engine_daily_buy_list.execute(sql).fetchall()
        num = len(target_code)
        # mark = ".KS"
        sql = "UPDATE stock_item_all SET check_daily_crawler='%s' WHERE code='%s'"

        for i in range(num):
            # check_daily_crawler 확인 후 1, 3이 아닌 경우만 업데이트
            # (1: 금일 콜렉팅 완료, 3:과거에 이미 콜렉팅 완료, 0: 콜렉팅 전, 4: 액면분할, 증자 등으로 인한 업데이트 필요)
            if int(target_code[i][2]) in (1, 3):
                continue

            code = target_code[i][0]
            code_name = target_code[i][1]

            logger.debug("++++++++++++++" + str(code_name) + "++++++++++++++++++++" + str(i + 1) + '/' + str(num))

            check_item_gubun = self.set_daily_crawler_table(code, code_name)

            self.open_api.engine_daily_buy_list.execute(sql % (check_item_gubun, code))

    def daily_crawler_check(self):
        self.db_to_daily_craw()
        logger.debug("daily_crawler success !!!")

        sql = "UPDATE setting_data SET daily_crawler='%s' limit 1"
        self.engine_JB.execute(sql % (self.open_api.today))

    def _stock_to_sql(self, origin_df, type):
        checking_stocks = ['kosdaq', 'kospi', 'konex', 'etf']
        stock_df = DataFrame()
        stock_df['code'] = origin_df['code']
        name_list = []
        for KIND_info in origin_df.itertuples():
            kiwoom_name = self.open_api.dynamicCall("GetMasterCodeName(QString)", KIND_info.code).strip()
            name_list.append(kiwoom_name)
            if not kiwoom_name:
                if type in checking_stocks:
                    logger.error(
                        f"종목명이 비어있습니다. - "
                        f"종목: {KIND_info.code_name}, "
                        f"코드: {KIND_info.code}"
                    )

        stock_df['code_name'] = name_list
        stock_df['check_item'] = 0
        if type in checking_stocks:
            stock_df = stock_df[stock_df['code_name'].map(len) > 0]

        if type == 'item_all':
            stock_df['check_daily_crawler'] = "0"

        dtypes = dict(zip(list(stock_df.columns), [Text] * len(stock_df.columns)))  # 모든 타입을 Text로
        dtypes['check_item'] = Integer  # check_item만 int로 변경

        if len(stock_df) > 0:
            stock_df.to_sql(f'stock_{type}', self.open_api.engine_daily_buy_list, if_exists='replace', dtype=dtypes)
        else:  # insincerity와 managing이 비어있는 경우
            stock_df.to_sql(f'stock_{type}', self.open_api.engine_daily_buy_list, if_exists='replace', dtype=dtypes, index=False)
        return stock_df

    # 종목코드에 숫자가 아닌 타입이 포함되어 있는 경우 해당되는 종목 제거
    def remove_code_included_char(self, df):
        return df.drop(list(df.loc[~df['code'].astype(str).str.isdigit(), 'code'].index))

    def get_code_list(self):
        # 아래 부분은 영상 촬영 후 좀 더 효율적으로 업그레이드 되었으므로 강의 영상속의 코드와 다를 수 있습니다.

        # ### KIND 사이트에서 종목 데이터 가져오는 버전 ###
        # <KIND version start------------------------------------------------------------------------------------------>
        self.dc.cc.get_item()
        self.dc.cc.get_item_kospi()
        self.dc.cc.get_item_kosdaq()
        self.dc.cc.get_item_managing()
        self.dc.cc.get_item_insincerity()

        # OrderedDict를 사용해 순서 보장
        stock_data = OrderedDict(
            kospi=self.dc.cc.code_df_kospi,
            kosdaq=self.dc.cc.code_df_kosdaq,
            insincerity=self.dc.cc.code_df_insincerity,
            managing=self.dc.cc.code_df_managing
        )
        # <KIND version end------------------------------------------------------------------------------------------>

        if cf.use_etf:
            stock_data['etf'] = self.remove_code_included_char(DataFrame([(c, '') for c in self._get_code_list_by_market(8) if c],
                                                                         columns=['code', 'code_name']))

        for _type, data in stock_data.items():
            stock_data[_type] = self._stock_to_sql(data, _type)

        # stock_insincerity와 stock_managing의 종목은 따로 중복하여 넣지 않음
        excluded_tables = ['insincerity', 'managing']
        stock_item_all_df = pd.concat(
            [v[v['code_name'].map(len) > 0] for k, v in stock_data.items() if k not in excluded_tables],
            ignore_index=True
        ).drop_duplicates(subset=['code', 'code_name'])
        self._stock_to_sql(stock_item_all_df, "item_all")

        sql = "UPDATE setting_data SET code_update='%s' limit 1"
        self.engine_JB.execute(sql % (self.open_api.today))

    def _get_code_list_by_market(self, market_num):
        codes = self.open_api.dynamicCall(f'GetCodeListByMarket("{market_num}")')
        return codes.split(';')

    def set_daily_crawler_table(self, code, code_name):
        df = self.open_api.get_total_data(code, code_name, self.open_api.today)
        if len(df) == 0:
            return 1
        oldest_row = df.iloc[-1]
        check_row = None
        deleted = False
        diff = False  # True 인 경우 수정주가 반영하여 업데이트

        # daily_buy_list 테이블 리스트를 추출
        dbl_dates = self.open_api.engine_daily_buy_list.execute("""
                SELECT table_name as tname FROM information_schema.tables 
                WHERE table_schema ='daily_buy_list' AND table_name REGEXP '[0-9]{8}'
            """).fetchall()

        check_daily_crawler_sql = """
            UPDATE daily_buy_list.stock_item_all SET check_daily_crawler = '4' WHERE code = '{}'
        """

        if self.open_api.engine_daily_craw.dialect.has_table(self.open_api.engine_daily_craw, code_name):
            check_row = self.open_api.engine_daily_craw.execute(f"""
                SELECT * FROM `{code_name}` WHERE date = '{oldest_row['date']}' LIMIT 1
            """).fetchall()

            # daily_buy_list 에 저장 된 주가와 daily_craw에 저장 된 주가가 다른 경우 diff를 True로 변경해서 업데이트
            if dbl_dates:
                if dbl_dates[0][0] > oldest_row['date']: #daily_buy_list 의 날짜 테이블 중 가장 과거의 날짜테이블이 API로 부터 받는 oldest_row 보다 더 최근 날짜이면
                    search_date = dbl_dates[0][0]
                else:
                    search_date = oldest_row['date']

                dc_item = self.open_api.engine_daily_craw.execute(f"""
                                SELECT date, close FROM `{code_name}` WHERE date >= '{search_date}' ORDER BY date asc limit 1
                            """).first() # daily_craw 종목테이블에서 search_date 보다는 과거 데이터이고 가장 오래된 row를 찾는다.
                if dc_item:
                    dc_date, dc_close = dc_item
                    if self.open_api.engine_daily_buy_list.dialect.has_table(self.open_api.engine_daily_buy_list, dc_date):
                        dbl_close = self.engine_JB.execute(f"""
                            SELECT close FROM daily_buy_list.`{dc_date}` WHERE code = '{code}'
                        """).fetchall()
                        if dbl_close:
                            if dbl_close[0][0] == dc_close:  # daily_craw, daily_buy_list 의 close 값이 같은 경우
                                diff = False
                            else:  # daily_craw, daily_buy_list 의 close 가 다른 경우
                                diff = True
                        else:  # daily_buy_list 날짜 테이블에 해당 종목이 없는 경우
                            diff = True
                    else:
                        diff = False  # daily_buy_list를 해당 날짜까지 아직 생성하지 못한 경우, 어차피 날짜테이블은 없으면 다시 생성한다. 비교대상이 없으므로 False
                else:
                    diff = True # 분할 재상장 하는 경우 (ex. F&F) daily_buy_list에 분할재상장 이전 데이터가 있을 수 있다. -> 삭제 후 다시 받도록
            else:
                diff = False # daily_buy_list에 아무런 날짜 테이블이 없는 경우 (처음 콜렉팅을 하는 경우)
        else:
            self.engine_JB.execute(check_daily_crawler_sql.format(code))
            deleted = True

        if (check_row and (check_row[0]['close'] != oldest_row['close'])) or diff:
            logger.info(f'{code} {code_name}의 액면분할/증자 등의 이유로 수정주가가 달라져서 처음부터 다시 콜렉팅')
            # daily_craw 삭제
            logger.info('daily_craw 삭제 중..')
            commands = [
                f'DROP TABLE IF EXISTS daily_craw.`{code_name}`',
            ]

            for com in commands:
                self.open_api.engine_daily_buy_list.execute(com)
            logger.info('삭제 완료')
            df = self.open_api.get_total_data(code, code_name, self.open_api.today)
            self.engine_JB.execute(check_daily_crawler_sql.format(code))
            deleted = True

        check_daily_crawler = self.engine_JB.execute(f"""
            SELECT check_daily_crawler FROM daily_buy_list.stock_item_all WHERE code = '{code}'
        """).fetchall()[0].check_daily_crawler

        df_temp = DataFrame(df,
                            columns=['date', 'check_item', 'code', 'code_name', 'd1_diff_rate', 'close', 'open', 'high',
                                     'low',
                                     'volume', 'clo5', 'clo10', 'clo20', 'clo40', 'clo60', 'clo80',
                                     'clo100', 'clo120', "clo5_diff_rate", "clo10_diff_rate",
                                     "clo20_diff_rate", "clo40_diff_rate", "clo60_diff_rate",
                                     "clo80_diff_rate", "clo100_diff_rate", "clo120_diff_rate",
                                     'yes_clo5', 'yes_clo10', 'yes_clo20', 'yes_clo40', 'yes_clo60', 'yes_clo80',
                                     'yes_clo100', 'yes_clo120',
                                     'vol5', 'vol10', 'vol20', 'vol40', 'vol60', 'vol80',
                                     'vol100', 'vol120'
                                     ])

        df_temp = df_temp.sort_values(by=['date'], ascending=True)
        # df_temp = df_temp[1:]

        df_temp['code'] = code
        df_temp['code_name'] = code_name
        df_temp['d1_diff_rate'] = round(
            (df_temp['close'] - df_temp['close'].shift(1)) / df_temp['close'].shift(1) * 100, 2)

        # 하나씩 추가할때는 append 아니면 replace
        clo5 = df_temp['close'].rolling(window=5).mean()
        clo10 = df_temp['close'].rolling(window=10).mean()
        clo20 = df_temp['close'].rolling(window=20).mean()
        clo40 = df_temp['close'].rolling(window=40).mean()
        clo60 = df_temp['close'].rolling(window=60).mean()
        clo80 = df_temp['close'].rolling(window=80).mean()
        clo100 = df_temp['close'].rolling(window=100).mean()
        clo120 = df_temp['close'].rolling(window=120).mean()
        df_temp['clo5'] = clo5
        df_temp['clo10'] = clo10
        df_temp['clo20'] = clo20
        df_temp['clo40'] = clo40
        df_temp['clo60'] = clo60
        df_temp['clo80'] = clo80
        df_temp['clo100'] = clo100
        df_temp['clo120'] = clo120

        df_temp['clo5_diff_rate'] = round((df_temp['close'] - clo5) / clo5 * 100, 2)
        df_temp['clo10_diff_rate'] = round((df_temp['close'] - clo10) / clo10 * 100, 2)
        df_temp['clo20_diff_rate'] = round((df_temp['close'] - clo20) / clo20 * 100, 2)
        df_temp['clo40_diff_rate'] = round((df_temp['close'] - clo40) / clo40 * 100, 2)
        df_temp['clo60_diff_rate'] = round((df_temp['close'] - clo60) / clo60 * 100, 2)
        df_temp['clo80_diff_rate'] = round((df_temp['close'] - clo80) / clo80 * 100, 2)
        df_temp['clo100_diff_rate'] = round((df_temp['close'] - clo100) / clo100 * 100, 2)
        df_temp['clo120_diff_rate'] = round((df_temp['close'] - clo120) / clo120 * 100, 2)

        df_temp['yes_clo5'] = df_temp['clo5'].shift(1)
        df_temp['yes_clo10'] = df_temp['clo10'].shift(1)
        df_temp['yes_clo20'] = df_temp['clo20'].shift(1)
        df_temp['yes_clo40'] = df_temp['clo40'].shift(1)
        df_temp['yes_clo60'] = df_temp['clo60'].shift(1)
        df_temp['yes_clo80'] = df_temp['clo80'].shift(1)
        df_temp['yes_clo100'] = df_temp['clo100'].shift(1)
        df_temp['yes_clo120'] = df_temp['clo120'].shift(1)

        df_temp['vol5'] = df_temp['volume'].rolling(window=5).mean()
        df_temp['vol10'] = df_temp['volume'].rolling(window=10).mean()
        df_temp['vol20'] = df_temp['volume'].rolling(window=20).mean()
        df_temp['vol40'] = df_temp['volume'].rolling(window=40).mean()
        df_temp['vol60'] = df_temp['volume'].rolling(window=60).mean()
        df_temp['vol80'] = df_temp['volume'].rolling(window=80).mean()
        df_temp['vol100'] = df_temp['volume'].rolling(window=100).mean()
        df_temp['vol120'] = df_temp['volume'].rolling(window=120).mean()

        # 여기 이렇게 추가해야함
        if self.open_api.engine_daily_craw.dialect.has_table(self.open_api.engine_daily_craw, code_name):
            df_temp = df_temp[df_temp.date > self.open_api.get_daily_craw_db_last_date(code_name)]

        if len(df_temp) == 0 and check_daily_crawler != '4':
            logger.debug("이미 daily_craw db의 " + code_name + " 테이블에 콜렉팅 완료 했다! df_temp가 비었다!!")

            # 이렇게 안해주면 아래 프로세스들을 안하고 바로 넘어가기때문에 그만큼 tr 조회 하는 시간이 짧아지고 1초에 5회 이상의 조회를 할 수 가있다 따라서 비었을 경우는 sleep해줘야 안멈춘다
            time.sleep(0.03)
            check_item_gubun = 3
            return check_item_gubun

        df_temp[['close', 'open', 'high', 'low', 'volume', 'clo5', 'clo10', 'clo20', 'clo40', 'clo60',
                 'clo80', 'clo100', 'clo120',
                 'yes_clo5', 'yes_clo10', 'yes_clo20', 'yes_clo40', 'yes_clo60', 'yes_clo80', 'yes_clo100',
                 'yes_clo120',
                 'vol5', 'vol10', 'vol20', 'vol40', 'vol60', 'vol80', 'vol100', 'vol120']] = \
            df_temp[
                ['close', 'open', 'high', 'low', 'volume', 'clo5', 'clo10', 'clo20', 'clo40', 'clo60',
                 'clo80', 'clo100', 'clo120',
                 'yes_clo5', 'yes_clo10', 'yes_clo20', 'yes_clo40', 'yes_clo60', 'yes_clo80', 'yes_clo100',
                 'yes_clo120',
                 'vol5', 'vol10', 'vol20', 'vol40', 'vol60', 'vol80', 'vol100', 'vol120']].fillna(0).astype(int)

        # inf 를 NaN으로 변경 (inf can not be used with MySQL 에러 방지)
        df_temp = df_temp.replace([numpy.inf, -numpy.inf], numpy.nan)

        df_temp.to_sql(name=code_name, con=self.open_api.engine_daily_craw, if_exists='append')
        index_name = ''.join(c for c in code_name if c.isalnum())
        if deleted:
            try:
                self.open_api.engine_daily_craw.execute(f"""
                    CREATE INDEX ix_{index_name}_date
                    ON daily_craw.`{code_name}` (date(8)) 
                """)
            except Exception:
                pass

        # check_daily_crawler 가 4 인 경우는 액면분할, 증자 등으로 인해 daily_buy_list 업데이트를 해야하는 경우
        if check_daily_crawler == '4':
            logger.info(f'daily_craw.{code_name} 업데이트 완료 {code}')
            logger.info('daily_buy_list 업데이트 중..')


            for row in dbl_dates:
                logger.info(f'{code} {code_name} - daily_buy_list.`{row.tname}` 업데이트')
                try:
                    new_data = df_temp[df_temp.date == row.tname]
                except KeyError:
                    continue
                if self.open_api.engine_daily_craw.dialect.has_table(self.open_api.engine_daily_buy_list, row.tname):
                    self.open_api.engine_daily_buy_list.execute(f"""
                        DELETE FROM `{row.tname}` WHERE code = '{code}'
                    """)
                    if not new_data.empty:
                        new_data.set_index('code')
                        new_data.to_sql(
                            name=row.tname,
                            con=self.open_api.engine_daily_buy_list,
                            index=True,
                            if_exists='append',
                            dtype={'code': String(6)}
                        )

            logger.info('daily_buy_list 업데이트 완료')

        check_item_gubun = 1
        return check_item_gubun
