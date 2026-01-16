import pandas as pd
import os
import sys
import re
from config import FIELD_ENUM_RULES, EMPTY_PATTERN

def check_value(cell_value, field_type):
    """兼容插件化接口，无实际逻辑"""
    return False, ""


def get_original_text_value(cell_val):
    """
    还原单元格值为原始文本形态（复用位数校验的核心函数，保证格式统一）
    """
    if pd.isna(cell_val):
        return ""
    if isinstance(cell_val, str):
        return cell_val.strip()
    elif isinstance(cell_val, (int, float)):
        return str(cell_val).strip()
    else:
        return str(cell_val).strip()


def check_field_enum(df, header_row):
    """
    校验指定字段的枚举值是否合法（静默匹配失败，不修改全局读取逻辑）
    :param df: 表格数据（保持原有读取格式）
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

    # 3. 遍历所有枚举校验规则
    for field_key, enum_str in FIELD_ENUM_RULES.items():
        # 跳过空规则（如配置中"" : ""的情况）
        if not field_key or not enum_str:
            continue

        # 解析枚举列表（兼容中英文逗号，去重+去空格）
        enum_list = [e.strip() for e in re.split(r'，|,', enum_str) if e.strip()]
        if not enum_list:
            continue

        # 匹配字段列（模糊匹配）
        field_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', field_key).lower()
        match_col_idx = None
        for h_clean, col_idx in header_clean_to_col.items():
            if field_clean in h_clean or h_clean in field_clean:
                match_col_idx = col_idx
                break
        if match_col_idx is None:
            continue  # 字段未匹配 → 静默跳过

        # 4. 遍历数据行，校验枚举值
        original_col = match_col_idx + 1  # Excel列号
        for row_idx in range(header_row + 1, df.shape[0]):
            # 提取单元格值并还原为原始文本形态
            cell_val = df.iloc[row_idx, match_col_idx]
            processed_val = get_original_text_value(cell_val)

            # 处理空值/空白字符（跳过）
            if EMPTY_PATTERN.match(processed_val):
                continue

            # 校验是否在枚举列表中（不区分大小写，兼容用户输入误差）
            if processed_val not in enum_list:
                original_row = row_idx + 1  # Excel行号
                enum_str_show = "、".join(enum_list)
                error_desc = (
                    f"字段枚举值非法：{field_key}（允许值：{enum_str_show}，当前值='{processed_val}'）"
                )
                errors.append((original_row, original_col, error_desc))

    return errors