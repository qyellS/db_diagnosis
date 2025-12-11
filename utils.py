import pandas as pd
import re
from typing import Tuple, Dict, List
from config import EMPTY_PATTERN, FIELD_KEYWORDS


def count_non_empty_cols(row_values: pd.Series) -> int:
    """统计一行中非空列的数量（去除空白字符后不为空）"""
    count = 0
    for val in row_values:
        val_str = str(val).strip() if not pd.isna(val) else ""
        if not EMPTY_PATTERN.match(val_str):
            count += 1
    return count


def is_col_all_empty(df: pd.DataFrame, col_idx: int) -> bool:
    """判断某一列是否全为空值（去除空白字符后）"""
    col_values = df.iloc[:, col_idx]
    for val in col_values:
        val_str = str(val).strip() if not pd.isna(val) else ""
        if not EMPTY_PATTERN.match(val_str):
            return False
    return True


def is_empty_or_special_value(cell_value: str) -> Tuple[bool, str]:
    """判断单元格是否为空值或包含特殊字符"""
    if EMPTY_PATTERN.match(cell_value):
        return True, "空值(空白字符)"
    cell_lower = cell_value.lower()
    if cell_lower == 'null':
        return True, "特殊字符：null"
    elif cell_value == '-':
        return True, "特殊字符：-"
    elif cell_value == '_':
        return True, "特殊字符：_"
    elif cell_value == '\\':
        return True, "特殊字符：\\"
    elif cell_value == '、':
        return True, "特殊字符：、"
    elif cell_value == '~':
        return True, "特殊字符：~"
    elif cell_value == '/':
        return True, "特殊字符：/"
    return False, ""


# 新增：匹配字段类型（根据表头名判断列类型）
def match_field_type(header_name: str) -> str:
    """根据表头名匹配字段类型（身份证号/手机号/邮政编码）"""
    header_lower = header_name.lower().strip()
    for field_type, keywords in FIELD_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in header_lower:
                return field_type
    return ""


# 新增：校验字段值（兼容脱敏格式）
def check_field_value(field_type: str, cell_value: str) -> Tuple[bool, str]:
    """
    校验字段值是否符合规则
    :param field_type: 字段类型（身份证号/手机号/邮政编码）
    :param cell_value: 单元格值
    :return: (是否通过, 错误描述)
    """
    # 先过滤空值/特殊值
    is_special, special_desc = is_empty_or_special_value(cell_value)
    if is_special:
        return False, special_desc

    # 去除首尾空格
    val_clean = cell_value.strip()
    # 无值情况
    if not val_clean:
        return False, "空值(空白字符)"

    # 匹配校验规则
    if field_type in FIELD_CHECK_RULES:
        check_func, error_msg = FIELD_CHECK_RULES[field_type]
        if check_func(val_clean):
            return True, ""
        else:
            return False, f"格式错误：{error_msg}（当前值：{val_clean}）"
    return True, ""