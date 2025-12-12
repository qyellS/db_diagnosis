import re
#配置
EMPTY_PATTERN = re.compile(r'^\s*$')
# 支持的表格格式
SUPPORTED_FORMATS = ('.xlsx', '.xls', '.csv')
# 表头行最小有效列数（默认3）
MIN_HEADER_COLS = 3
# 配置：是否跳过第一列检查（True=跳过，False=不跳过）
SKIP_FIRST_COL = True
# 配置：跳过全空列的检查（True=跳过，False=不跳过）
SKIP_ALL_EMPTY_COLS = True
# 过滤Excel临时文件（以~$开头）
SKIP_TEMP_FILES = True
# 临时文件前缀（Excel锁定文件）
TEMP_FILE_PREFIX = '~$'

#小数精度检查配置（列名关键词 → 保留小数位数）
DECIMAL_PRECISION_RULES = {

    '容积(L)': 1,
    '容量': 3,

}



#启用的校验规则（想禁用某规则，直接注释掉）
ENABLED_RULES = [
    "check_null",           # 空值/特殊值检查
    "check_id_card",        # 身份证号校验
    "check_mobile",         # 手机号校验
    "check_postcode",       # 邮政编码校验
    "check_float",          # 浮点数精度校验
]

# 字段关键词
FIELD_KEYWORDS = {
    '身份证号': ['身份证号', '身份证'],
    '手机号': ['手机号', '电话', '手机', '联系电话'],
    '邮政编码': ['邮编', '邮政编码']
}