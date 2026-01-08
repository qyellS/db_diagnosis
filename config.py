import re
import os
#配置
EMPTY_PATTERN = re.compile(r'^\s*$')
# 支持的表格格式
SUPPORTED_FORMATS = ('.xlsx', '.xls', '.csv')

# 配置：是否跳过第一列检查（True=跳过，False=不跳过）
SKIP_FIRST_COL = False
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
    "check_null",           # 空值/特殊值检查 （完整性-数据元素完整性）
    "check_id_card",        # 身份证号校验，（准确性-数据格式合规性）
    "check_mobile",         # 手机号校验，（数据格式合规性）
    "check_postcode",       # 邮政编码校验，（数据格式合规性）
    "check_header",         # 检查表头，（准确性-数据重复率-重复列检测。规范性-元数据：字段空值检查）
    "check_row",            # 检查重复行，（准确性-数据重复率-重复行检测）
    "check_sensitive_word", # 敏感词检测，（规范性-安全规范性）
    #下面的需要根据实际表情况进行配置
    "check_float",          # 浮点数精度校验，（准确性-数据格式合规性）
    "check_primary_slave",  # 检查主键从键（准确性-数据唯一性）
    "check_key_scope",      # 检查关键字范围  例如年龄范围 （准确性-脏数据）
    "check_field_length",   # 检查指定字段长度数是否符合 （准确性-数据格式合规性）
    "check_field_enum",     # 检查枚举类型字段内容，值域范围，如性别  男或女或保密
    "check_time_rule",      # 检查时间类型字段是符合内容 （准确性-数据格式合规性）
    "check_encrypt",        # 检查字段是否进行脱敏 （规范性-安全规范性）

]

# 检查内容是否符合固定规则，如身份证号18位，手机号11位，邮政编码6位
FIELD_KEYWORDS = {
    '身份证号': ['身份证号', '身份证','证件号'],       # 一个字段多种名称，例如“身份证号”可能为 身份证、证件号等
    '手机号': ['手机号', '电话', '手机', '联系电话'],
    '邮政编码': ['邮编', '邮政编码'],
}


# 浮点数精度校验，（准确性-数据格式合规性）
DECIMAL_PRECISION_RULES = {
    '容积(L)': 1,
    '容量': 3,

}

#数据唯一性，主键从键检查配置
PRIMARY_SLAVE_KEY_RULES = {
    '监测点': ['测试时间,风速（单位:m/s）', 'True'],  # 允许监测点主键重复，仅校验组合
    '机构名称': ['身份证号', 'False'],               # 不允许机构名称主键重复，同时校验组合
}

#字段范围配置文件
FIELD_RANGE_RULES = {
    '年龄': (0, 200),        # 年龄范围：0 ≤ 数值 ≤ 200
    '温度': (-20, 40),       # 温度范围：-20 ≤ 数值 ≤ 40
    '风速（单位:m/s）': (0, 100)  # 风速范围：0 ≤ 数值 ≤ 100
}

#字段位数校验规则（对应需求的JSON格式，转为Python字典）
FIELD_LENGTH_RULES = {
    "个人ID": [13],  # 支持3位
    "设备号": [11,14],         # 仅支持9位
}

# 字段枚举值校验规则（对应需求的JSON格式，转为Python字典）
FIELD_ENUM_RULES = {
    "性别": "男，女，保密",       # 性别允许值：男、女、保密
    "状态": "在用，通气已点火，通气未点火",         # 状态允许值：正常、故障

}

# 新增：日期格式校验规则（字段关键词: 允许的日期格式列表）
#   年  月  日  时  分  秒
#  %Y %M  %D  %H  %M  %S
# 检查时间类型字段是符合内容 （准确性-数据格式合规性）
FIELD_DATE_RULES = {
    "测试时间": ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"], #年/月/日
    "时间": ["%Y-%m-%d"],               # 仅支持YYYY-MM-DD年-月-日
}

# 检查字段是否进行脱敏 （规范性-安全规范性）
ENCRYPT_REQUIRED_FIELDS = [
    "身份证号",    # 需要加密的字段名1
    "手机号"       # 需要加密的字段名2
]

#脱敏规则
ENCRYPT_CONFIG = {
    "min_star_count": 1,  # 至少包含1个 *
    "ignore_empty": True  # 空值跳过检查，无需修改
}

SENSITIVE_CONFIG = {
    "sensitive_file_rel_path": "data\keywords.txt"  # 敏感词文件相对路径
}

# 辅助：获取项目根目录（用于解析相对路径）
def get_project_root():
    return os.path.dirname(os.path.abspath(__file__))

# 辅助：获取敏感词文件绝对路径
def get_sensitive_file_path():
    root = get_project_root()
    rel_path = SENSITIVE_CONFIG.get("sensitive_file_rel_path", "keywords.txt")
    return os.path.join(root, rel_path)