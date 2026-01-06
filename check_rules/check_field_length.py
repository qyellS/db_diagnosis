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
    校验指定字段的字符位数（支持一个字段对应多个允许长度，如门牌号[3,4,6]）
    :param df: 表格数据
    :param header_row: 表头行索引
    :return: 错误列表 [(行号, 列号, 错误描述)]
    """
    errors = []
    # 1. 添加根目录到Python路径
    RULE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(RULE_DIR)
    sys.path.append(ROOT_DIR)

    # 2. 预处理表头：构建「清理后表头→列索引」映射
    header_clean_to_col = {}  # 清理后的表头 → 列索引
    for col_idx in range(df.shape[1]):
        header_original = str(df.iloc[header_row, col_idx]).strip() if not pd.isna(df.iloc[header_row, col_idx]) else ""
        if not header_original:
            continue
        # 清理规则：去除特殊字符+空格，转小写（保证模糊匹配）
        header_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', header_original).lower()
        header_clean_to_col[header_clean] = col_idx

    # 3. 遍历所有位数校验规则
    for field_key, length_config in FIELD_LENGTH_RULES.items():
        # 统一格式：将单值/列表都转为整数列表（兼容所有配置格式）
        allowed_lengths = []
        if isinstance(length_config, int):
            allowed_lengths = [length_config]  # 单值转列表
        elif isinstance(length_config, (list, tuple)):
            # 过滤有效整数（避免配置错误，如[3, "4", 6.0] → [3,4,6]）
            allowed_lengths = [
                int(l) for l in length_config
                if isinstance(l, (int, float, str)) and str(l).isdigit()
            ]
        else:
            print(f"⚠️  字段{field_key}长度配置无效：{length_config}，跳过校验")
            continue

        # 无有效长度配置，直接跳过
        if not allowed_lengths:
            continue

        # 4. 模糊匹配字段列（如"门牌号"/"门牌"/"门号"都能匹配）
        field_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', field_key).lower()
        match_col_idx = None
        for h_clean, col_idx in header_clean_to_col.items():
            if field_clean in h_clean or h_clean in field_clean:
                match_col_idx = col_idx
                break
        if match_col_idx is None:
            continue  # 表格中无该字段，跳过

        # 5. 遍历数据行，校验长度
        original_col = match_col_idx + 1  # 转换为Excel列号（从1开始）
        for row_idx in range(header_row + 1, df.shape[0]):
            # 提取单元格值并处理空值
            cell_val = df.iloc[row_idx, match_col_idx]
            if pd.isna(cell_val) or EMPTY_PATTERN.match(str(cell_val).strip()):
                continue

            # 6. 按文本语义处理值（修复数值型长度统计问题）
            cell_str = str(cell_val).strip()
            processed_val = cell_str
            # 处理数值型值：104.0 → "104"，1104.5 → "1104.5"
            try:
                num = float(cell_str)
                if num.is_integer():
                    processed_val = str(int(num))
            except (ValueError, TypeError):
                pass  # 非数值型值，保留原样

            # 7. 核心校验：判断长度是否在允许列表中
            actual_length = len(processed_val)
            if actual_length not in allowed_lengths:
                original_row = row_idx + 1  # 转换为Excel行号（从1开始）
                # 格式化允许长度提示（如[3,4,6] → "3位、4位或6位"）
                allowed_str = "、".join([f"{l}位" for l in sorted(allowed_lengths)[:-1]]) + f"或{allowed_lengths[-1]}位"
                # 构造错误描述
                error_desc = (
                    f"字段位数不符合要求：{field_key}（要求{allowed_str}，原始值='{cell_str}'，处理后值='{processed_val}'，实际{actual_length}位）"
                )
                errors.append((original_row, original_col, error_desc))

    return errors