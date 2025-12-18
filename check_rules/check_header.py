import pandas as pd


def check_value(cell_value, field_type):

    """
    校验表头字段是否重复（注：该规则不依赖cell_value/field_type，仅利用统一接口，实际在checker_core中提前校验）
    此处为兼容插件化架构，实际表头重复校验逻辑需在checker_core中扩展，本函数仅返回已收集的错误
    """
    # 表头重复属于“文件级错误”，需在checker_core中单独处理，此处返回空（后续优化可通过全局变量传递错误）
    return False, ""


# 新增独立函数：供checker_core调用的表头重复校验
def check_duplicate_header(df, header_row):
    """
    检查表头行是否有重复字段
    :param df: 表格数据
    :param header_row: 表头行索引
    :return: 错误信息列表 [(行号, 列号, 错误描述)]
    """
    errors = []
    # 获取表头行数据
    header_values = df.iloc[header_row]
    # 清理表头值（去空格、转小写，用于判断重复）
    header_clean = []
    header_original = []
    for col_idx, val in enumerate(header_values):
        val_str = str(val).strip() if not pd.isna(val) else ""
        header_clean.append(val_str.lower())
        header_original.append(val_str)

    # 查找重复的表头字段
    seen = {}
    for col_idx, (clean_val, original_val) in enumerate(zip(header_clean, header_original)):
        if not clean_val:  # 空表头跳过
            continue
        if clean_val in seen:
            # 记录重复错误（原表头行号+重复列号）
            original_row = header_row + 1
            original_col = col_idx + 1
            prev_col = seen[clean_val] + 1
            errors.append(
                (original_row, original_col,
                 f"表头字段重复：'{original_val}' 与第{prev_col}列的'{original_val}'重复")
            )
        else:
            seen[clean_val] = col_idx
    return errors