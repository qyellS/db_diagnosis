import pandas as pd
import xlrd  # 直接用xlrd原生接口
import os
from config import SUPPORTED_FORMATS

def read_xls_file_raw(file_path: str) -> pd.DataFrame:
    """用xlrd原生接口读取.xls文件，绕过pandas的版本校验（新增HTML伪Excel兼容）"""
    try:
        # 先尝试常规xlrd读取
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
        # 捕获BOF错误，尝试按HTML读取（兼容lxml缺失的情况）
        if "Expected BOF record" in str(e):
            try:
                # 用pandas读取HTML表格（兼容伪Excel的HTML文件）
                df = pd.read_html(file_path)[0]
                return df
            except ImportError:
                raise Exception("解析HTML伪Excel文件失败：缺少lxml依赖（执行pip install lxml安装）")
            except Exception as html_e:
                raise Exception(f"既非有效XLS也非可解析的HTML表格：{str(html_e)}")
        else:
            raise Exception(f"xlrd原生读取失败：{str(e)}")


def read_table_file(file_path: str) -> pd.DataFrame:
    """兼容读取.xlsx/.xls/.csv，彻底解决xlrd版本冲突（含HTML伪Excel+权限兼容）"""
    file_ext = os.path.splitext(file_path)[1].lower()
    # 跳过无权限的文件（捕获权限错误）
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
    except PermissionError:
        raise Exception("权限拒绝：文件被占用/无读取权限")
    except Exception as e:
        raise Exception(f"读取失败：{str(e)}")