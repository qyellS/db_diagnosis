运行前根据具体表格在config.py文件中配置具体字段

运行main.py，输入需要检查表格路径，检查结果保存到main同级目录下，

每个功能都在check_rules中，增加新功能在check_rules中创建新py文件

新的代码创建完毕后，须在config.py中 ENABLED_RULES 写入新增加的规则代码文件名

修改 checker.py 导入新的规则应用。

以下规则需要在config中进行配置

check_float 检查浮点数精度
    DECIMAL_PRECISION_RULES进行配置
    '容量': 3,
    '需要检查的字段名':需要的精度3位小数

check_primary_slave 检查主键从键是否重复
    PRIMARY_SLAVE_KEY_RULES进行配置

    '监测点': ['测试时间,风速（单位:m/s）', 'True'],
    '需要检查的主键':['需要检查的从键1,需要检查的从键2','允许主键重复']
    '机构名称': ['身份证号', 'False'],
    '需要检查的主键':['需要检查的从键1,需要检查的从键2','不允许主键重复']

check_key_scope 检查字段的值域
    FIELD_RANGE_RULES
    '年龄': (0, 200)
    '需要检查的字段':(范围内最小值，范围内最大值)

check_field_length 检查指定字段的长度
    FIELD_LENGTH_RULES
    
    只写一个值，则只支持一个长度，写两个值，则支持两个值的范围
    "个人ID": [13],   只支持13位
    "需要检查的字段名":[检查字段的位数]
    "设备号": [11,14],   支持11 -> 14位
    "需要检查的字段":[检查字段的最短长度，检查字段的最大长度]

check_field_enum
    FIELD_ENUM_RULES
    "性别": "男，女，保密",
    "需要检查的字段":"需要检查的字段允许出现的值所有类型" 只支持列出的内容

check_time_rule
    FIELD_DATE_RULES

    年  月  日  时  分  秒

    %Y %M  %D  %H  %M  %S

    "测试时间": ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"],

    需要什么格式就拼接什么格式
    例如只支持   2026/01/01   则   %Y/%M/%D
              2026+01+01    则   %Y+%M+%D
    一个字段支持多种格式

check_encrypt
    ENCRYPT_REQUIRED_FIELDS
    直接写出需要进行加密的字段名

    ENCRYPT_CONFIG
    "min_star_count": 1    需要至少包含一个 *
