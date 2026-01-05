def check_value(cell_value, field_type):
    """校验身份证号（仅当字段类型为身份证号时触发）"""
    if field_type != '身份证号':
        return False, ""
    # 空值已由special_value规则检查，此处无需重复
    if not cell_value:
        return False, ""

    # 统一转为字符串（避免非字符串类型导致len报错）
    cell_value = str(cell_value).strip()

    # 校验长度+脱敏格式（支持18位原始/脱敏身份证号）
    if len(cell_value) != 18:
        return True, f"身份证号：长度需为18位（当前{len(cell_value)}位）"

    # 步骤1：处理脱敏符*（保留X/x，仅移除*）
    clean_value = cell_value.replace('*', '')

    # 步骤2：校验身份证号格式（最后一位允许X/x，其余位必须是数字）
    # 前17位必须是数字
    prefix = clean_value[:17]
    suffix = clean_value[-1].upper()  # 最后一位统一转大写（x→X）

    # 校验前17位是否为数字
    if not prefix.isdigit():
        return True, f"身份证号：前17位需为数字（当前值：{cell_value}）"

    # 校验最后一位是否为数字或X
    if suffix not in ('X',) and not suffix.isdigit():
        return True, f"身份证号：最后一位需为数字或X（当前值：{cell_value}）"

    return False, ""