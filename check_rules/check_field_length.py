import pandas as pd
import os
import sys
import re
from SetExcelRule.config import FIELD_LENGTH_RULES, EMPTY_PATTERN

def check_value(cell_value, field_type):
    """兼容插件化接口，无实际逻辑"""
    return False, ""


def check_field_length(df, header_row):
    """
    校验指定字段的字符位数（按文本语义校验，修复数值型值长度统计问题）
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

    # 3. 遍历所有位数校验规则
    for field_key, target_length in FIELD_LENGTH_RULES.items():
        # 匹配字段列（模糊匹配）
        field_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', field_key).lower()
        match_col_idx = None
        for h_clean, col_idx in header_clean_to_col.items():
            if field_clean in h_clean or h_clean in field_clean:
                match_col_idx = col_idx
                break
        if match_col_idx is None:
            continue  # 字段未匹配 → 静默跳过

        # 4. 遍历数据行，校验字符位数（按文本语义）
        original_col = match_col_idx + 1  # Excel列号
        for row_idx in range(header_row + 1, df.shape[0]):
            # 提取单元格值
            cell_val = df.iloc[row_idx, match_col_idx]
            # 第一步：处理空值
            if pd.isna(cell_val):
                continue
            cell_str = str(cell_val).strip()
            if EMPTY_PATTERN.match(cell_str):
                continue  # 空值跳过

            # 第二步：按文本语义处理值（核心修复）
            processed_val = cell_str
            # 处理数值型值：去除小数尾缀.0（如323.0→323，123.45→123.45）
            try:
                # 尝试转换为数值
                num = float(cell_str)
                # 若是整数（如323.0），转为整数字符串；否则保留原小数字符串
                if num.is_integer():
                    processed_val = str(int(num))
                else:
                    processed_val = str(num)
            except (ValueError, TypeError):
                # 非数值型值（纯文本），保留原样
                pass

            # 第三步：统计文本语义长度（处理后的值长度）
            actual_length = len(processed_val)

            # 校验位数是否匹配
            if actual_length != target_length:
                original_row = row_idx + 1  # Excel行号
                error_desc = (
                    f"字段位数不符合要求：{field_key}（要求{target_length}位，原始值='{cell_str}'，处理后值='{processed_val}'，实际{actual_length}位）"
                )
                errors.append((original_row, original_col, error_desc))

    return errors