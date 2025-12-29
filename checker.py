import pandas as pd
import importlib
import os
import sys
from typing import List, Tuple, Dict, Callable
from config import MIN_HEADER_COLS, SKIP_FIRST_COL, SKIP_ALL_EMPTY_COLS, ENABLED_RULES
from utils import count_non_empty_cols, is_col_all_empty, match_field_type

# 确保根目录在Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入验函数
from check_rules.check_header import check_duplicate_header
from check_rules.check_row import check_duplicate_row
from check_rules.check_primary_slave import check_primary_slave_duplicate
from check_rules.check_key_scope import check_field_range
from check_rules.check_field_length import check_field_length
from check_rules.check_field_enum import check_field_enum
from check_rules.check_time_rule import check_field_date

def load_check_rules() -> Dict[str, Callable]:
    rule_functions = {}
    for rule_name in ENABLED_RULES:
        try:
            module = importlib.import_module(f"check_rules.{rule_name}")
            rule_functions[rule_name] = module.check_value
        except Exception as e:
            print(f"加载规则{rule_name}失败：{e}")
    return rule_functions


def find_valid_header_row(df: pd.DataFrame) -> int:
    max_check_rows = min(10, df.shape[0])
    for row_idx in range(max_check_rows):
        row_values = df.iloc[row_idx]
        non_empty_cols = count_non_empty_cols(row_values)
        if non_empty_cols >= MIN_HEADER_COLS:
            return row_idx
    return 0


def get_header_mapping(df: pd.DataFrame, header_row: int) -> Dict[int, str]:
    header_mapping = {}
    header_values = df.iloc[header_row]
    for col_idx in range(len(header_values)):
        header_name = str(header_values.iloc[col_idx]).strip() if not pd.isna(header_values.iloc[col_idx]) else ""
        field_type = match_field_type(header_name)
        if field_type:
            header_mapping[col_idx] = field_type
    return header_mapping


def check_all_rules(df: pd.DataFrame, header_row: int) -> List[Tuple[int, int, str]]:
    errors = []
    skip_cols = set()

    # 跳过列配置（不动）
    if SKIP_FIRST_COL and df.shape[1] >= 1:
        skip_cols.add(0)
    if SKIP_ALL_EMPTY_COLS:
        for col_idx in range(df.shape[1]):
            if is_col_all_empty(df, col_idx):
                skip_cols.add(col_idx)

    # 新增1：校验表头重复
    header_duplicate_errors = check_duplicate_header(df, header_row)
    errors.extend(header_duplicate_errors)

    # 新增2：校验数据行重复
    row_duplicate_errors = check_duplicate_row(df, header_row)
    errors.extend(row_duplicate_errors)

    primary_slave_errors = check_primary_slave_duplicate(df, header_row)
    errors.extend(primary_slave_errors)

    field_range_errors = check_field_range(df, header_row)
    errors.extend(field_range_errors)

    header_mapping = get_header_mapping(df, header_row)
    rule_functions = load_check_rules()

    field_length_errors = check_field_length(df, header_row)
    errors.extend(field_length_errors)

    field_enum_errors = check_field_enum(df, header_row)
    errors.extend(field_enum_errors)

    field_date_errors = check_field_date(df, header_row)
    errors.extend(field_date_errors)


    for row_idx in range(header_row + 1, df.shape[0]):
        row_values = df.iloc[row_idx]
        for col_idx in range(df.shape[1]):
            if col_idx in skip_cols:
                continue

            cell_value = str(row_values.iloc[col_idx]).strip() if not pd.isna(row_values.iloc[col_idx]) else ""
            if col_idx in header_mapping:
                field_type = header_mapping[col_idx]
                for rule_name, rule_func in rule_functions.items():
                    is_error, error_desc = rule_func(cell_value, field_type)
                    if is_error:
                        original_row = row_idx + 1
                        original_col = col_idx + 1
                        errors.append((original_row, original_col, error_desc))
                continue

            for rule_name, rule_func in rule_functions.items():
                is_error, error_desc = rule_func(cell_value, "")
                if is_error:
                    original_row = row_idx + 1
                    original_col = col_idx + 1
                    errors.append((original_row, original_col, error_desc))
    return errors