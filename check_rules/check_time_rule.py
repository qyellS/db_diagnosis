import pandas as pd
import os
import sys
import re
from datetime import datetime
from config import FIELD_DATE_RULES, EMPTY_PATTERN

def check_value(cell_value, field_type):
    """兼容插件化接口，无实际逻辑"""
    return False, ""


def get_original_text_value(cell_val):
    """还原单元格值为原始文本形态"""
    if pd.isna(cell_val):
        return ""
    if isinstance(cell_val, str):
        return cell_val.strip()
    elif isinstance(cell_val, (int, float)):
        return str(cell_val).strip()
    else:
        return str(cell_val).strip()


def is_valid_date(date_str, allowed_formats):
    """校验日期字符串是否符合指定格式"""
    if not date_str:
        return True, ""

    for fmt in allowed_formats:
        try:
            datetime.strptime(date_str, fmt)
            return True, ""
        except ValueError:
            continue

    readable_formats = [
        fmt.replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")
        .replace("%H", "HH").replace("%M", "MM").replace("%S", "SS")
        for fmt in allowed_formats
    ]
    error_desc = f"不匹配允许的日期格式（允许：{', '.join(readable_formats)}）"
    return False, error_desc


def check_field_date(df, header_row):
    """校验指定字段的日期格式（改为全量匹配，避免字段错配）"""
    errors = []
    RULE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(RULE_DIR)
    sys.path.append(ROOT_DIR)


    # 预处理表头：构建「清理后表头→列索引」映射（不变）
    header_clean_to_col = {}
    header_col_to_original = {}
    for col_idx in range(df.shape[1]):
        header_original = str(df.iloc[header_row, col_idx]).strip() if not pd.isna(df.iloc[header_row, col_idx]) else ""
        if not header_original:
            continue
        # 清理规则：去除特殊字符+空格，转小写（不变）
        header_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', header_original).lower()
        header_clean_to_col[header_clean] = col_idx
        header_col_to_original[col_idx] = header_original

    # 遍历所有日期格式校验规则（核心修改：全量匹配）
    for field_key, allowed_formats in FIELD_DATE_RULES.items():
        if not field_key or not allowed_formats:
            continue

        # 核心修改：清理配置关键词（和表头清理规则完全一致）
        field_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', field_key).lower()
        # 从模糊匹配 → 全量匹配：仅当表头清理后 == 配置关键词清理后，才匹配
        match_col_idx = header_clean_to_col.get(field_clean, None)

        if match_col_idx is None:
            continue  # 无完全匹配的字段 → 静默跳过

        # 后续校验逻辑（不变）
        original_col = match_col_idx + 1
        for row_idx in range(header_row + 1, df.shape[0]):
            cell_val = df.iloc[row_idx, match_col_idx]
            processed_val = get_original_text_value(cell_val)

            if EMPTY_PATTERN.match(processed_val):
                continue

            valid, error_msg = is_valid_date(processed_val, allowed_formats)
            if not valid:
                original_row = row_idx + 1
                error_desc = (
                    f"日期格式非法：{field_key}（当前值='{processed_val}'，{error_msg}）"
                )
                errors.append((original_row, original_col, error_desc))

    return errors