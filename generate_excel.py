import os
import re
import pandas as pd


def txt_to_excel(txt_path):
    """
    自动识别所有类型的错误标识，将txt文件内容按错误类型分类写入Excel
    :param txt_path: txt文件的路径
    """
    # 初始化字典存储不同错误类型的内容
    error_data = {}

    # 正则表达式：匹配"行X 列X："之后、第一个"："之前的错误类型
    # 匹配规则：
    # 1. 先匹配并跳过 "行\d+ 列\d+：" 部分
    # 2. 捕获直到下一个冒号前的所有内容作为错误类型
    pattern = re.compile(r'行\d+ 列\d+：([^：]+)：?')

    # 读取txt文件内容
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误：未找到文件 {txt_path}")
        return
    except Exception as e:
        print(f"读取文件出错：{e}")
        return

    # 处理每一行数据
    for line in lines:
        # 去除首尾空格和换行符
        clean_line = line.strip()
        if not clean_line:  # 跳过空行
            continue

        # 使用正则表达式提取错误类型
        match = pattern.search(clean_line)
        if match:
            # 提取匹配到的错误类型（去除首尾空格）
            error_type = match.group(1).strip()
            # 如果该错误类型不存在于字典中，初始化空列表
            if error_type not in error_data:
                error_data[error_type] = []
            # 将当前行添加到对应错误类型的列表中
            error_data[error_type].append(clean_line)

    # 若未识别到任何错误类型，给出提示并退出
    if not error_data:
        print("未识别到任何错误类型，请检查txt文件内容格式")
        return

    # 找出最长的列表长度，用于补全其他列表（保证Excel列长度一致）
    max_len = max(len(v) for v in error_data.values())

    # 补全每个列表到相同长度（空值填充）
    for key in error_data:
        if len(error_data[key]) < max_len:
            error_data[key] += [''] * (max_len - len(error_data[key]))

    # 创建DataFrame并写入Excel
    df = pd.DataFrame(error_data)

    # 生成Excel文件名（与txt同名，后缀改为xlsx）
    excel_path = os.path.splitext(txt_path)[0] + '.xlsx'

    # 写入Excel文件
    try:
        df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"Excel文件已生成：{excel_path}")
        print(f"自动识别的错误类型（表头）：{list(error_data.keys())}")
    except Exception as e:
        print(f"写入Excel出错：{e}")
        return


# 示例调用
if __name__ == "__main__":
    # 请将此处替换为你的txt文件实际路径
    txt_file_path = r"20260104检查结果.txt"
    txt_to_excel(txt_file_path)