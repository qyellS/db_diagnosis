"""
check_data_correctness.py

使用语义相似度（Sentence-BERT）判断单元格文本是否与列名语义匹配。

说明：为了避免在每次校验时重复加载模型（开销大且耗时），模块在导入时会尝试一次性初始化 SBERT 模型。
也提供 `init_semantic_model` 函数供上层在程序启动阶段显式调用以确保模型已加载。

如果环境中未安装 sentence_transformers 或模型加载失败，会退回到轻量的 token 覆盖率相似度算法以保证功能可用性。
"""

from typing import Tuple, Optional
import logging
import re

import pandas as pd

try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_SBERT = True
except Exception:
    SentenceTransformer = None
    util = None
    _HAS_SBERT = False

# 全局缓存的 SBERT 模型实例（仅加载一次）
_SBERT_MODEL = None
_SBERT_MODEL_NAME = 'paraphrase-MiniLM-L6-v2'

logger = logging.getLogger(__name__)


def init_semantic_model(model_name: Optional[str] = None, force: bool = False) -> None:
    """初始化并缓存 SentenceTransformer 模型。

    Args:
        model_name: 指定模型名称（如 'paraphrase-MiniLM-L6-v2'），默认为模块内默认值
        force: 若为 True，则强制重新加载模型（即使已加载过）

    备注：建议在程序启动阶段调用该函数以减少延迟。例如在主程序入口处调用一次。
    """
    global _SBERT_MODEL, _SBERT_MODEL_NAME, _HAS_SBERT
    if model_name:
        _SBERT_MODEL_NAME = model_name
    if _SBERT_MODEL is not None and not force:
        logger.debug("SBERT 模型已加载，跳过初始化")
        return
    if not _HAS_SBERT:
        logger.warning("未检测到 sentence_transformers，无法加载 SBERT 模型；将使用回退相似度算法")
        return
    try:
        logger.info(f"加载 SBERT 模型：{_SBERT_MODEL_NAME}（仅加载一次）")
        _SBERT_MODEL = SentenceTransformer(_SBERT_MODEL_NAME)
        logger.info("SBERT 模型加载完成")
    except Exception as e:
        _SBERT_MODEL = None
        logger.exception("加载 SBERT 模型失败：%s", e)


# 在模块导入时尝试加载模型，以便程序启动阶段即可可用（符合用户期望）
init_semantic_model()


def _is_numeric(value: str) -> bool:
    """判断字符串是否代表一个数值（包含整数、小数、带千分位的数字以及带%符号的简单形式）。

    规则：尝试去除常见格式化符号（逗号、%），再尝试转换为 float。
    返回 True 表示该单元格可被视为数值，应跳过语义文本匹配检查以避免误报。
    """
    if value is None:
        return False
    s = str(value).strip()
    if s == "":
        return False
    # 去掉常见的千位分隔符与百分号
    s_clean = s.replace(',', '').replace('%', '')
    # 若包含非数字且非小数点和负号的字符，则不是纯数值（例如 '100kg' 视为非数值）
    if re.search(r"[^0-9eE+\-\.]", s_clean):
        return False
    try:
        float(s_clean)
        return True
    except Exception:
        return False

def _basic_token_similarity(a: str, b: str) -> float:
    """轻量回退相似度计算：基于 token 覆盖率返回 0-1 的相似度分数。

    该方法在没有 SBERT 时用于退化处理，尽量避免完全失能。
    """
    if not a or not b:
        return 0.0
    a_tokens = set(re.findall(r"\w+", a.lower()))
    b_tokens = set(re.findall(r"\w+", b.lower()))
    if not a_tokens or not b_tokens:
        return 0.0
    inter = a_tokens & b_tokens
    union = a_tokens | b_tokens
    return len(inter) / len(union)


def check_data_correctness(cell_value: str, field_type: str, threshold: float = 0.7, lazy_load: bool = False) -> Tuple[bool, str]:
    """判断单元格文本是否与列名语义匹配。

    行为说明：
    - 优先使用已加载的 SBERT 模型计算余弦相似度（高质量）。
    - 若模型未加载：
        * 若 lazy_load=True，会尝试在调用时加载模型；
        * 否则使用轻量回退算法来计算相似度（基于 token 覆盖率）。
    - 当相似度小于 threshold 时，函数返回 (True, 描述)，表示判定为“不匹配”。

    参数：
        cell_value: 单元格的字符串值
        field_type: 列名或字段描述（用作语义参考）
        threshold: 相似度阈值（默认为 0.7）
        lazy_load: 是否允许在函数内部懒加载模型（默认为 False）

    返回：
        (is_error: bool, message: str)
    """
    # 标准化输入
    if cell_value is None:
        cell_value = ""
    if field_type is None:
        field_type = ""
    cell_value = str(cell_value).strip()
    field_type = str(field_type).strip()

    # 若列名或值为空，视为不进行语义判定（避免误报）
    if not field_type or not cell_value:
        return False, ""

    # 若单元格内容为数值（例如 '1000', '98.5%', '1,000' 等），则跳过语义匹配
    if _is_numeric(cell_value):
        return False, ""

    # 如果模型尚未加载，且允许 lazy_load，则尝试加载一次
    if _SBERT_MODEL is None:
        if lazy_load:
            init_semantic_model()
        # 如果仍然为空则使用回退算法
        if _SBERT_MODEL is None:
            sim = _basic_token_similarity(field_type, cell_value)
            if sim < threshold:
                return True, f"（回退相似度）数据与列名内容不匹配（相似度：{sim:.2f}）"
            return False, ""
    # 使用 SBERT 计算余弦相似度
    try:
        field_embedding = _SBERT_MODEL.encode(field_type, convert_to_tensor=True)
        cell_embedding = _SBERT_MODEL.encode(cell_value, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(field_embedding, cell_embedding).item()
    except Exception as e:
        logger.exception("使用 SBERT 计算相似度时出错，降级到回退算法：%s", e)
        sim = _basic_token_similarity(field_type, cell_value)
        if sim < threshold:
            return True, f"（回退相似度）数据与列名内容不匹配（相似度：{sim:.2f}）"
        return False, ""

    if similarity < threshold:
        return True, f"数据与列名内容不匹配（相似度：{similarity:.2f}）"
    return False, ""

test_cases = [
    ("苹果", "水果"),
    ("2023-10-01", "日期"),
    ("梁博文", "姓名"),
    ("北京市朝阳区", "地址"),
    ("1000", "数量"),
    ("This is a test.", "测试内容"),
    ("Unrelated text", "完全不相关的内容"),
    ("这个东西的颜色是蓝色", "颜色描述"),
]

for cell_val, field in test_cases:
    is_error, msg = check_data_correctness(cell_val, field, threshold=0.5)
    status = "不匹配" if is_error else "匹配"
    print(f"单元格值：'{cell_val}' | 列名：'{field}' => {status}. {msg}")