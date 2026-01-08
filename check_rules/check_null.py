from typing import Tuple, List
import re
import pandas as pd  # 新增导入，处理NaN

EMPTY_PATTERN = re.compile(r'^\s*$')


def check_value(cell_value: str, field_type: str) -> Tuple[bool, str]:
    """校验空值/特殊字符（原有逻辑，供数据行调用）"""
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
    elif cell_value == '--':
        return True, "特殊字符：--"
    return False, ""


def check_header_null(df: pd.DataFrame, header_row: int) -> List[Tuple[int, int, str]]:
    """
    新增：专门检查表头行的空值/特殊字符
    :param df: 表格数据
    :param header_row: 表头行索引
    :return: 错误列表 [(行号, 列号, 错误描述)]
    """
    errors = []
    # 仅处理表头行
    header_values = df.iloc[header_row]

    for col_idx in range(len(header_values)):
        # 提取表头单元格值，兼容NaN
        cell_val = header_values.iloc[col_idx]

        # 步骤1：处理NaN（Pandas空值）
        if pd.isna(cell_val):
            excel_row = header_row + 1
            excel_col = col_idx + 1
            errors.append((excel_row, excel_col, "表头空值：NaN（空白单元格）"))
            continue

        # 步骤2：转为字符串并清理空白
        cell_str = str(cell_val).strip()

        # 步骤3：复用原有空值/特殊字符校验逻辑
        is_error, error_desc = check_value(cell_str, "")
        if is_error:
            excel_row = header_row + 1
            excel_col = col_idx + 1
            errors.append((excel_row, excel_col, f"表头{error_desc}"))

    return errors