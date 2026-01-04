#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import pandas as pd
import os
import sys
import re
from datetime import datetime

# ===================== 内嵌DFA敏感词检测器 =====================
class DFAFilter:
    """基于确定性有限自动机（DFA）的敏感词检测器
    核心：仅检测文本中的敏感词，不做替换，返回检测结果
    """

    def __init__(self):
        # 敏感词字典树（核心数据结构）
        self.keyword_chains = {}
        # 字典树终止符（标记敏感词结束）
        self.delimit = '\x00'
        # 已加载的敏感词集合（用于快速查询）
        self.sensitive_words = set()

    def add(self, keyword):
        """添加单个敏感词到字典树
        :param keyword: 敏感词（字符串）
        """
        if not isinstance(keyword, str):
            keyword = str(keyword)
        # 统一转为小写，实现大小写不敏感匹配
        keyword = keyword.lower().strip()
        if not keyword or keyword in self.sensitive_words:
            return

        self.sensitive_words.add(keyword)
        level = self.keyword_chains
        for char in keyword:
            if char in level:
                level = level[char]
            else:
                # 为未存在的字符创建新节点
                for new_char in [char] + list(keyword[keyword.index(char) + 1:]):
                    level[new_char] = {}
                    last_level, last_char = level, new_char
                    level = level[new_char]
                # 标记敏感词结束
                last_level[last_char] = {self.delimit: 0}
                break
        # 若敏感词已存在，补充终止符
        if self.delimit not in level:
            level[self.delimit] = 0

    def parse(self, path):
        """从文件加载敏感词列表（每行一个敏感词）
        :param path: 敏感词文件路径（支持绝对/相对路径）
        """
        # 解析绝对路径（兼容相对路径）
        abs_path = os.path.abspath(path)
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                for line in f:
                    self.add(line.strip())
        except FileNotFoundError:
            raise FileNotFoundError(f"敏感词文件 {abs_path} 不存在，请检查路径！")
        except Exception as e:
            raise Exception(f"加载敏感词文件失败：{e}")

    def detect(self, message):
        """检测文本中的敏感词
        :param message: 待检测文本
        :return: dict - 检测结果
                {
                    'has_sensitive': bool,  # 是否包含敏感词
                    'sensitive_words': list  # 检测到的敏感词列表（去重）
                }
        """
        if not isinstance(message, str):
            message = str(message)
        # 统一转为小写匹配，不修改原文本
        message_lower = message.lower()
        detected_words = set()  # 存储检测到的敏感词（去重）
        start = 0

        while start < len(message_lower):
            level = self.keyword_chains
            step_ins = 0  # 记录匹配到的字符长度
            current_word = ""  # 存储当前匹配的敏感词
            # 从start位置开始遍历文本字符
            for char in message_lower[start:]:
                if char in level:
                    step_ins += 1
                    current_word += char
                    if self.delimit in level[char]:
                        # 匹配到完整敏感词，加入结果集
                        detected_words.add(current_word)
                        # 继续向后匹配（支持重叠敏感词）
                        level = level[char]
                    else:
                        level = level[char]
                else:
                    break
            start += 1

        # 整理检测结果
        result = {
            'has_sensitive': len(detected_words) > 0,
            'sensitive_words': list(detected_words)
        }
        return result

# 全局初始化敏感词检测器（避免重复加载）
_global_detector = None

def get_sensitive_detector(sensitive_file_path):
    """获取全局敏感词检测器（单例）
    :param sensitive_file_path: 敏感词文件绝对路径
    :return: DFAFilter实例
    """
    global _global_detector
    if _global_detector is None:
        detector = DFAFilter()
        # 加载敏感词文件
        detector.parse(sensitive_file_path)
        _global_detector = detector
    return _global_detector

# ===================== 校验规则核心逻辑 =====================
def check_value(cell_value, field_type):
    """兼容插件化接口，无实际逻辑"""
    return False, ""

def get_original_text_value(cell_val):
    """还原单元格值为原始文本形态"""
    if pd.isna(cell_val):
        return ""
    if isinstance(cell_val, str):
        return cell_val.strip()
    elif isinstance(cell_val, (int, float)):
        return str(cell_val).strip()
    else:
        return str(cell_val).strip()

def check_sensitive_word(df, header_row):
    """
    全表格敏感词检测（遍历所有单元格，不限制字段）
    :param df: 表格数据（保持原有读取格式）
    :param header_row: 表头行索引（仅用于区分表头/数据行，表头不检测）
    :return: 错误列表 [(行号, 列号, 错误描述)]
    """
    errors = []
    # 1. 添加项目根目录到Python路径，导入配置
    RULE_DIR = os.path.dirname(os.path.abspath(__file__))  # check_rules目录
    ROOT_DIR = os.path.dirname(RULE_DIR)  # 项目根目录（SetExcelRule）
    sys.path.append(ROOT_DIR)

    # 导入配置中的关键参数
    try:
        from config import EMPTY_PATTERN, get_sensitive_file_path
    except ImportError as e:
        print(f"导入配置文件失败：{e}")
        return errors

    # 2. 初始化敏感词检测器
    try:
        # 获取敏感词文件绝对路径（基于配置的相对路径）
        sensitive_file_path = get_sensitive_file_path()
        print(f"敏感词文件路径：{sensitive_file_path}")  # 调试用，可删除
        detector = get_sensitive_detector(sensitive_file_path)
    except Exception as e:
        print(f"敏感词检测器初始化失败：{e}")
        return errors

    # 3. 获取表头名称（用于错误提示）
    header_names = []
    for col_idx in range(df.shape[1]):
        if header_row < df.shape[0]:
            header_val = df.iloc[header_row, col_idx]
            header_name = str(header_val).strip() if not pd.isna(header_val) else f"列{col_idx+1}"
        else:
            header_name = f"列{col_idx+1}"
        header_names.append(header_name)

    # 4. 遍历所有数据行和列（跳过表头行）
    for row_idx in range(header_row + 1, df.shape[0]):
        for col_idx in range(df.shape[1]):
            # 提取并处理单元格值
            cell_val = df.iloc[row_idx, col_idx]
            processed_val = get_original_text_value(cell_val)

            # 空值/空白字符跳过检测
            if EMPTY_PATTERN.match(processed_val):
                continue

            # 检测敏感词
            detect_result = detector.detect(processed_val)
            if detect_result['has_sensitive']:
                # 转换为Excel风格的行列号（从1开始）
                excel_row = row_idx + 1
                excel_col = col_idx + 1
                # 整理敏感词列表
                sensitive_words = "、".join(detect_result['sensitive_words'])
                # 构造错误信息
                error_desc = (
                    f"内容包含敏感词：【{header_names[col_idx]}】列（行{excel_row}列{excel_col}），"
                    f"当前值='{processed_val}'，检测到敏感词：{sensitive_words}"
                )
                errors.append((excel_row, excel_col, error_desc))

    return errors

# ===================== 测试代码（可选） =====================
if __name__ == "__main__":
    # 测试用例：创建示例DataFrame
    test_df = pd.DataFrame({
        "姓名": ["张三", "李四", "王五"],
        "备注": ["正常文本", "法轮功是违法的", "我操操操针孔摄像机"],
        "测试时间": ["2025-10-01", "2025/10/01", "售假人民币不可取"]
    })
    # 执行敏感词检测
    errors = check_sensitive_word(test_df, header_row=0)
    # 打印检测结果
    if errors:
        print("检测到敏感词错误：")
        for err in errors:
            print(f"行{err[0]} 列{err[1]}：{err[2]}")
    else:
        print("未检测到敏感词")