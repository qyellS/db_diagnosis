运行main.py，输入需要检查表格路径，检查结果保存到main同级目录下，

每个功能都在check_rules中，增加新功能在check_rules中创建新py文件

新的代码创建完毕后，须在config.py中 ENABLED_RULES 写入新增加的规则代码文件名

修改 checker.py 导入新的规则应用。