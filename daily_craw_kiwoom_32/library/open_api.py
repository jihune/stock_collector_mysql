from functools import partial

ver = "#version 1.3.15"
print(f"open_api Version: {ver}")

from library.simulator_func_mysql import *
import datetime
import sys
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
from library import cf
from collections import defaultdict

import warnings
warnings.simplefilter(action='ignore', category=UserWarning)
from pandas import DataFrame
import re
import pandas as pd
import os

from sqlalchemy import create_engine, event, Text, Float
from sqlalchemy.pool import Pool

import pymysql

pymysql.install_as_MySQLdb()
TR_REQ_TIME_INTERVAL = 0.5
code_pattern = re.compile(r'\d{6}')  # 숫자 6자리가 연속으로오는 패턴


def escape_percentage(conn, clauseelement, multiparams, params):
    # execute로 실행한 sql문이 들어왔을 때 %를 %%로 replace
    if isinstance(clauseelement, str) and '%' in clauseelement and multiparams is not None:
        while True:
            replaced = re.sub(r'([^%])%([^%s])', r'\1%%\2', clauseelement)
            if replaced == clauseelement:
                break
            clauseelement = replaced

    return clauseelement, multiparams, params


def setup_sql_mod(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET sql_mode = ''")


event.listen(Pool, 'connect', setup_sql_mod)
event.listen(Pool, 'first_connect', setup_sql_mod)


class RateLimitExceeded(Exception):
    pass


def timedout_exit(widget):
    logger.debug("서버로 부터 응답이 없어 프로그램을 종료합니다.")
    widget.clear()
    time.sleep(3)
    sys.exit(-1)


class open_api(QAxWidget):
    def __init__(self):
        super().__init__()

        # openapi 호출 횟수를 저장하는 변수
        self.rq_count = 0
        self.date_setting()
        self.tr_loop_count = 0
        self.call_time = datetime.datetime.now()
        # openapi연동
        self._create_open_api_instance()
        self._set_signal_slots()
        self.comm_connect()

        # 계좌 정보 가져오는 함수
        self.account_info()
        self.variable_setting()

        # open_api가 호출 되는 경우 (콜렉터, 모의투자, 실전투자) 의 경우는
        # 아래 simulator_func_mysql 클래스를 호출 할 때 두번째 인자에 real을 보낸다.
        self.sf = simulator_func_mysql(self.simul_num, 'real', self.db_name)
        logger.debug("self.sf.simul_num(알고리즘 번호) : %s", self.sf.simul_num)
        logger.debug("self.sf.db_to_realtime_daily_buy_list_num : %s", self.sf.db_to_realtime_daily_buy_list_num)
        logger.debug("self.sf.sell_list_num : %s", self.sf.sell_list_num)

        # 만약에 setting_data 테이블이 존재하지 않으면 구축 하는 로직
        if not self.sf.is_simul_table_exist(self.db_name, "setting_data"):
            self.init_db_setting_data()
        else:
            logger.debug("setting_data db 존재한다!!!")

        # 여기서 invest_unit 설정함
        self.sf_variable_setting()
        self.ohlcv = defaultdict(list)

    # 날짜 세팅
    def date_setting(self):
        self.today = datetime.datetime.today().strftime("%Y%m%d")
        self.today_detail = datetime.datetime.today().strftime("%Y%m%d%H%M")

    # invest_unit을 가져오는 함수
    def get_invest_unit(self):
        logger.debug("get_invest_unit 함수에 들어왔습니다!")
        sql = "select invest_unit from setting_data limit 1"
        # 데이타 Fetch
        # rows 는 list안에 튜플이 있는 [()] 형태로 받아온다
        return self.engine_JB.execute(sql).fetchall()[0][0]

    # simulator_func_mysql 에서 설정한 값을 가져오는 함수
    def sf_variable_setting(self):
        self.date_rows_yesterday = self.sf.get_recent_daily_buy_list_date()

        if not self.sf.is_simul_table_exist(self.db_name, "all_item_db"):
            logger.debug("all_item_db 없어서 생성!! init !! ")
            self.invest_unit = 0
            self.db_to_all_item(0, 0, 0, 0, 0)
            self.delete_all_item("0")

        # setting_data에 invest_unit값이 설정 되어 있는지 확인
        if not self.check_set_invest_unit():
            # setting_data에 invest_unit 값이 설정 되어 있지 않으면 세팅
            self.set_invest_unit()
        # setting_data에 invest_unit값이 설정 되어 있으면 해당 값을 가져온다.
        else:
            self.invest_unit = self.get_invest_unit()
            self.sf.invest_unit = self.invest_unit
        # setting_data에 invest_unit값이 설정 되어 있는지 확인 하는 함수

    # setting_data에 invest_unit값이 설정 되어 있는지 확인 하는 함수
    def check_set_invest_unit(self):
        sql = "select invest_unit, set_invest_unit from setting_data limit 1"
        rows = self.engine_JB.execute(sql).fetchall()
        if rows[0][1] == self.today:
            self.invest_unit = rows[0][0]
            return True
        else:
            return False

    # 매수 금액을 설정 하는 함수
    def set_invest_unit(self):
        self.get_d2_deposit()
        self.check_balance()
        self.total_invest = self.change_format(
            str(int(self.d2_deposit_before_format) + int(self.total_purchase_price)))

        # 이런식으로 변수에 값 할당
        self.invest_unit = self.sf.invest_unit
        sql = "UPDATE setting_data SET invest_unit='%s',set_invest_unit='%s' limit 1"
        self.engine_JB.execute(sql % (self.invest_unit, self.today))

    # 변수 설정 함수
    def variable_setting(self):
        logger.debug("variable_setting 함수에 들어왔다.")
        self.get_today_buy_list_code = 0
        self.cf = cf
        self.reset_opw00018_output()
        # 아래 분기문은 실전 투자 인지, 모의 투자 인지 결정
        if self.account_number == cf.real_account:  # 실전
            self.simul_num = cf.real_simul_num
            logger.debug("실전!@@@@@@@@@@@" + cf.real_account)
            self.db_name_setting(cf.real_db_name)
            # 실전과 모의투자가 다른 것은 아래 mod_gubun 이 다르다.
            # 금일 수익률 표시 하는게 달라서(중요X)
            self.mod_gubun = 100

        elif self.account_number == cf.imi1_accout:  # 모의1
            logger.debug("모의투자 1!!")
            self.simul_num = cf.imi1_simul_num
            self.db_name_setting(cf.imi1_db_name)
            self.mod_gubun = 1

        else:
            logger.debug("계정이 존재하지 않습니다!! library/cf.py 파일에 계좌번호를 입력해주세요!")
            exit(1)
        # 여기에 이렇게 true로 고정해놔야 exit check 할때 false 인 경우에 들어갔을 때  today_buy_code is null 이런 에러 안생긴다.
        self.jango_is_null = True

        self.py_gubun = False

    # 봇 데이터 베이스를 만드는 함수
    def create_database(self, cursor):
        logger.debug("create_database!!! {}".format(self.db_name))
        sql = 'CREATE DATABASE {}'
        cursor.execute(sql.format(self.db_name))

    # 봇 데이터 베이스 존재 여부 확인 함수
    def is_database_exist(self, cursor):
        sql = "SELECT 1 FROM Information_schema.SCHEMATA WHERE SCHEMA_NAME = '{}'"
        if cursor.execute(sql.format(self.db_name)):
            logger.debug("%s 데이터 베이스가 존재한다! ", self.db_name)
            return True
        else:
            logger.debug("%s 데이터 베이스가 존재하지 않는다! ", self.db_name)
            return False

    # db 세팅 함수
    def db_name_setting(self, db_name):
        self.db_name = db_name
        logger.debug("db name !!! : %s", self.db_name)
        conn = pymysql.connect(
            host=cf.db_ip,
            port=int(cf.db_port),
            user=cf.db_id,
            password=cf.db_passwd,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            if not self.is_database_exist(cursor):
                self.create_database(cursor)
            self.engine_JB = create_engine(
                "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/" + db_name,
                encoding='utf-8'
            )
            self.basic_db_check(cursor)

        conn.commit()
        conn.close()

        self.engine_craw = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/min_craw",
            encoding='utf-8')
        self.engine_daily_craw = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/daily_craw",
            encoding='utf-8')
        self.engine_daily_buy_list = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/daily_buy_list",
            encoding='utf-8')

        event.listen(self.engine_craw, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_daily_craw, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_daily_buy_list, 'before_execute', escape_percentage, retval=True)

    # 계좌 정보 함수
    def account_info(self):
        logger.debug("account_info 함수에 들어왔습니다!")
        account_number = self.get_login_info("ACCNO")
        self.account_number = account_number.split(';')[0]
        logger.debug("계좌번호 : " + self.account_number)

    # OpenAPI+에서 계좌 정보 및 로그인 사용자 정보를 얻어오는 메서드는 GetLoginInfo입니다.
    def get_login_info(self, tag):
        logger.debug("get_login_info 함수에 들어왔습니다!")
        try:
            ret = self.dynamicCall("GetLoginInfo(QString)", tag)
            # logger.debug(ret)
            return ret
        except Exception as e:
            logger.critical(e)

    def _create_open_api_instance(self):
        try:
            self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        except Exception as e:
            logger.critical(e)

    def _set_signal_slots(self):
        try:
            self.OnEventConnect.connect(self._event_connect)
            self.OnReceiveTrData.connect(self._receive_tr_data)
            self.OnReceiveMsg.connect(self._receive_msg)
            # 주문체결 시점에서 키움증권 서버가 발생시키는 OnReceiveChejanData 이벤트를 처리하는 메서드
            self.OnReceiveChejanData.connect(self._receive_chejan_data)


        except Exception as e:
            is_64bits = sys.maxsize > 2**32
            if is_64bits:
                logger.critical('현재 Anaconda는 64bit 환경입니다. 32bit 환경으로 실행하여 주시기 바랍니다.')
            else:
                logger.critical(e)

    def comm_connect(self):
        try:
            self.dynamicCall("CommConnect()")
            self.login_event_loop = QEventLoop()
            self.login_event_loop.exec_()
        except Exception as e:
            logger.critical(e)

    def _receive_msg(self, sScrNo, sRQName, sTrCode, sMsg):
        logger.debug("_receive_msg 함수에 들어왔습니다!")
        # logger.debug("sScrNo!!!")
        # logger.debug(sScrNo)
        # logger.debug("sRQName!!!")
        # logger.debug(sRQName)
        # logger.debug("sTrCode!!!")
        # logger.debug(sTrCode)
        # logger.debug("sMsg!!!")
        logger.debug(sMsg)

    def _event_connect(self, err_code):
        try:
            if err_code == 0:
                logger.debug("connected")
            else:
                logger.debug("disconnected")

            self.login_event_loop.exit()
        except Exception as e:
            logger.critical(e)

    def set_input_value(self, id, value):
        try:
            self.dynamicCall("SetInputValue(QString, QString)", id, value)
        except Exception as e:
            logger.critical(e)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.exit_check()
        ret = self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        if ret == -200:
            raise RateLimitExceeded('요청제한 횟수를 초과하였습니다.')

        self.call_time = datetime.datetime.now()

        if ret == 0:
            self.tr_event_loop = QEventLoop()
            self.tr_loop_count += 1
            # 영상 촬영 후 추가 된 코드입니다 (서버 응답이 늦을 시 예외 발생)
            self.timer = QTimer()
            self.timer.timeout.connect(partial(timedout_exit, self))
            self.timer.setSingleShot(True)
            self.timer.start(5000)
            #########################################################
            self.tr_event_loop.exec_()

    def _get_comm_data(self, code, field_name, index, item_name):
        # logger.debug('calling GetCommData...')
        # self.exit_check()
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)", code, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        try:
            ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            return ret
        except Exception as e:
            logger.critical(e)

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        # print("screen_no, rqname, trcode", screen_no, rqname, trcode)
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False
        # print("self.py_gubun!!", self.py_gubun)
        if rqname == "opt10081_req" and self.py_gubun == "trader":
            # logger.debug("opt10081_req trader!!!")
            # logger.debug("Get an item info !!!!")
            self._opt10081(rqname, trcode)
        elif rqname == "opt10081_req" and self.py_gubun == "collector":
            # logger.debug("opt10081_req collector!!!")
            # logger.debug("Get an item info !!!!")
            self.collector_opt10081(rqname, trcode)
        elif rqname == "opw00001_req":
            # logger.debug("opw00001_req!!!")
            # logger.debug("Get an de_deposit!!!")
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            # logger.debug("opw00018_req!!!")
            # logger.debug("Get the possessed item !!!!")
            self._opw00018(rqname, trcode)
        elif rqname == "opt10074_req":
            # logger.debug("opt10074_req!!!")
            # logger.debug("Get the profit")
            self._opt10074(rqname, trcode)
        elif rqname == "opw00015_req":
            # logger.debug("opw00015_req!!!")
            # logger.debug("deal list!!!!")
            self._opw00015(rqname, trcode)
        elif rqname == "opt10076_req":
            # logger.debug("opt10076_req")
            # logger.debug("chegyul list!!!!")
            self._opt10076(rqname, trcode)
        elif rqname == "opt10073_req":
            # logger.debug("opt10073_req")
            # logger.debug("Get today profit !!!!")
            self._opt10073(rqname, trcode)
        elif rqname == "opt10080_req":
            # logger.debug("opt10080_req!!!")
            # logger.debug("Get an de_deposit!!!")
            self._opt10080(rqname, trcode)
        elif rqname == "send_order_req":
            pass
        else:
            logger.debug(f'non existence code {rqname}, {trcode}')
        # except Exception as e:
        #     logger.critical(e)

        if rqname != 'send_order_req':
            self.tr_loop_count -= 1
        try:
            if self.tr_loop_count <= 0:
                self.tr_event_loop.exit()
                self.tr_loop_count = 0
        except AttributeError:
            pass

    # setting_data를 초기화 하는 함수
    def init_db_setting_data(self):
        logger.debug("init_db_setting_data !! ")

        #  추가하면 여기에도 추가해야함
        df_setting_data_temp = {'loan_money': [], 'limit_money': [], 'invest_unit': [], 'max_invest_unit': [],
                                'min_invest_unit': [],
                                'set_invest_unit': [], 'code_update': [], 'today_buy_stop': [],
                                'jango_data_db_check': [], 'possessed_item': [], 'today_profit': [],
                                'final_chegyul_check': [],
                                'db_to_buy_list': [], 'today_buy_list': [], 'daily_crawler': [],
                                'daily_buy_list': []}

        df_setting_data = DataFrame(df_setting_data_temp,
                                    columns=['loan_money', 'limit_money', 'invest_unit', 'max_invest_unit',
                                             'min_invest_unit',
                                             'set_invest_unit', 'code_update', 'today_buy_stop',
                                             'jango_data_db_check', 'possessed_item', 'today_profit',
                                             'final_chegyul_check',
                                             'db_to_buy_list', 'today_buy_list', 'daily_crawler',
                                             'daily_buy_list'])

        # 자료형
        df_setting_data.loc[0, 'loan_money'] = int(0)
        df_setting_data.loc[0, 'limit_money'] = int(0)
        df_setting_data.loc[0, 'invest_unit'] = int(0)
        df_setting_data.loc[0, 'max_invest_unit'] = int(0)
        df_setting_data.loc[0, 'min_invest_unit'] = int(0)

        df_setting_data.loc[0, 'set_invest_unit'] = str(0)
        df_setting_data.loc[0, 'code_update'] = str(0)
        df_setting_data.loc[0, 'today_buy_stop'] = str(0)
        df_setting_data.loc[0, 'jango_data_db_check'] = str(0)

        df_setting_data.loc[0, 'possessed_item'] = str(0)
        df_setting_data.loc[0, 'today_profit'] = str(0)
        df_setting_data.loc[0, 'final_chegyul_check'] = str(0)
        df_setting_data.loc[0, 'db_to_buy_list'] = str(0)
        df_setting_data.loc[0, 'today_buy_list'] = str(0)
        df_setting_data.loc[0, 'daily_crawler'] = str(0)
        df_setting_data.loc[0, 'min_crawler'] = str(0)
        df_setting_data.loc[0, 'daily_buy_list'] = str(0)

        df_setting_data.to_sql('setting_data', self.engine_JB, if_exists='replace')

    # all_item_db에 추가하는 함수
    def db_to_all_item(self, order_num, code, chegyul_check, purchase_price, rate):
        logger.debug("db_to_all_item 함수에 들어왔다!!!")
        self.date_setting()
        self.sf.init_df_all_item()
        self.sf.df_all_item.loc[0, 'order_num'] = order_num
        self.sf.df_all_item.loc[0, 'code'] = str(code)
        self.sf.df_all_item.loc[0, 'rate'] = float(rate)

        self.sf.df_all_item.loc[0, 'buy_date'] = self.today_detail
        # 사는 순간 chegyul_check 1 로 만드는거다.
        self.sf.df_all_item.loc[0, 'chegyul_check'] = chegyul_check
        # int로 넣어야 나중에 ++ 할수 있다.
        self.sf.df_all_item.loc[0, 'reinvest_date'] = '#'
        # df_all_item.loc[0, 'reinvest_count'] = int(0)
        # 다음에 투자할 금액은 invest_unit과 같은 금액이다.
        self.sf.df_all_item.loc[0, 'invest_unit'] = self.invest_unit
        # df_all_item.loc[0, 'reinvest_unit'] = self.invest_unit
        self.sf.df_all_item.loc[0, 'purchase_price'] = purchase_price

        # 신규 매수의 경우
        if order_num != 0:
            recent_daily_buy_list_date = self.sf.get_recent_daily_buy_list_date()
            if recent_daily_buy_list_date:
                df = self.sf.get_daily_buy_list_by_code(code, recent_daily_buy_list_date)
                if not df.empty:
                    self.sf.df_all_item.loc[0, 'code_name'] = df.loc[0, 'code_name']
                    self.sf.df_all_item.loc[0, 'close'] = df.loc[0, 'close']
                    self.sf.df_all_item.loc[0, 'open'] = df.loc[0, 'open']
                    self.sf.df_all_item.loc[0, 'high'] = df.loc[0, 'high']
                    self.sf.df_all_item.loc[0, 'low'] = df.loc[0, 'low']
                    self.sf.df_all_item.loc[0, 'volume'] = df.loc[0, 'volume']
                    self.sf.df_all_item.loc[0, 'd1_diff_rate'] = float(df.loc[0, 'd1_diff_rate'])
                    self.sf.df_all_item.loc[0, 'clo5'] = df.loc[0, 'clo5']
                    self.sf.df_all_item.loc[0, 'clo10'] = df.loc[0, 'clo10']
                    self.sf.df_all_item.loc[0, 'clo20'] = df.loc[0, 'clo20']
                    self.sf.df_all_item.loc[0, 'clo40'] = df.loc[0, 'clo40']
                    self.sf.df_all_item.loc[0, 'clo60'] = df.loc[0, 'clo60']
                    self.sf.df_all_item.loc[0, 'clo80'] = df.loc[0, 'clo80']
                    self.sf.df_all_item.loc[0, 'clo100'] = df.loc[0, 'clo100']
                    self.sf.df_all_item.loc[0, 'clo120'] = df.loc[0, 'clo120']

                    if df.loc[0, 'clo5_diff_rate'] is not None:
                        self.sf.df_all_item.loc[0, 'clo5_diff_rate'] = float(df.loc[0, 'clo5_diff_rate'])
                    if df.loc[0, 'clo10_diff_rate'] is not None:
                        self.sf.df_all_item.loc[0, 'clo10_diff_rate'] = float(df.loc[0, 'clo10_diff_rate'])
                    if df.loc[0, 'clo20_diff_rate'] is not None:
                        self.sf.df_all_item.loc[0, 'clo20_diff_rate'] = float(df.loc[0, 'clo20_diff_rate'])
                    if df.loc[0, 'clo40_diff_rate'] is not None:
                        self.sf.df_all_item.loc[0, 'clo40_diff_rate'] = float(df.loc[0, 'clo40_diff_rate'])

                    if df.loc[0, 'clo60_diff_rate'] is not None:
                        self.sf.df_all_item.loc[0, 'clo60_diff_rate'] = float(df.loc[0, 'clo60_diff_rate'])
                    if df.loc[0, 'clo80_diff_rate'] is not None:
                        self.sf.df_all_item.loc[0, 'clo80_diff_rate'] = float(df.loc[0, 'clo80_diff_rate'])
                    if df.loc[0, 'clo100_diff_rate'] is not None:
                        self.sf.df_all_item.loc[0, 'clo100_diff_rate'] = float(df.loc[0, 'clo100_diff_rate'])
                    if df.loc[0, 'clo120_diff_rate'] is not None:
                        self.sf.df_all_item.loc[0, 'clo120_diff_rate'] = float(df.loc[0, 'clo120_diff_rate'])

        # 컬럼 중에 nan 값이 있는 경우 0으로 변경 -> 이렇게 안하면 아래 데이터베이스에 넣을 때
        # AttributeError: 'numpy.int64' object has no attribute 'translate' 에러 발생
        self.sf.df_all_item = self.sf.df_all_item.fillna(0)
        self.sf.df_all_item.to_sql('all_item_db', self.engine_JB, if_exists='append', dtype={
            'code_name': Text,
            'rate': Float,
            'sell_rate': Float,
            'purchase_rate': Float,
            'sell_date': Text,
            'd1_diff_rate': Float,
            'clo5_diff_rate': Float,
            'clo10_diff_rate': Float,
            'clo20_diff_rate': Float,
            'clo40_diff_rate': Float,
            'clo60_diff_rate': Float,
            'clo80_diff_rate': Float,
            'clo100_diff_rate': Float,
            'clo120_diff_rate': Float
        })

    def check_balance(self):

        logger.debug("check_balance 함수에 들어왔습니다!")
        # 1차원 / 2차원 인스턴스 변수 생성
        self.reset_opw00018_output()

        # # 예수금 가져오기
        # self.get_d2_deposit()

        # 여기서 부터는 1차원 2차원 데이터 다 불러오는거다 opw00018에 1차원 2차원 다 있다.
        # 1차원 : 위에 한 줄 표  2차원 : 매수한 종목들

        # comm_rq_data 호출하기 전에 반드시 set_input_value 해야한다.
        self.set_input_value("계좌번호", self.account_number)
        # 사용자구분명, tran명, 3째는 0은 조회, 2는 연속, 네번째 2000은 화면 번호
        self.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.remained_data:
            # # comm_rq_data 호출하기 전에 반드시 set_input_value 해야한다. 초기화 되기 때문
            self.set_input_value("계좌번호", self.account_number)

            self.comm_rq_data("opw00018_req", "opw00018", 2, "2000")
            # print("self.opw00018_output: ", self.opw00018_output)

    # get_total_data : 특정 종목의 일자별 거래 데이터 조회 함수
    # 사용방법
    # code: 종목코드(ex. '005930' )
    # date : 기준일자. (ex. '20200424') => 20200424 일자 까지의 모든 open, high, low, close, volume 데이터 출력
    def get_total_data(self, code, code_name, date):
        logger.debug("get_total_data 함수에 들어왔다!")

        self.ohlcv = defaultdict(list)
        self.set_input_value("종목코드", code)
        self.set_input_value("기준일자", date)
        self.set_input_value("수정주가구분", 1)

        # 아래에 이거 하나만 있고 while없애면 600일 한번만 가져오는거
        self.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

        # 만약에 종목 테이블이 없으면 600일 한번만 가져오는게 아니고 몇 천일이던 싹다 가져오는거다.
        if not self.is_craw_table_exist(code_name):
            while self.remained_data == True:
                self.set_input_value("종목코드", code)
                self.set_input_value("기준일자", date)
                self.set_input_value("수정주가구분", 1)
                self.comm_rq_data("opt10081_req", "opt10081", 2, "0101")

        # data 비어있는 경우
        if len(self.ohlcv) == 0:
            return []
        # 위에 에러나면 이거해봐 일단 여기 try catch 해야함
        if self.ohlcv['date'] == '':
            return []
        # logger.debug(7)
        df = DataFrame(self.ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])

        return df

    # except Exception as e:
    #     logger.critical(e)

    # daily_craw에 종목 테이블 존재 여부 확인 함수
    def is_craw_table_exist(self, code_name):
        # #jackbot("******************************** is_craw_table_exist !!")
        sql = "select 1 from information_schema.tables where table_schema ='daily_craw' and table_name = '{}'"
        rows = self.engine_daily_craw.execute(sql.format(code_name)).fetchall()
        if rows:
            return True
        else:
            logger.debug(str(code_name) + " 테이블이 daily_craw db 에 없다. 새로 생성! ", )
            return False

    # daily_craw 특정 종목의 테이블에서 마지막으로 콜렉팅한 date를 가져오는 함수
    def get_daily_craw_db_last_date(self, code_name):
        sql = "SELECT date from `" + code_name + "` order by date desc limit 1"
        rows = self.engine_daily_craw.execute(sql).fetchall()
        if len(rows):
            return rows[0][0]
        # 신생
        else:
            return str(0)

    def collector_opt10081(self, rqname, trcode):
        # 몇 개의 row를 읽어 왔는지 담는 변수
        ohlcv_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(ohlcv_cnt):
            date = self._get_comm_data(trcode, rqname, i, "일자")
            open = self._get_comm_data(trcode, rqname, i, "시가")
            high = self._get_comm_data(trcode, rqname, i, "고가")
            low = self._get_comm_data(trcode, rqname, i, "저가")
            close = self._get_comm_data(trcode, rqname, i, "현재가")
            volume = self._get_comm_data(trcode, rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def _opt10080(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        for i in range(data_cnt):
            date = self._get_comm_data(trcode, rqname, i, "체결시간")
            open = self._get_comm_data(trcode, rqname, i, "시가")
            high = self._get_comm_data(trcode, rqname, i, "고가")
            low = self._get_comm_data(trcode, rqname, i, "저가")
            close = self._get_comm_data(trcode, rqname, i, "현재가")
            volume = self._get_comm_data(trcode, rqname, i, "거래량")

            self.ohlcv['date'].append(date[:-2])
            self.ohlcv['open'].append(abs(int(open)))
            self.ohlcv['high'].append(abs(int(high)))
            self.ohlcv['low'].append(abs(int(low)))
            self.ohlcv['close'].append(abs(int(close)))
            self.ohlcv['volume'].append(int(volume))
            self.ohlcv['sum_volume'].append(int(0))

    # trader가 호출 할때는 collector_opt10081과 다르게 1회만 _get_comm_data 호출 하면 된다.
    def _opt10081(self, rqname, trcode):
        code = self._get_comm_data(trcode, rqname, 0, "종목코드")
        if code != self.get_today_buy_list_code:
            logger.critical(
                f'_opt10081: ({code}, {self.get_today_buy_list_code})'
            )
        try:
            logger.debug("_opt10081!!!")
            date = self._get_comm_data(trcode, rqname, 0, "일자")
            open = self._get_comm_data(trcode, rqname, 0, "시가")
            high = self._get_comm_data(trcode, rqname, 0, "고가")
            low = self._get_comm_data(trcode, rqname, 0, "저가")
            close = self._get_comm_data(trcode, rqname, 0, "현재가")
            volume = self._get_comm_data(trcode, rqname, 0, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))
        except Exception as e:
            logger.critical(e)

    # # 체결 데이터를 가져오는 메서드인 GetChejanData를 사용하는
    # get_chejan_data 메서드
    def get_chejan_data(self, fid):
        # logger.debug("get_chejan_data!!!")
        try:
            ret = self.dynamicCall("GetChejanData(int)", fid)
            return ret
        except Exception as e:
            logger.critical(e)

    def end_invest_count_check(self, code):
        logger.debug("end_invest_count_check 함수로 들어왔습니다!")
        logger.debug("end_invest_count_check_code!!!!!!!!")
        logger.debug(code)

        sql = "UPDATE all_item_db SET chegyul_check='%s' WHERE code='%s' and sell_date = '%s' ORDER BY buy_date desc LIMIT 1"

        self.engine_JB.execute(sql % (0, code, 0))

        # 중복적으로 possessed_item 테이블에 반영되는 이슈가 있어서 일단 possesed_item 테이블에서 해당 종목을 지운다.
        # 어차피 다시 possessed_item은 업데이트가 된다.
        sql = "delete from possessed_item where code ='%s'"
        self.engine_JB.execute(sql % (code,))

    # 매도 했는데 완벽히 매도 못한 경우
    def sell_chegyul_fail_check(self, code):
        logger.debug("sell_chegyul_fail_check 함수에 들어왔습니다!")
        logger.debug(code + " check!")
        sql = "UPDATE all_item_db SET chegyul_check='%s' WHERE code='%s' and sell_date = '%s' ORDER BY buy_date desc LIMIT 1"
        self.engine_JB.execute(sql % (1, code, 0))

    # openapi 조회 카운트를 체크 하고 cf.max_api_call 횟수 만큼 카운트 되면 봇이 꺼지게 하는 함수
    def exit_check(self):
        rq_delay = datetime.timedelta(seconds=0.6)
        time_diff = datetime.datetime.now() - self.call_time
        if rq_delay > datetime.datetime.now() - self.call_time:
            time.sleep((rq_delay - time_diff).total_seconds())

        self.rq_count += 1
        # openapi 조회 count 출력
        logger.debug(self.rq_count)
        if self.rq_count == cf.max_api_call:
            sys.exit(1)

    # 하나의 종목이 체결이 됐는지 확인
    # 그래야 재매수든, 초기매수든 한번 샀는데 미체결량이 남아서 다시 사는건지 확인이 가능하다.
    def stock_chegyul_check(self, code):
        logger.debug("stock_chegyul_check 함수에 들어왔다!")

        sql = "SELECT chegyul_check FROM all_item_db where code='%s' and sell_date = '%s' ORDER BY buy_date desc LIMIT 1"
        # 무조건 튜플 형태로 실행해야한다. 따라서 인자 하나를 보내더라도 ( , ) 안에 하나 넣어서 보낸다.
        # self.engine_JB.execute(sql % (self.today,))

        rows = self.engine_JB.execute(sql % (code, 0)).fetchall()

        if rows[0][0] == 1:
            return True
        else:
            return False

    # 매도 후 all item db 에 작업하는거
    def sell_final_check(self, code):
        logger.debug("sell_final_check")

        # sell_price가 없어서 에러가났음
        get_list = self.engine_JB.execute(f"""
            SELECT valuation_profit, rate, item_total_purchase, present_price 
            FROM possessed_item WHERE code='{code}' LIMIT 1
        """).fetchall()
        if get_list:
            item = get_list[0]
            sql = f"""UPDATE all_item_db
                SET item_total_purchase = {item.item_total_purchase}, chegyul_check = 0,
                 sell_date = '{self.today_detail}', valuation_profit = {item.valuation_profit},
                 sell_rate = {item.rate}, sell_price = {item.present_price}
                WHERE code = '{code}' and sell_date = '0' ORDER BY buy_date desc LIMIT 1"""
            self.engine_JB.execute(sql)

            # 팔았으면 즉각 possess db에서 삭제한다. 왜냐하면 checgyul_check 들어가기 직전에 possess_db를 최신화 하긴 하지만 possess db 최신화와 chegyul_check 사이에 매도가 이뤄져서 receive로 가게 되면 sell_date를 찍어버리기 때문에 checgyul_check 입장에서는 possess에는 존재하고 all_db는 sell_date찍혀있다고 판단해서 새롭게 all_db추가해버린다.
            self.engine_JB.execute(f"DELETE FROM possessed_item WHERE code = '{code}'")

            logger.debug(f"delete {code}!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        else:
            logger.debug("possess가 없다!!!!!!!!!!!!!!!!!!!!!")

    def delete_all_item(self, code):
        logger.debug("delete_all_item!!!!!!!!")

        # 팔았으면 즉각 possess db에서 삭제한다. 왜냐하면 checgyul_check 들어가기 직전에 possess_db를 최신화 하긴 하지만 possess db 최신화와 chegyul_check 사이에 매도가 이뤄져서 receive로 가게 되면 sell_date를 찍어버리기 때문에 checgyul_check 입장에서는 possess에는 존재하고 all_db는 sell_date찍혀있다고 판단해서 새롭게 all_db추가해버린다.
        sql = "delete from all_item_db where code = '%s'"
        # self.engine_JB.execute(sql % (code,))
        # self.jackbot_db_con.commit()
        self.engine_JB.execute(sql % (code))

        logger.debug("delete_all_item!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        logger.debug(code)

    # all_item_db 보유한 종목이 있는지 확인 (sell_date가 0이거나 비어있으면 아직 매도하지 않고 보유한 종목이다)
    # 보유한 경우 true 반환, 보유 하지 않았으면 False 반환
    def is_all_item_db_check(self, code):
        logger.debug(f"is_all_item_db_check code!! {code}")
        sql = "select code from all_item_db where code='%s' and (sell_date ='%s' or sell_date='%s') ORDER BY buy_date desc LIMIT 1"

        rows = self.engine_JB.execute(sql % (code, 0, "")).fetchall()
        if len(rows) != 0:
            return True
        else:
            return False

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        logger.debug("_receive_chejan_data 함수로 들어왔습니다!!!")
        logger.debug("gubun !!! :" + gubun)

        account_num = self.get_chejan_data(9201)

        # 선택 계좌가 아닐 시 아무 행동도 하지 않는다
        if self.account_number != account_num:
            logger.info(f"{self.account_number} != {account_num}")
            return

        # 체결구분 접수와 체결
        if gubun == "0":
            logger.debug("in 체결 data!!!!!")
            # 현재 체결 진행 중인 코드를 키움증권으로 부터 가져온다
            # 종목 코드
            code = code_pattern.search(self.get_chejan_data(9001)).group(0)  # 주식 코드가 숫자만오지 않아서 정규식으로 필터링
            # 주문 번호
            order_num = self.get_chejan_data(9203)
            if not order_num:
                logger.debug(f'{code} 주문 실패')
                return

            # logger.debug("주문수량!!!")
            # logger.debug(self.get_chejan_data(900))
            # logger.debug("주문가격!!!")
            # logger.debug(self.get_chejan_data(901))

            # logger.debug("미체결수량!!!")
            # 미체결 수량
            chegyul_fail_amount_temp = self.get_chejan_data(902)
            # logger.debug(chegyul_fail_amount_temp)
            # logger.debug("원주문번호!!!")
            # logger.debug(self.get_chejan_data(904))
            # logger.debug("주문구분!!!")
            # order_gubun -> "+매수" or "-매도"
            order_gubun = self.get_chejan_data(905)
            # logger.debug(order_gubun)
            # logger.debug("주문/체결시간!!!")
            # logger.debug(self.get_chejan_data(908))
            # logger.debug("체결번호!!!")
            # logger.debug(self.get_chejan_data(909))
            # logger.debug("체결가!!!")
            # purchase_price=self.get_chejan_data(910)
            # logger.debug(self.get_chejan_data(910))
            # logger.debug("체결량!!!")
            # logger.debug(self.get_chejan_data(911))
            # logger.debug("현재가, 체결가, 실시간종가")
            purchase_price = abs(int(self.get_chejan_data(10)))

            if code:
                # 미체결 수량이 ""가 아닌 경우
                if chegyul_fail_amount_temp != "":
                    logger.debug("일단 체결은 된 경우!")
                    if self.is_all_item_db_check(code) == False:
                        logger.debug("all_item_db에 매수한 종목이 없음 ! 즉 신규 매수하는 종목이다!!!!")
                        if chegyul_fail_amount_temp == "0":
                            logger.debug("완벽히 싹 다 체결됨!!!!!!!!!!!!!!!!!!!!!!!!!")
                            self.db_to_all_item(order_num, code, 0, purchase_price, 0)
                        else:
                            logger.debug("체결 되었지만 덜 체결 됨!!!!!!!!!!!!!!!!!!")
                            self.db_to_all_item(order_num, code, 1, purchase_price, 0)

                    elif order_gubun == "+매수":
                        if chegyul_fail_amount_temp != "0" and self.stock_chegyul_check(code) == True:
                            logger.debug("아직 미체결 수량이 남아있다. 매수 진행 중!")
                            pass
                        elif chegyul_fail_amount_temp == "0" and self.stock_chegyul_check(code) == True:
                            logger.debug("미체결 수량이 없다 / 즉, 매수 끝났다!!!!!!!")
                            self.end_invest_count_check(code)
                        elif self.stock_chegyul_check(code) == False:
                            logger.debug("현재 all_item_db에 존재하고 체결 체크가 0인 종목, 재매수 하는 경우!!!!!!!")
                            # self.reinvest_count_check(code)
                        else:
                            pass

                    elif order_gubun == "-매도":
                        if chegyul_fail_amount_temp == "0":
                            logger.debug("all db에 존재하고 전량 매도하는 경우!!!!!")
                            self.sell_final_check(code)
                        else:
                            logger.debug("all db에 존재하고 수량 남겨 놓고 매도하는 경우!!!!!")
                            self.sell_chegyul_fail_check(code)

                    else:
                        logger.debug(f"order_gubun이 매수, 매도가 아닌 다른 구분!(ex. 매수취소) gubun : {order_gubun}")
                else:
                    logger.debug("_receive_chejan_data 에서 code 가 불량은 아닌데 chegyul_fail_amount_temp 가 비어있는 경우")
            else:
                logger.debug("get_chejan_data(9001): code를 받아오지 못함")

        # 국내주식 잔고전달
        elif gubun == "1":
            logger.debug("잔고데이터!!!!!")
            # logger.debug("item_cnt!!!")
            # logger.debug(item_cnt)
            # logger.debug("fid_list!!!")
            # logger.debug(fid_list)
            # try:
            # logger.debug("주문번호!!!")
            # logger.debug(self.get_chejan_data(9203))
            # logger.debug("종목명!!!")
            # logger.debug(self.get_chejan_data(302))
            # logger.debug("주문수량!!!")
            # logger.debug(self.get_chejan_data(900))
            # logger.debug("주문가격!!!")
            # logger.debug(self.get_chejan_data(901))
            #
            # logger.debug("미체결수량!!!")
            chegyul_fail_amount_temp = self.get_chejan_data(902)
            logger.debug(chegyul_fail_amount_temp)
            # logger.debug("원주문번호!!!")
            # logger.debug(self.get_chejan_data(904))
            # logger.debug("주문구분!!!")
            # logger.debug(self.get_chejan_data(905))
            # logger.debug("주문/체결시간!!!")
            # logger.debug(self.get_chejan_data(908))
            # logger.debug("체결번호!!!")
            # logger.debug(self.get_chejan_data(909))
            # logger.debug("체결가!!!")
            # logger.debug(self.get_chejan_data(910))
            # logger.debug("체결량!!!")
            # logger.debug(self.get_chejan_data(911))
            # logger.debug("현재가, 체결가, 실시간종가")
            # logger.debug(self.get_chejan_data(10))
        else:
            logger.debug(
                "_receive_chejan_data 에서 아무것도 해당 되지않음!")

    # 예수금(계좌 잔액) 호출 함수
    def get_d2_deposit(self):
        logger.debug("get_d2_deposit 함수에 들어왔습니다!")
        # 이번에는 예수금 데이터를 얻기 위해 opw00001 TR을 요청하는 코드를 구현해 봅시다. opw00001 TR은 연속적으로 데이터를 요청할 필요가 없으므로 상당히 간단합니다.
        # 비밀번호 입력매체 구분, 조회구분 다 작성해야 된다. 안그러면 0 으로 출력됨
        self.set_input_value("계좌번호", self.account_number)
        self.set_input_value("비밀번호입력매체구분", 00)
        # 조회구분 = 1:추정조회, 2: 일반조회
        self.set_input_value("조회구분", 1)
        self.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

    # 먼저 OnReceiveTrData 이벤트가 발생할 때 수신 데이터를 가져오는 함수인 _opw00001를 open_api 클래스에 추가합니다.
    def _opw00001(self, rqname, trcode):
        logger.debug("_opw00001!!!")
        try:
            self.d2_deposit_before_format = self._get_comm_data(trcode, rqname, 0, "d+2출금가능금액")
            self.d2_deposit = self.change_format(self.d2_deposit_before_format)
            logger.debug("예수금!!!!")
            logger.debug(self.d2_deposit_before_format)
        except Exception as e:
            logger.critical(e)

    # 일별실현손익
    def _opt10074(self, rqname, trcode):
        logger.debug("_opt10074!!!")
        try:
            rows = self._get_repeat_cnt(trcode, rqname)
            # total 실현손익
            self.total_profit = self._get_comm_data(trcode, rqname, 0, "실현손익")

            # KOA STUDIO에서 output에 있는 내용을 4번째 인자에 넣으면된다 (총매수금액, 당일매도순익 등등)
            # 오늘 실현손익
            self.today_profit = self._get_comm_data(trcode, rqname, 0, "당일매도손익")
            logger.debug("today_profit")
            logger.debug(self.today_profit)

            # 아래는 모든 당일매도 실현손익가져오는거다.
            # for i in range(rows):
            #     today_profit = self._get_comm_data(trcode, rqname, i, "당일매도손익")
            #     logger.debug("today_profit")
            #     logger.debug(today_profit)



        except Exception as e:
            logger.critical(e)
            # self.opw00018_output['multi'].append(
            #     [name, quantity, purchase_price, current_price, eval_profit_loss_price, earning_rate])

    def _opw00015(self, rqname, trcode):
        logger.debug("_opw00015!!!")
        try:

            rows = self._get_repeat_cnt(trcode, rqname)

            name = self._get_comm_data(trcode, rqname, 1, "계좌번호")

            for i in range(rows):
                name = self._get_comm_data(trcode, rqname, i, "거래일자")

                # self.opw00018_output['multi'].append(
                #     [name, quantity, purchase_price, current_price, eval_profit_loss_price, earning_rate])
        except Exception as e:
            logger.critical(e)

    # @staticmethod  # 이건머지
    # 아래에서 일단 위로 바꿔봄
    def change_format(self, data):
        try:
            strip_data = data.lstrip('0')
            if strip_data == '':
                strip_data = '0'

            # format_data = format(int(strip_data), ',d')

            # if data.startswith('-'):
            #     format_data = '-' + format_data
            return int(strip_data)
        except Exception as e:
            logger.critical(e)

    # 수익률에 대한 포맷 변경은 change_format2라는 정적 메서드를 사용합니다.
    #     @staticmethod
    def change_format2(self, data):
        try:
            # 앞에 0 제거
            strip_data = data.lstrip('-0')

            # 이렇게 추가해야 소수점으로 나온다.
            if strip_data == '':
                strip_data = '0'
            else:
                # 여기서 strip_data가 0이거나 " " 되니까 100 나눴을 때 갑자기 동작안함. 에러도 안뜸 그래서 원래는 if 위에 있었는데 else 아래로 내림
                strip_data = str(float(strip_data) / self.mod_gubun)
                if strip_data.startswith('.'):
                    strip_data = '0' + strip_data

                #     strip 하면 -도 사라지나보네 여기서 else 하면 안된다. 바로 위에 소수 읻네 음수 인 경우가 있기 때문
                if data.startswith('-'):
                    strip_data = '-' + strip_data

            return strip_data
        except Exception as e:
            logger.critical(e)

    # 코드 앞에 A제거
    def change_format4(self, data):
        try:
            strip_data = data.lstrip('A')
            return strip_data
        except Exception as e:
            logger.critical(e)

    def _opt10073(self, rqname, trcode):
        logger.debug("_opt10073!!!")

        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            date = self._get_comm_data(trcode, rqname, i, "일자")
            code = self._get_comm_data(trcode, rqname, i, "종목코드")
            code_name = self._get_comm_data(trcode, rqname, i, "종목명")
            amount = self._get_comm_data(trcode, rqname, i, "체결량")
            today_profit = self._get_comm_data(trcode, rqname, i, "당일매도손익")
            earning_rate = self._get_comm_data(trcode, rqname, i, "손익율")
            code = self.change_format4(code)

            # earning_rate = self.change_format2(earning_rate)

            # logger.debug("multi item_total_purchase type!!!!!!!!!!!!!!")
            # int로 나온다!!!!
            # logger.debug(type(item_total_purchase))

            self.opt10073_output['multi'].append([date, code, code_name, amount, today_profit, earning_rate])

        logger.debug("_opt10073 end!!!")

    def _opw00018(self, rqname, trcode):
        logger.debug("_opw00018!!!")
        # try:
        # 전역변수로 사용하기 위해서 총매입금액은 self로 선언
        # logger.debug(1)
        self.total_purchase_price = self._get_comm_data(trcode, rqname, 0, "총매입금액")
        # logger.debug(2)
        self.total_eval_price = self._get_comm_data(trcode, rqname, 0, "총평가금액")
        # logger.debug(3)
        self.total_eval_profit_loss_price = self._get_comm_data(trcode, rqname, 0, "총평가손익금액")
        # logger.debug(4)
        self.total_earning_rate = self._get_comm_data(trcode, rqname, 0, "총수익률(%)")
        # logger.debug(5)
        self.estimated_deposit = self._get_comm_data(trcode, rqname, 0, "추정예탁자산")
        # logger.debug(6)
        self.change_total_purchase_price = self.change_format(self.total_purchase_price)
        self.change_total_eval_price = self.change_format(self.total_eval_price)
        self.change_total_eval_profit_loss_price = self.change_format(self.total_eval_profit_loss_price)
        self.change_total_earning_rate = self.change_format2(self.total_earning_rate)

        self.change_estimated_deposit = self.change_format(self.estimated_deposit)

        self.opw00018_output['single'].append(self.change_total_purchase_price)
        self.opw00018_output['single'].append(self.change_total_eval_price)
        self.opw00018_output['single'].append(self.change_total_eval_profit_loss_price)
        self.opw00018_output['single'].append(self.change_total_earning_rate)
        self.opw00018_output['single'].append(self.change_estimated_deposit)
        # 이번에는 멀티 데이터를 통해 보유 종목별로 평가 잔고 데이터를 얻어와 보겠습니다.
        # 다음 코드를 _opw00018에 추가합니다.
        # 멀티 데이터는 먼저 _get_repeat_cnt 메서드를 호출해 보유 종목의 개수를 얻어옵니다.
        # 그런 다음 해당 개수만큼 반복하면서 각 보유 종목에 대한 상세 데이터를
        # _get_comm_data를 통해 얻어옵니다.
        # 참고로 opw00018 TR을 사용하는 경우 한 번의 TR 요청으로
        # 최대 20개의 보유 종목에 대한 데이터를 얻을 수 있습니다.
        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)

        for i in range(rows):
            code = code_pattern.search(self._get_comm_data(trcode, rqname, i, "종목번호")).group(0)
            name = self._get_comm_data(trcode, rqname, i, "종목명")
            quantity = self._get_comm_data(trcode, rqname, i, "보유수량")
            purchase_price = self._get_comm_data(trcode, rqname, i, "매입가")
            current_price = self._get_comm_data(trcode, rqname, i, "현재가")
            eval_profit_loss_price = self._get_comm_data(trcode, rqname, i, "평가손익")
            earning_rate = self._get_comm_data(trcode, rqname, i, "수익률(%)")
            item_total_purchase = self._get_comm_data(trcode, rqname, i, "매입금액")

            quantity = self.change_format(quantity)
            purchase_price = self.change_format(purchase_price)
            current_price = self.change_format(current_price)
            eval_profit_loss_price = self.change_format(eval_profit_loss_price)
            earning_rate = self.change_format2(earning_rate)
            item_total_purchase = self.change_format(item_total_purchase)

            self.opw00018_output['multi'].append(
                [name, quantity, purchase_price, current_price,
                 eval_profit_loss_price, earning_rate, item_total_purchase, code]
            )

    def reset_opw00018_output(self):
        try:
            self.opw00018_output = {'single': [], 'multi': []}
        except Exception as e:
            logger.critical(e)

    #   미체결 정보
    def _opt10076(self, rqname, trcode):
        logger.debug("func in !!! _opt10076!!!!!!!!! ")
        output_keys = ['주문번호', '종목명', '주문구분', '주문가격', '주문수량', '체결가', '체결량', '미체결수량',
                       '당일매매수수료', '당일매매세금', '주문상태', '매매구분', '원주문번호', '주문시간', '종목코드']
        self._data = {}

        for key in output_keys:
            if key not in ('주문번호', '원주문번호', '주문시간', '종목코드'):
                try:
                    self._data[key] = int(self._get_comm_data(trcode, rqname, 0, key))
                    continue
                except ValueError:
                    pass

            self._data[key] = self._get_comm_data(trcode, rqname, 0, key)

    def basic_db_check(self, cursor):
        check_list = ['daily_craw', 'daily_buy_list', 'min_craw']
        sql = "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA"
        cursor.execute(sql)
        rows = cursor.fetchall()
        db_list = [n['SCHEMA_NAME'].lower() for n in rows]
        create_db_tmp = "CREATE DATABASE {}"
        has_created = False
        for check_name in check_list:
            if check_name not in db_list:
                has_created = True
                logger.debug(f'{check_name} DB가 존재하지 않아 생성 중...')
                create_db_sql = create_db_tmp.format(check_name)
                cursor.execute(create_db_sql)
                logger.debug(f'{check_name} 생성 완료')

        if has_created and self.engine_JB.has_table('setting_data'):
            self.engine_JB.execute("""
                UPDATE setting_data SET code_update = '0';
            """)
