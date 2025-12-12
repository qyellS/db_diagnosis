def check_value(cell_value, field_type):
    """校验身份证号（仅当字段类型为身份证号时触发）"""
    if field_type != '身份证号':
        return False, ""
    # 空值已由special_value规则检查，此处无需重复
    if not cell_value:
        return False, ""
    # 校验长度+脱敏格式
    if len(cell_value) != 18:
        return True, f"身份证号：长度需为18位（当前{len(cell_value)}位）"
    # 非*部分需为数字
    clean_value = cell_value.replace('*', '')
    if clean_value and not clean_value.isdigit():
        return True, f"身份证号：非脱敏部分需为数字（当前值：{cell_value}）"
    return False, ""