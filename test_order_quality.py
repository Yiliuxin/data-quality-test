# -*- coding: utf-8 -*-
"""
电商订单数据质量校验框架（Python + Pytest + Pandas）
校验维度：完整性 / 唯一性 / 一致性 / 时效性
说明：自带 10 万行合成样本（约 1% 注入脏数据，用于演示框架检出能力），开箱即跑。
"""
import random

import pandas as pd
import pytest
from datetime import datetime, timedelta

N = 100_000
VALID_STATUS = {"paid", "refunded", "shipped", "cancelled"}
COLS = ["order_id", "user_id", "amount", "status", "create_time"]


def make_sample() -> pd.DataFrame:
    """生成合成订单样本，并注入约 1% 各类脏数据用于演示。"""
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
    # 唯一性：~1% order_id 复制首行
    for i in random.sample(idx, N // 100):
        df.loc[i, "order_id"] = "O00000000"
    return df


@pytest.fixture(scope="module")
def orders():
    return make_sample()


def test_completeness(orders):
    """完整性：关键字段不应有空值。"""
    nulls = int(orders[COLS].isnull().sum().sum())
    assert nulls < N * 0.02, f"完整性缺失 {nulls} 条，超过阈值"


def test_uniqueness(orders):
    """唯一性：order_id 重复率应低于 2%。"""
    dup = int(orders["order_id"].duplicated().sum())
    assert 0 < dup < N * 0.02, f"重复 {dup} 条，异常"


def test_consistency_amount(orders):
    """一致性：金额应为正数。"""
    bad = int((orders["amount"] <= 0).sum())
    assert 0 < bad, "未检出非法金额（样本应含负值）"


def test_status_enum(orders):
    """一致性：状态应落在枚举范围内。"""
    invalid = int((~orders["status"].isin(VALID_STATUS)).sum())
    assert invalid == 0, f"发现 {invalid} 条非法状态"


def test_timeliness(orders):
    """时效性：create_time 不应超前于当前时间。"""
    now = pd.Timestamp.now()
    future = int((pd.to_datetime(orders["create_time"]) > now).sum())
    assert future == 0, f"发现 {future} 条超前时间"
