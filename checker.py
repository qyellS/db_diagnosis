import pandas as pd
import importlib
import os
from typing import List, Tuple, Dict, Callable
from config import MIN_HEADER_COLS, SKIP_FIRST_COL, SKIP_ALL_EMPTY_COLS, ENABLED_RULES
from utils import count_non_empty_cols, is_col_all_empty, match_field_type

# 加载校验规则插件
def load_check_rules() -> Dict[str, Callable]:
    rule_functions = {}
    for rule_name in ENABLED_RULES:
        try:
            # 导入路径改为"check_rules.规则文件名"
            module = importlib.import_module(f"check_rules.{rule_name}")
            rule_functions[rule_name] = module.check_value
        except Exception as e:
            print(f"加载规则{rule_name}失败：{e}")
    return rule_functions

def find_valid_header_row(df: pd.DataFrame) -> int:
    """仅通过列数查找有效表头行（不动）"""
    max_check_rows = min(10, df.shape[0])
    for row_idx in range(max_check_rows):
        row_values = df.iloc[row_idx]
        non_empty_cols = count_non_empty_cols(row_values)
        if non_empty_cols >= MIN_HEADER_COLS:
            return row_idx
    return 0

def get_header_mapping(df: pd.DataFrame, header_row: int) -> Dict[int, str]:
    """获取表头列映射（不动）"""
    header_mapping = {}
    header_values = df.iloc[header_row]
    for col_idx in range(len(header_values)):
        header_name = str(header_values.iloc[col_idx]).strip() if not pd.isna(header_values.iloc[col_idx]) else ""
        field_type = match_field_type(header_name)
        if field_type:
            header_mapping[col_idx] = field_type
    return header_mapping

def check_all_rules(df: pd.DataFrame, header_row: int) -> List[Tuple[int, int, str]]:
    """执行所有启用的校验规则"""
    errors = []
    skip_cols = set()
    # 跳过列配置（不动）
    if SKIP_FIRST_COL and df.shape[1] >= 1:
        skip_cols.add(0)
    if SKIP_ALL_EMPTY_COLS:
        for col_idx in range(df.shape[1]):
            if is_col_all_empty(df, col_idx):
                skip_cols.add(col_idx)
    # 获取表头映射
    header_mapping = get_header_mapping(df, header_row)
    # 加载启用的规则
    rule_functions = load_check_rules()

    # 逐行逐列执行校验
    for row_idx in range(header_row + 1, df.shape[0]):
        row_values = df.iloc[row_idx]
        for col_idx in range(df.shape[1]):
            if col_idx in skip_cols:
                continue
            # 获取单元格值
            cell_value = str(row_values.iloc[col_idx]).strip() if not pd.isna(row_values.iloc[col_idx]) else ""
            # 获取字段类型（身份证/手机号/邮编）
            field_type = header_mapping.get(col_idx, "")
            # 执行所有启用的规则
            for rule_name, rule_func in rule_functions.items():
                is_error, error_desc = rule_func(cell_value, field_type)
                if is_error:
                    original_row = row_idx + 1
                    original_col = col_idx + 1
                    errors.append((original_row, original_col, error_desc))
    return errors