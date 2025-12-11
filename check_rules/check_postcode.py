from typing import Tuple

def check_value(cell_value: str, field_type: str) -> Tuple[bool, str]:
    """校验邮政编码（仅当字段类型为邮政编码时触发）"""
    if field_type != '邮政编码':
        return False, ""
    if not cell_value:
        return False, ""
    if len(cell_value) != 6:
        return True, f"邮政编码：长度需为6位（当前{len(cell_value)}位）"
    if not cell_value.isdigit():
        return True, f"邮政编码：需为6位纯数字（当前值：{cell_value}）"
    return False, ""