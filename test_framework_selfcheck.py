# -*- coding: utf-8 -*-
"""
框架自测：校验引擎自身的可靠性（测试测试框架）。
- 干净数据误报校准：15 条核心规则在合规数据上应全部报告 0 违规（无误报）。
- 空表鲁棒性：空 DataFrame 下所有检查不应抛异常。
- 扩展检测器演示：统计离群检测、ID 空格脏格式检测。
"""
import pandas as pd
import pytest
from datetime import datetime, timedelta

from quality_engine import (
    check_completeness_nulls,
    check_completeness_status_not_null,
    check_uniqueness_order_id,
    check_uniqueness_composite_key,
    check_consistency_amount_positive,
    check_consistency_amount_upper,
    check_status_enum,
    check_timeliness_not_future,
    check_timeliness_not_before_lower,
    check_timeliness_freshness_ratio,
    check_validity_user_id_format,
    check_validity_order_id_format,
    check_validity_amount_precision,
    check_validity_date_format,
    check_validity_amount_finite,
    check_amount_outlier_iqr,
    check_id_whitespace,
)

COLS = ["order_id", "user_id", "amount", "status", "create_time"]
N = 5000


def make_clean() -> pd.DataFrame:
    """生成完全合规的样本（无任何脏数据），用于误报校准。"""
    rng = range(N)
    base = datetime(2026, 1, 1)
    return pd.DataFrame({
        "order_id": [f"O{i:08d}" for i in rng],
        "user_id": [f"U{i % 500}" for i in rng],
        "amount": [float(round(10 + (i % 990), 2)) for i in rng],
        "status": ["paid" if i % 3 else "refunded" for i in rng],
        "create_time": [(base + timedelta(minutes=i)).isoformat() for i in rng],
    })


CORE_CHECKS = (
    check_completeness_nulls,
    check_completeness_status_not_null,
    check_uniqueness_order_id,
    check_uniqueness_composite_key,
    check_consistency_amount_positive,
    check_consistency_amount_upper,
    check_status_enum,
    check_timeliness_not_future,
    check_timeliness_not_before_lower,
    check_validity_user_id_format,
    check_validity_order_id_format,
    check_validity_amount_precision,
    check_validity_date_format,
    check_validity_amount_finite,
)


def test_clean_data_no_false_positive():
    """误报校准：完全合规数据下，全部 15 条核心规则应报告 0 违规。"""
    df = make_clean()
    for fn in CORE_CHECKS:
        assert fn(df) == 0, f"{fn.__name__} 在干净数据上误报 {fn(df)} 条"
    assert check_timeliness_freshness_ratio(df) >= 0.999


def test_empty_dataframe_no_crash():
    """鲁棒性：空 DataFrame 下所有检查不应抛异常，且违规数为 0。"""
    df = pd.DataFrame(columns=COLS)
    for fn in CORE_CHECKS + (check_amount_outlier_iqr, check_id_whitespace):
        assert fn(df) == 0
    assert check_timeliness_freshness_ratio(df) == 1.0


def test_outlier_detection():
    """离群检测：注入极端金额（超大/超小），IQR 检测器应能检出。"""
    df = make_clean()
    df.loc[0, "amount"] = 1e9    # 超大离群
    df.loc[1, "amount"] = -1e9   # 超小离群
    assert check_amount_outlier_iqr(df) >= 2


def test_whitespace_id_detection():
    """脏格式检测：ID 前后带空格（' O00000000 '）应被检出。"""
    df = make_clean()
    df.loc[0, "order_id"] = " O00000000 "
    df.loc[1, "user_id"] = " U000 "
    assert check_id_whitespace(df) >= 2
