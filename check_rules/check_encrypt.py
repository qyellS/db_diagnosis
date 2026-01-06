#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import pandas as pd
from SetExcelRule.config import ENCRYPT_REQUIRED_FIELDS, ENCRYPT_CONFIG, EMPTY_PATTERN


def check_value(cell_value, field_type):
    """兼容插件化接口，无实际逻辑"""
    return False, ""


def check_encrypt(df, header_row):
    """
    检查指定字段是否添加*加密脱敏
    :param df: 表格数据
    :param header_row: 表头行索引
    :return: 错误列表 [(行号, 列号, 错误描述)]
    """
    errors = []
    min_star_count = ENCRYPT_CONFIG.get("min_star_count", 1)
    ignore_empty = ENCRYPT_CONFIG.get("ignore_empty", True)

    # 1. 获取表头名称与列索引的映射
    header_map = {}  # {字段名: 列索引}
    for col_idx in range(df.shape[1]):
        header_val = df.iloc[header_row, col_idx] if header_row < df.shape[0] else f"列{col_idx + 1}"
        header_name = str(header_val).strip() if not pd.isna(header_val) else ""
        if header_name in ENCRYPT_REQUIRED_FIELDS:
            header_map[header_name] = col_idx

    # 无需要检查的字段，直接返回
    if not header_map:
        return errors

    # 2. 遍历数据行，检查指定字段
    for row_idx in range(header_row + 1, df.shape[0]):
        for field_name, col_idx in header_map.items():
            # 提取单元格值
            cell_val = df.iloc[row_idx, col_idx]
            cell_str = str(cell_val).strip() if not pd.isna(cell_val) else ""

            # 空值跳过（由空值规则处理）
            if ignore_empty and EMPTY_PATTERN.match(cell_str):
                continue

            # 检查是否包含足够的*
            star_count = cell_str.count("*")
            if star_count < min_star_count:
                # 转换为Excel风格的行列号（从1开始）
                excel_row = row_idx + 1
                excel_col = col_idx + 1
                # 构造错误信息
                error_desc = (
                    f"字段加密检查：【{field_name}】列（行{excel_row}列{excel_col}）未加密，"
                    f"当前值='{cell_str}'（需包含至少{min_star_count}个*）"
                )
                errors.append((excel_row, excel_col, error_desc))

    return errors


# 测试代码（可选）
if __name__ == "__main__":
    test_df = pd.DataFrame({
        "身份证号": ["13063719520404031X", "130******0404031X", ""],
        "手机号": ["13800138000", "138****8000", "13800138000"],
        "姓名": ["张三", "李四", "王五"]
    })
    errors = check_encrypt(test_df, header_row=0)
    for err in errors:
        print(f"行{err[0]} 列{err[1]}：{err[2]}")