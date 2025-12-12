import os
import sys
from SetExcelRule.config import DECIMAL_PRECISION_RULES, EMPTY_PATTERN
from SetExcelRule.utils import match_field_type

def check_value(cell_value, field_type):
    """校验小数精度"""
    # 1. 先把根目录（SetExcelRule）加入Python搜索路径

    # 获取当前规则文件的目录（check_rules）
    RULE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 向上一级就是根目录（SetExcelRule）
    ROOT_DIR = os.path.dirname(RULE_DIR)
    # 把根目录加入Python路径，让Python能找到config、utils等模块
    sys.path.append(ROOT_DIR)

    # 2. 绝对导入需要的模块（不再用from .. import）


    # 3. 原有业务逻辑（不动）
    if EMPTY_PATTERN.match(str(cell_value).strip()):
        return False, ""

    target_precision = None
    col_name = field_type
    for keyword, precision in DECIMAL_PRECISION_RULES.items():
        if keyword in col_name:
            target_precision = precision
            break
    if target_precision is None:
        return False, ""

    try:
        clean_value = str(cell_value).strip().replace(',', '').replace(' ', '')
        num = float(clean_value)
    except (ValueError, TypeError):
        return False, ""

    num_str = str(num)
    if '.' in num_str:
        decimal_part = num_str.split('.')[1]
        decimal_part_stripped = decimal_part.rstrip('0')
        actual_decimal_digits = len(decimal_part_stripped) if decimal_part_stripped else 0
    else:
        actual_decimal_digits = 0

    if actual_decimal_digits > target_precision:
        error_desc = f"小数精度错误：{col_name}列需保留{target_precision}位小数（当前值{cell_value}，实际{actual_decimal_digits}位）"
        return True, error_desc

    return False, ""