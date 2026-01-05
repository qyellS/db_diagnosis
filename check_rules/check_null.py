from typing import Tuple
import re

EMPTY_PATTERN = re.compile(r'^\s*$')

def check_value(cell_value: str, field_type: str) -> Tuple[bool, str]:
    """校验空值/特殊字符"""
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
    elif cell_value == '——':
        return True, "特殊字符：——"
    return False, ""