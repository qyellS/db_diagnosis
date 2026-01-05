import os
from datetime import datetime
from config import SUPPORTED_FORMATS, SKIP_TEMP_FILES, TEMP_FILE_PREFIX
from get_excel import read_table_file
from checker import find_valid_header_row, check_all_rules
from generate_excel import txt_to_excel


def process_single_file(file_path: str, output) -> None:
    """处理单个表格文件的校验逻辑"""
    # 跳过临时文件
    if SKIP_TEMP_FILES and os.path.basename(file_path).startswith(TEMP_FILE_PREFIX):
        print(f"跳过Excel临时文件：{file_path}")
        return

    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        output.write(f"\n======== 跳过文件：{file_path} ========\n")
        output.write(f"原因：不支持的文件格式（仅支持{SUPPORTED_FORMATS}）\n")
        return

    try:
        df = read_table_file(file_path)
        if df.empty:
            output.write(f"\n======== 跳过文件：{file_path} ========\n")
            output.write("原因：文件为空或无法解析\n")
            return

        header_row = find_valid_header_row(df)
        # 调用所有校验规则
        errors = check_all_rules(df, header_row)
        if errors:
            output.write(f"\n======== 检查文件：{file_path} ========\n")
            output.write(f"识别到有效表头行：第{header_row + 1}行\n")
            output.write("❌ 发现异常值：\n")
            # 输出所有错误（保留原有逻辑，未做数量限制）
            for row, col, content in errors:
                output.write(f"   行{row} 列{col}：{content}\n")
        else:
            output.write(f"\n======== 检查文件：{file_path} ========\n")
            output.write("✅ 未发现任何异常值\n")
    except Exception as e:
        output.write(f"\n======== 读取失败：{file_path} ========\n")
        output.write(f"错误原因：{str(e)}\n")
        print(f"读取文件失败 {file_path}：{str(e)}")


def traverse_folder(folder_path: str, output_file: str) -> None:
    """遍历文件夹并校验所有表格文件（原有逻辑）"""
    if not os.path.exists(folder_path):
        print(f"错误：文件夹路径不存在 - {folder_path}")
        return

    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(f"检查结果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # 判断输入是文件夹还是单个文件
        if os.path.isdir(folder_path):
            # 处理文件夹：遍历所有文件
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    process_single_file(file_path, output)
        elif os.path.isfile(folder_path):
            # 处理单个文件
            process_single_file(folder_path, output)
        else:
            output.write(f"错误：无效的路径 - {folder_path}\n")
            print(f"错误：无效的路径 - {folder_path}")


if __name__ == "__main__":
    # 修改输入提示，支持文件夹/单个文件
    input_path = input("请输入要检查的路径（文件夹/单个表格文件）：").strip('"').strip("'")

    # 校验路径是否存在
    if not os.path.exists(input_path):
        print(f"错误：路径不存在 - {input_path}")
        input("按回车键退出...")
        exit(1)

    # 生成输出文件名（保留原有命名规则）
    output_file = datetime.now().strftime("%Y%m%d") + "检查结果.txt"

    # 执行校验（兼容文件夹/单个文件）
    traverse_folder(input_path, output_file)

    # 输出完成提示并转换Excel
    print(f"\n检查完成！结果已保存到 {os.path.abspath(output_file)}")
    txt_path = os.path.abspath(output_file)
    txt_to_excel(txt_path)

    input("按回车键退出...")