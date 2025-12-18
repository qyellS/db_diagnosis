import pandas as pd
import os
import sys
import re
from SetExcelRule.config import FIELD_RANGE_RULES, EMPTY_PATTERN


def check_value(cell_value, field_type):
    """兼容插件化接口，无实际逻辑"""
    return False, ""

def check_field_range(df, header_row):
    """
    校验字段数值是否在配置的范围内（静默匹配失败，无冗余错误）
    :param df: 表格数据
    :param header_row: 表头行索引
    :return: 错误列表 [(行号, 列号, 错误描述)]
    """
    errors = []
    # 1. 添加根目录到Python路径，导入配置
    RULE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(RULE_DIR)
    sys.path.append(ROOT_DIR)


    # 2. 预处理表头：构建「清理后表头→列索引」映射
    header_clean_to_col = {}  # 清理后的表头 → 列索引
    header_col_to_original = {}  # 列索引 → 原始表头（用于错误描述）
    for col_idx in range(df.shape[1]):
        header_original = str(df.iloc[header_row, col_idx]).strip() if not pd.isna(df.iloc[header_row, col_idx]) else ""
        if not header_original:
            continue
        # 清理规则：去除特殊字符+空格，转小写
        header_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', header_original).lower()
        header_clean_to_col[header_clean] = col_idx
        header_col_to_original[col_idx] = header_original

    # 3. 遍历所有范围校验规则
    for field_key, (min_val, max_val) in FIELD_RANGE_RULES.items():
        # 匹配字段列（模糊匹配）
        field_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', field_key).lower()
        match_col_idx = None
        for h_clean, col_idx in header_clean_to_col.items():
            if field_clean in h_clean or h_clean in field_clean:
                match_col_idx = col_idx
                break
        if match_col_idx is None:
            continue  # 字段未匹配 → 静默跳过

        # 4. 遍历数据行，校验数值范围
        original_col = match_col_idx + 1  # Excel列号
        for row_idx in range(header_row + 1, df.shape[0]):
            # 提取单元格值并清理
            cell_val = df.iloc[row_idx, match_col_idx]
            cell_str = str(cell_val).strip() if not pd.isna(cell_val) else ""
            if EMPTY_PATTERN.match(cell_str):
                continue  # 空值跳过

            # 尝试转换为数值（支持整数/小数）
            try:
                num = float(cell_str.replace(',', ''))  # 去除千分位逗号
            except (ValueError, TypeError):
                continue  # 非数值 → 跳过

            # 校验范围
            if num < min_val or num > max_val:
                original_row = row_idx + 1  # Excel行号
                error_desc = (
                    f"字段数值超出范围：{field_key}（允许{min_val}~{max_val}），当前值={num}"
                )
                errors.append((original_row, original_col, error_desc))

    return errors