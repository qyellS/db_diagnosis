import re
#配置
EMPTY_PATTERN = re.compile(r'^\s*$')
# 支持的表格格式
SUPPORTED_FORMATS = ('.xlsx', '.xls', '.csv')

# 配置：是否跳过第一列检查（True=跳过，False=不跳过）
SKIP_FIRST_COL = True
# 配置：跳过全空列的检查（True=跳过，False=不跳过）
SKIP_ALL_EMPTY_COLS = True
# 过滤Excel临时文件（以~$开头）
SKIP_TEMP_FILES = True
# 临时文件前缀（Excel锁定文件）
TEMP_FILE_PREFIX = '~$'
################（以上无需修改）##################################


# 表头行最小有效列数（默认3）
MIN_HEADER_COLS = 3

# 校验规则，新增功能代码名称
ENABLED_RULES = [
    "check_null",           # 空值/特殊值检查
    "check_id_card",        # 身份证号校验
    "check_mobile",         # 手机号校验
    "check_postcode",       # 邮政编码校验
    "check_float",          # 浮点数精度校验
    "check_header",         # 检查表头
    "check_row",            # 检查重复行
    "check_primary_slave",  # 检查主键从键（数据唯一性）
    "check_key_scope",      # 检查关键字范围
    "check_field_length",   # 检查指定字段长度数是否符合
    "check_field_enum",     # 检查枚举类型字段内容
    "check_time_rule",      # 检查时间类型字段是符合内容
]

#小数精度检查配置（列名关键词 : 保留小数位数）
DECIMAL_PRECISION_RULES = {
    '容积(L)': 1,
    '容量': 3,
}

# 检查内容是否符合固定规则，如身份证号18位，手机号11位，邮政编码6位
FIELD_KEYWORDS = {
    '身份证号': ['身份证号', '身份证','证件号'],
    '手机号': ['手机号', '电话', '手机', '联系电话'],
    '邮政编码': ['邮编', '邮政编码'],
}

#数据唯一性，主键从键检查配置
PRIMARY_SLAVE_KEY_RULES = {
    # '身份证号': '姓名',          # 单从键：身份证号+姓名组合重复
    '监测点': '测试时间,风速（单位:m/s）',      # 多从键：手机号+姓名+金额组合重复
    '机构名称': '身份证号',

}

#字段范围配置文件
FIELD_RANGE_RULES = {
    '年龄': (0, 200),        # 年龄范围：0 ≤ 数值 ≤ 200
    '温度': (-20, 40),       # 温度范围：-20 ≤ 数值 ≤ 40
    '风速（单位:m/s）': (0, 100)  # 风速范围：0 ≤ 数值 ≤ 100
}

#字段位数校验规则（对应需求的JSON格式，转为Python字典）
FIELD_LENGTH_RULES = {
    "门牌号": 3,   # 要求门牌号长度为3
    "设备号": 2    # 要求设备号长度为9
}

# 字段枚举值校验规则（对应需求的JSON格式，转为Python字典）
FIELD_ENUM_RULES = {
    "性别": "男，女，保密",       # 性别允许值：男、女、保密
    "状态": "正常，故障",         # 状态允许值：正常、故障

}

# 新增：日期格式校验规则（字段关键词: 允许的日期格式列表）
#   年  月  日  时  分  秒
#  %Y %M  %D  %H  %M  %S
FIELD_DATE_RULES = {
    "测试时间": ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"],
    "时间": ["%Y-%m-%d"],              # 仅支持YYYY-MM-DD

}