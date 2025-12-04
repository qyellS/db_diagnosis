import os
import re
import pandas as pd
import xlrd  # 直接用xlrd原生接口
from typing import List, Tuple
from datetime import datetime

# 支持的表格格式
SUPPORTED_FORMATS = ('.xlsx', '.xls', '.csv')
# 空字符匹配（去除空格/制表符后为空）
EMPTY_PATTERN = re.compile(r'^\s*$')
# 表头行最小有效列数（默认3）
MIN_HEADER_COLS = 3
# 配置：是否跳过第一列检查（True=跳过，False=不跳过）
SKIP_FIRST_COL = True
# 配置：跳过全空列的检查（True=跳过，False=不跳过）
SKIP_ALL_EMPTY_COLS = True


def read_xls_file_raw(file_path: str) -> pd.DataFrame:
    """用xlrd原生接口读取.xls文件，绕过pandas的版本校验"""
    try:
        workbook = xlrd.open_workbook(file_path)
        sheet = workbook.sheet_by_index(0)
        data = []
        for row_idx in range(sheet.nrows):
            row_data = []
            for col_idx in range(sheet.ncols):
                cell_value = sheet.cell_value(row_idx, col_idx)
                if sheet.cell_type(row_idx, col_idx) == xlrd.XL_CELL_DATE:
                    try:
                        cell_value = xlrd.xldate_as_datetime(cell_value, workbook.datemode).strftime('%Y-%m-%d')
                    except:
                        cell_value = str(cell_value)
                row_data.append(cell_value)
            data.append(row_data)
        return pd.DataFrame(data)
    except Exception as e:
        raise Exception(f"xlrd原生读取失败：{str(e)}")


def read_table_file(file_path: str) -> pd.DataFrame:
    """兼容读取.xlsx/.xls/.csv，彻底解决xlrd版本冲突"""
    file_ext = os.path.splitext(file_path)[1].lower()
    try:
        if file_ext == '.xlsx':
            return pd.read_excel(file_path, header=None, engine='openpyxl')
        elif file_ext == '.xls':
            return read_xls_file_raw(file_path)
        elif file_ext == '.csv':
            try:
                return pd.read_csv(file_path, header=None, encoding='utf-8-sig')
            except:
                return pd.read_csv(file_path, header=None, encoding='gbk')
        else:
            raise ValueError(f"不支持的文件格式：{file_ext}")
    except Exception as e:
        print(f"读取文件失败 {file_path}：{str(e)}")
        return pd.DataFrame()


def count_non_empty_cols(row_values: pd.Series) -> int:
    """统计一行中非空列的数量（去除空白字符后不为空）"""
    count = 0
    for val in row_values:
        val_str = str(val).strip() if not pd.isna(val) else ""
        if not EMPTY_PATTERN.match(val_str):
            count += 1
    return count


def is_col_all_empty(df: pd.DataFrame, col_idx: int) -> bool:
    """判断某一列是否全为空值（去除空白字符后）"""
    col_values = df.iloc[:, col_idx]
    for val in col_values:
        val_str = str(val).strip() if not pd.isna(val) else ""
        if not EMPTY_PATTERN.match(val_str):
            return False
    return True


def find_valid_header_row(df: pd.DataFrame) -> int:
    """仅通过列数查找有效表头行：取前10行中第一个非空列数≥3的行"""
    max_check_rows = min(10, df.shape[0])
    for row_idx in range(max_check_rows):
        row_values = df.iloc[row_idx]
        non_empty_cols = count_non_empty_cols(row_values)
        if non_empty_cols >= MIN_HEADER_COLS:
            return row_idx
    return 0


def is_empty_or_special_value(cell_value: str) -> Tuple[bool, str]:
    """判断单元格是否为空值或包含特殊字符"""
    if EMPTY_PATTERN.match(cell_value):
        return True, "空值(空白字符)"
    cell_lower = cell_value.lower()
    if cell_lower == 'null':
        return True, "特殊字符：null"
    elif cell_value == '/':
        return True, "特殊字符：/"
    elif cell_value == '——':
        return True, "特殊字符：——"
    return False, ""


def check_special_values(df: pd.DataFrame, header_row: int) -> List[Tuple[int, int, str]]:
    """检查有效表头后的行是否包含空值/特殊字符（跳过指定列/全空列）"""
    errors = []
    skip_cols = set()

    if SKIP_FIRST_COL and df.shape[1] >= 1:
        skip_cols.add(0)

    if SKIP_ALL_EMPTY_COLS:
        for col_idx in range(df.shape[1]):
            if is_col_all_empty(df, col_idx):
                skip_cols.add(col_idx)

    for row_idx in range(header_row + 1, df.shape[0]):
        row_values = df.iloc[row_idx]
        for col_idx in range(df.shape[1]):
            if col_idx in skip_cols:
                continue

            cell_value = str(row_values.iloc[col_idx]) if not pd.isna(row_values.iloc[col_idx]) else ""
            is_error, error_desc = is_empty_or_special_value(cell_value)
            if is_error:
                original_row = row_idx + 1
                original_col = col_idx + 1
                errors.append((original_row, original_col, error_desc))
    return errors


def traverse_folder(folder_path: str, output_file: str) -> None:
    """递归遍历文件夹，检查所有表格文件并输出结果"""
    if not os.path.exists(folder_path):
        print(f"错误：文件夹路径不存在 - {folder_path}")
        return

    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(f"检查结果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in SUPPORTED_FORMATS:
                    file_path = os.path.join(root, file)
                    df = read_table_file(file_path)
                    if df.empty:
                        continue  # 跳过空文件

                    header_row = find_valid_header_row(df)

                    # 检查文件是否有异常值（空值或特殊字符）
                    errors = check_special_values(df, header_row)
                    if errors:
                        # 记录有异常值的文件
                        output.write(f"\n======== 检查文件：{file_path} ========\n")
                        output.write(f"识别到有效表头行：第{header_row + 1}行\n")
                        output.write("❌ 发现异常值：\n")

                        # 只保留前10条错误记录
                        limited_errors = errors[:10]
                        for row, col, content in limited_errors:
                            output.write(f"   行{row} 列{col}：{content}\n")

                        # 如果超过10条，添加省略内容提示
                        if len(errors) > 10:
                            output.write("   ... 更多异常值已省略\n")


if __name__ == "__main__":
    folder_path = input("请输入要检查的文件夹路径：").strip()
    output_file = datetime.now().strftime("%Y%m%d") + "检查结果.txt"
    traverse_folder(folder_path, output_file)
    print(f"检查结果已保存到 {output_file}")
    input("...")
