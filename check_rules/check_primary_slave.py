import pandas as pd
import os
import sys
import re
from config import PRIMARY_SLAVE_KEY_RULES, EMPTY_PATTERN

def check_value(cell_value, field_type):
    """兼容插件化接口，无实际逻辑"""
    return False, ""


def check_primary_slave_duplicate(df, header_row):
    """
    多主键-从键组合重复校验（支持按配置控制主键是否允许重复，静默匹配失败，支持联合主键）
    :param df: 表格数据
    :param header_row: 表头行索引
    :return: 错误列表 [(行号, 列号, 错误描述)]
    """
    errors = []
    # 1. 添加根目录到Python路径，导入核心配置
    RULE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(RULE_DIR)
    sys.path.append(ROOT_DIR)

    # 2. 预处理表头：构建「清理后表头→列索引」映射（用于模糊匹配）
    header_clean_to_col = {}  # 清理后的表头 → 列索引
    header_col_to_original = {}  # 列索引 → 原始表头（仅用于调试）
    for col_idx in range(df.shape[1]):
        # 提取原始表头并清理
        header_original = str(df.iloc[header_row, col_idx]).strip() if not pd.isna(df.iloc[header_row, col_idx]) else ""
        # 清理规则：去除所有特殊字符+空格，转小写（最大化兼容）
        header_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', header_original).lower()
        if header_clean:  # 仅保留非空表头
            header_clean_to_col[header_clean] = col_idx
            header_col_to_original[col_idx] = header_original

    # 3. 遍历所有主键-从键规则（支持多组+联合主键）
    for primary_keys_str, rule_config in PRIMARY_SLAVE_KEY_RULES.items():
        # ===== 解析新格式配置 =====
        # 规则配置：[从键字符串, 是否允许主键重复(字符串True/False)]
        slave_keys_str = rule_config[0] if len(rule_config) >= 1 else ""
        # 解析是否允许主键重复（兼容大小写/字符串转布尔）
        allow_primary_dup_str = rule_config[1].strip().lower() if len(rule_config) >= 2 else "true"
        allow_primary_dup = True if allow_primary_dup_str == "true" else False

        # ===== 解析规则：支持联合主键（|分隔）、多从键（,分隔）=====
        # 解析联合主键（如：城市名称|区县名称 → ['城市名称', '区县名称']）
        primary_keys = [pk.strip() for pk in primary_keys_str.split('|') if pk.strip()]
        # 解析从键（兼容中英文逗号）
        slave_keys = [sk.strip() for sk in slave_keys_str.replace('，', ',').split(',') if sk.strip()]

        # ===== 步骤1：匹配所有主键列（静默跳过匹配失败的规则）=====
        primary_col_idxs = []  # 联合主键对应的列索引列表
        for pk in primary_keys:
            # 清理主键关键词（和表头清理规则一致）
            pk_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', pk).lower()
            # 模糊匹配：表头包含关键词 或 关键词包含表头
            match_col_idx = None
            for h_clean, col_idx in header_clean_to_col.items():
                if pk_clean in h_clean or h_clean in pk_clean:
                    match_col_idx = col_idx
                    break
            if match_col_idx is None:
                # 主键匹配失败 → 静默跳过当前规则，不输出错误
                primary_col_idxs = []
                break
            primary_col_idxs.append(match_col_idx)
        if not primary_col_idxs:
            continue  # 有主键未匹配 → 跳过当前规则

        # ===== 步骤2：匹配所有从键列（静默跳过匹配失败的规则）=====
        slave_col_idxs = []  # 从键对应的列索引列表
        slave_key_names = []  # 保留原始从键名（用于错误描述）
        for sk in slave_keys:
            sk_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', sk).lower()
            match_col_idx = None
            for h_clean, col_idx in header_clean_to_col.items():
                if sk_clean in h_clean or h_clean in sk_clean:
                    match_col_idx = col_idx
                    break
            if match_col_idx is None:
                # 从键匹配失败 → 静默跳过组合校验，但不影响主键校验
                slave_col_idxs = []
                break
            slave_col_idxs.append(match_col_idx)
            slave_key_names.append(sk)

        # ===== 新增：按配置校验主键单独重复 =====
        if not allow_primary_dup:  # 不允许主键重复时才校验
            primary_only_dict = {}  # 主键组合 → (主键描述, 行号列表)
            for row_idx in range(header_row + 1, df.shape[0]):
                # 提取联合主键值（任意主键为空则跳过）
                primary_vals = []
                primary_vals_desc = []  # 用于错误描述的主键-值
                is_primary_empty = False
                for pk, col_idx in zip(primary_keys, primary_col_idxs):
                    val = df.iloc[row_idx, col_idx]
                    val_str = str(val).strip() if not pd.isna(val) else ""
                    if EMPTY_PATTERN.match(val_str):
                        is_primary_empty = True
                        break
                    primary_vals.append(val_str)
                    primary_vals_desc.append(f"{pk}={val_str}")
                if is_primary_empty:
                    continue  # 主键为空 → 跳过该行

                # 构建主键组合键
                primary_key = tuple(primary_vals)
                excel_row = row_idx + 1  # 转换为Excel实际行号
                primary_desc = " + ".join(primary_vals_desc)

                # 记录主键对应的行号和描述
                if primary_key not in primary_only_dict:
                    primary_only_dict[primary_key] = (primary_desc, [])
                primary_only_dict[primary_key][1].append(excel_row)

            # 生成主键重复错误
            for primary_key, (primary_desc, row_nums) in primary_only_dict.items():
                if len(row_nums) > 1:
                    error_desc = (
                        f"主键重复（不允许）：[{primary_desc}] | "
                        f"重复行：{','.join(map(str, row_nums))}"
                    )
                    # 列号标为1（行级错误），错误行号取第二个重复行
                    errors.append((row_nums[1], 1, error_desc))

        # ===== 原有：主键+从键组合重复校验（仅当从键匹配成功时执行）=====
        if not slave_col_idxs:
            continue  # 有从键未匹配 → 跳过组合校验

        combo_dict = {}  # 组合值 → (主键描述, 从键描述, 行号列表)
        # 遍历数据行（仅处理表头后的行）
        for row_idx in range(header_row + 1, df.shape[0]):
            # 提取联合主键值（任意主键为空则跳过）
            primary_vals = []
            primary_vals_desc = []  # 用于错误描述的主键-值
            is_primary_empty = False
            for pk, col_idx in zip(primary_keys, primary_col_idxs):
                val = df.iloc[row_idx, col_idx]
                val_str = str(val).strip() if not pd.isna(val) else ""
                if EMPTY_PATTERN.match(val_str):
                    is_primary_empty = True
                    break
                primary_vals.append(val_str)
                primary_vals_desc.append(f"{pk}={val_str}")
            if is_primary_empty:
                continue  # 主键为空 → 跳过该行

            # 提取从键值（允许从键为空，但参与组合）
            slave_vals = []
            slave_vals_desc = []
            for sk, col_idx in zip(slave_key_names, slave_col_idxs):
                val = df.iloc[row_idx, col_idx]
                val_str = str(val).strip() if not pd.isna(val) else ""
                slave_vals.append(val_str)
                slave_vals_desc.append(f"{sk}={val_str}")

            # 构建组合键（联合主键+所有从键）
            combo_key = (tuple(primary_vals), tuple(slave_vals))
            excel_row = row_idx + 1  # 转换为Excel实际行号
            primary_desc = " + ".join(primary_vals_desc)
            slave_desc = " + ".join(slave_vals_desc)

            # 记录组合键对应的描述和行号（修复原代码作用域问题）
            if combo_key not in combo_dict:
                combo_dict[combo_key] = (primary_desc, slave_desc, [])
            combo_dict[combo_key][2].append(excel_row)

        # ===== 步骤4：生成组合重复错误（仅输出有重复的情况）=====
        for combo_key, (primary_desc, slave_desc, row_nums) in combo_dict.items():
            if len(row_nums) > 1:
                # 拼接错误描述
                error_desc = (
                    f"组合重复：[{primary_desc}] + [{slave_desc}] | "
                    f"重复行：{','.join(map(str, row_nums))}"
                )
                # 列号标为1（行级错误），错误行号取第二个重复行
                errors.append((row_nums[1], 1, error_desc))

    return errors