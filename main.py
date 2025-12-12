import os
from datetime import datetime
from config import SUPPORTED_FORMATS, SKIP_TEMP_FILES, TEMP_FILE_PREFIX
from get_excel import read_table_file
from checker import find_valid_header_row, check_all_rules


def traverse_folder(folder_path: str, output_file: str) -> None:
    if not os.path.exists(folder_path):
        print(f"错误：文件夹路径不存在 - {folder_path}")
        return

    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(f"检查结果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if SKIP_TEMP_FILES and file.startswith(TEMP_FILE_PREFIX):
                    print(f"跳过Excel临时文件：{os.path.join(root, file)}")
                    continue

                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in SUPPORTED_FORMATS:
                    file_path = os.path.join(root, file)
                    try:
                        df = read_table_file(file_path)
                        if df.empty:
                            output.write(f"\n======== 跳过文件：{file_path} ========\n")
                            output.write("原因：文件为空或无法解析\n")
                            continue

                        header_row = find_valid_header_row(df)
                        # 改这里：调用check_all_rules
                        errors = check_all_rules(df, header_row)
                        if errors:
                            output.write(f"\n======== 检查文件：{file_path} ========\n")
                            output.write(f"识别到有效表头行：第{header_row + 1}行\n")
                            output.write("❌ 发现异常值：\n")
                            limited_errors = errors[:10]

                            # for row, col, content in limited_errors:
                            for row, col, content in errors:
                                output.write(f"   行{row} 列{col}：{content}\n")
                            # if len(errors) > 10:
                            #     output.write("   ... 更多异常值已省略\n")
                    except Exception as e:
                        output.write(f"\n======== 读取失败：{file_path} ========\n")
                        output.write(f"错误原因：{str(e)}\n")
                        print(f"读取文件失败 {file_path}：{str(e)}")


if __name__ == "__main__":
    folder_path = input("请输入要检查的文件夹路径：").strip()
    output_file = datetime.now().strftime("%Y%m%d") + "检查结果.txt"
    traverse_folder(folder_path, output_file)
    print(f"\n检查完成！结果已保存到 {os.path.abspath(output_file)}")
    input("按回车键退出...")