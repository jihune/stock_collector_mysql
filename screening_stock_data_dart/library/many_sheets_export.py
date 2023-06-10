import os
import stock.filter_data as filter_data
from export_data import ExportToData
import datetime

def make_file_path(category):
    directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'result_xlsx')

    if not os.path.exists(directory):
        os.makedirs(directory)

    # 현재 시간을 파일 이름에 추가합니다.
    current_date = datetime.datetime.today().strftime('%Y%m%d')
    current_time = datetime.datetime.now().strftime('%H%M')

    file_name = f"{current_date}_{current_time}_{category}.xlsx"
    file_path = os.path.join(directory, file_name)

    return file_path


def simple_export_data(raw_data):
    exporter = ExportToData()

    file_path = make_file_path("KOSPI_KOSDAQ")

    exporter.export_to_excel_with_many_sheets(
        file_path,
        [
            filter_data.filtering_low_per("ALL_DATA_저PER", raw_data.copy(), True),
            filter_data.filtering_low_pbr_and_per("ALL_DATA_저PBR_저PER", 1.0, 10, raw_data.copy(), True),
            filter_data.filtering_s_rim_disparity_all_data("S-RIM ALL_DATA", raw_data.copy()),
            filter_data.filtering_high_div("고배당률_리스트", raw_data.copy()),

            ("RAW_Data", raw_data)
        ]
    )


def complex_export_data(category, raw_data, extracted_data):
    exporter = ExportToData()

    file_path = make_file_path(category)

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
