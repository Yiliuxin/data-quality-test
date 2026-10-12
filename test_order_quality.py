# -*- coding: utf-8 -*-
"""
电商订单数据质量校验用例集（Python + Pytest + Pandas）
校验维度（5 大类 15 条核心规则）：完整性 / 唯一性 / 一致性 / 时效性 / 有效性(格式)
说明：自带 10 万行合成样本（注入多类脏数据，用于演示框架检出能力），开箱即跑。
规则实现见 quality_engine.py（纯函数，便于复用与自测）。
"""
import random

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
)

N = 100_000


def make_sample() -> pd.DataFrame:
    """生成合成订单样本，并注入多类脏数据用于演示。"""
    rng = range(N)
    df = pd.DataFrame({
        "order_id": [f"O{i:08d}" for i in rng],
        "user_id": [f"U{i % 5000}" for i in rng],
        "amount": [float(round(10 + (i % 990), 2)) for i in rng],
        "status": ["paid" if i % 3 else "refunded" for i in rng],
        "create_time": [(datetime(2026, 1, 1) + timedelta(minutes=i)).isoformat() for i in rng],
    })
    idx = list(range(N))
    random.seed(42)
    # 完整性：~1% user_id 置空
    for i in random.sample(idx, N // 100):
        df.loc[i, "user_id"] = None
    # 一致性：~1% 金额为负
    for i in random.sample(idx, N // 100):
        df.loc[i, "amount"] = -round(random.uniform(1, 100), 2)
    # 一致性：~0.5% 金额超限（超大值，疑似刷单/单位错误）
    for i in random.sample(idx, N // 200):
        df.loc[i, "amount"] = 9_999_999.0
    # 唯一性：~1% order_id 复制首行
    for i in random.sample(idx, N // 100):
        df.loc[i, "order_id"] = "O00000000"
    # 有效性：~0.5% user_id 格式非法（非 U+数字）
    for i in random.sample(idx, N // 200):
        df.loc[i, "user_id"] = "BAD"
    # 有效性：~0.5% order_id 格式非法（非 O+8 位数字）
    for i in random.sample(idx, N // 200):
        df.loc[i, "order_id"] = "X9"
    # 有效性：~0.5% 金额小数位超过 2 位
    for i in random.sample(idx, N // 200):
        df.loc[i, "amount"] = round(random.uniform(1, 100), 3)
    # 时效性：~0.5% 创建时间早于下界（系统时间/时区错乱）
    past = datetime(2020, 1, 1).isoformat()
    for i in random.sample(idx, N // 200):
        df.loc[i, "create_time"] = past
    # 一致性：~0.2% 状态非法（不在枚举内，如 'unknown'）
    for i in random.sample(idx, N // 500):
        df.loc[i, "status"] = "unknown"
    # 有效性：~0.2% 创建时间格式非法（非 ISO，如中文日期乱码）
    garbage_date = "2026年01月01日 09:30:00"
    for i in random.sample(idx, N // 500):
        df.loc[i, "create_time"] = garbage_date
    # 有效性：~0.1% 金额为 NaN（缺失/脏数值）
    for i in random.sample(idx, N // 1000):
        df.loc[i, "amount"] = float("nan")
    # 唯一性：~0.2% (user_id, create_time) 复合重复（疑似重复提交/双写）
    ref_user = df.loc[0, "user_id"]
    ref_time = df.loc[0, "create_time"]
    for i in random.sample(idx, N // 500):
        df.loc[i, "user_id"] = ref_user
        df.loc[i, "create_time"] = ref_time
    # 完整性：~0.2% 状态枚举列为空（关键业务字段缺失）
    for i in random.sample(idx, N // 500):
        df.loc[i, "status"] = None
    return df


@pytest.fixture(scope="module")
def orders():
    return make_sample()


def test_completeness(orders):
    """完整性：关键字段不应有空值。"""
    assert 0 < check_completeness_nulls(orders) < N * 0.02


def test_uniqueness(orders):
    """唯一性：order_id 重复率应低于 2%。"""
    dup = check_uniqueness_order_id(orders)
    assert 0 < dup < N * 0.02


def test_consistency_amount_positive(orders):
    """一致性：金额应为正数（样本应含负值）。"""
    assert 0 < check_consistency_amount_positive(orders)


def test_consistency_amount_upper(orders):
    """一致性：单笔金额不应超过上限（样本应含超大值）。"""
    assert 0 < check_consistency_amount_upper(orders)


def test_status_enum(orders):
    """一致性：应检出状态枚举之外的非法值（如 'unknown'）。"""
    assert 0 < check_status_enum(orders)


def test_timeliness_not_future(orders):
    """时效性：create_time 不应超前于当前时间。"""
    assert check_timeliness_not_future(orders) == 0


def test_timeliness_not_before_lower(orders):
    """时效性：create_time 不应早于下界（样本应含历史脏数据）。"""
    assert 0 < check_timeliness_not_before_lower(orders)


def test_validity_user_id_format(orders):
    """有效性：user_id 应符合 U+数字 格式。"""
    assert 0 < check_validity_user_id_format(orders)


def test_validity_order_id_format(orders):
    """有效性：order_id 应符合 O+8 位数字 格式。"""
    assert 0 < check_validity_order_id_format(orders)


def test_validity_amount_precision(orders):
    """有效性：金额小数位不应超过 2 位（样本应含 3 位小数）。"""
    assert 0 < check_validity_amount_precision(orders)


def test_validity_date_format(orders):
    """有效性：create_time 应为 ISO 8601 格式（样本应含中文日期等乱码）。"""
    assert 0 < check_validity_date_format(orders)


def test_validity_amount_finite(orders):
    """有效性：金额应为有限数值（样本应含 NaN）。"""
    assert 0 < check_validity_amount_finite(orders)


def test_uniqueness_composite_key(orders):
    """唯一性：组合键 (user_id, create_time) 不应重复（样本应含重复提交）。"""
    assert 0 < check_uniqueness_composite_key(orders)


def test_timeliness_freshness_ratio(orders):
    """时效性（数据新鲜度）：≥95% 的 create_time 应落在 [下界, 当前] 窗口内。"""
    assert check_timeliness_freshness_ratio(orders) >= 0.95


def test_completeness_status_not_null(orders):
    """完整性：状态枚举列不应有空值（样本应含空值）。"""
    assert 0 < check_completeness_status_not_null(orders)
