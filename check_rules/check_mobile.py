from typing import Tuple

def check_value(cell_value: str, field_type: str) -> Tuple[bool, str]:
    """校验手机号（仅当字段类型为手机号时触发）"""
    if field_type != '手机号':
        return False, ""
    if not cell_value:
        return False, ""
    if len(cell_value) != 11:
        return True, f"手机号：长度需为11位（当前{len(cell_value)}位）"
    clean_value = cell_value.replace('*', '')
    if clean_value and not clean_value.isdigit():
        return True, f"手机号：非脱敏部分需为数字（当前值：{cell_value}）"
    return False, ""