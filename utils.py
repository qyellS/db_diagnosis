import pandas as pd
import re
from typing import Tuple, Dict, List
from config import EMPTY_PATTERN, FIELD_KEYWORDS, DECIMAL_PRECISION_RULES  # 新增DECIMAL_PRECISION_RULES


# 原有函数（不动）
def count_non_empty_cols(row_values: pd.Series) -> int:
    count = 0
    for val in row_values:
        val_str = str(val).strip() if not pd.isna(val) else ""
        if not EMPTY_PATTERN.match(val_str):
            count += 1
    return count


def is_col_all_empty(df: pd.DataFrame, col_idx: int) -> bool:
    col_values = df.iloc[:, col_idx]
    for val in col_values:
        val_str = str(val).strip() if not pd.isna(val) else ""
        if not EMPTY_PATTERN.match(val_str):
            return False
    return True


def is_empty_or_special_value(cell_value: str) -> Tuple[bool, str]:
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


# 优化字段匹配函数：返回所有匹配的字段类型（包括小数规则）
def match_field_type(header_name: str) -> str:
    """
    匹配字段类型（优先原有类型，再匹配小数规则）
    :param header_name: 表头名
    :return: 字段类型（含小数规则的关键词，如"金额"）
    """
    header_lower = header_name.lower().strip()

    # 1. 匹配原有字段类型（身份证/手机号/邮编）
    for field_type, keywords in FIELD_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in header_lower:
                return field_type

    # 2. 匹配小数精度规则的关键词
    for keyword in DECIMAL_PRECISION_RULES.keys():
        if keyword.lower() in header_lower:
            return keyword  # 返回小数规则的关键词（如"金额"）

    return ""
