# 新增：导入pandas并命名为pd
import pandas as pd


def check_value(cell_value, field_type):
    """兼容插件化接口，行重复校验在独立函数中执行"""
    return False, ""


def check_duplicate_row(df, header_row):
    """检查数据行是否完全重复"""
    errors = []
    # 只检查表头后的行
    data_rows = df.iloc[header_row + 1:]
    # 清理每行数据（去空格、转字符串）
    row_clean = []
    row_original_idx = []
    for row_idx, (_, row) in enumerate(data_rows.iterrows()):
        clean_row = []
        for val in row:
            # 修复：pd.isna() 需要先导入pandas
            val_str = str(val).strip() if not pd.isna(val) else ""
            clean_row.append(val_str)
        row_clean.append(tuple(clean_row))  # 转元组用于哈希
        row_original_idx.append(row_idx + header_row + 2)  # 转换为Excel实际行号

    # 查找重复行
    seen = {}
    for row_idx, (clean_row, original_row) in enumerate(zip(row_clean, row_original_idx)):
        # 全空行跳过
        if all(not val for val in clean_row):
            continue
        if clean_row in seen:
            prev_row = seen[clean_row]
            errors.append(
                (original_row, 1,  # 列号标为1，代表整行重复
                 f"数据行重复：第{original_row}行与第{prev_row}行完全重复")
            )
        else:
            seen[clean_row] = original_row
    return errors