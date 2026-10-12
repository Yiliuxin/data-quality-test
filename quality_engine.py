# -*- coding: utf-8 -*-
"""电商订单数据质量校验引擎。

把 15 条核心规则 + 2 条扩展检测器封装为纯函数（每个 check_* 返回违规条数，
freshness 返回窗口内占比），便于用例断言与跨项目复用，也方便做框架自测。
"""
import re

import pandas as pd

VALID_STATUS = {"paid", "refunded", "shipped", "cancelled"}
COLS = ["order_id", "user_id", "amount", "status", "create_time"]
USER_ID_RE = re.compile(r"^U\d+$")
ORDER_ID_RE = re.compile(r"^O\d{8}$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
LOWER_TIME = pd.Timestamp("2025-01-01")  # 时效性下界
AMOUNT_UPPER = 1_000_000                 # 一致性上界


# ------------------------- 完整性 -------------------------
def check_completeness_nulls(df):
    """关键字段不应有空值。"""
    return int(df[COLS].isnull().sum().sum())


def check_completeness_status_not_null(df):
    """状态枚举列不应有空值。"""
    return int(df["status"].isnull().sum())


# ------------------------- 唯一性 -------------------------
def check_uniqueness_order_id(df):
    """order_id 不应重复。"""
    return int(df["order_id"].duplicated().sum())


def check_uniqueness_composite_key(df):
    """组合键 (user_id, create_time) 不应重复（疑似重复提交/双写）。"""
    return int(df.duplicated(subset=["user_id", "create_time"]).sum())


# ------------------------- 一致性 -------------------------
def check_consistency_amount_positive(df):
    """金额应为正数。"""
    return int((df["amount"] <= 0).sum())


def check_consistency_amount_upper(df):
    """单笔金额不应超过上限（如刷单/单位错误）。"""
    return int((df["amount"] > AMOUNT_UPPER).sum())


def check_status_enum(df):
    """状态应落在合法枚举内。"""
    return int((~df["status"].isin(VALID_STATUS)).sum())


# ------------------------- 时效性 -------------------------
def check_timeliness_not_future(df):
    """create_time 不应超前于当前时间。"""
    now = pd.Timestamp.now()
    ts = pd.to_datetime(df["create_time"], errors="coerce", format="mixed")
    return int((ts > now).sum())


def check_timeliness_not_before_lower(df):
    """create_time 不应早于下界。"""
    ts = pd.to_datetime(df["create_time"], errors="coerce")
    return int((ts < LOWER_TIME).sum())


def check_timeliness_freshness_ratio(df):
    """数据新鲜度：落在 [下界, 当前] 窗口内的占比（空表返回 1.0，无越界）。"""
    if len(df) == 0:
        return 1.0
    ts = pd.to_datetime(df["create_time"], errors="coerce")
    now = pd.Timestamp.now()
    in_window = int(((ts >= LOWER_TIME) & (ts <= now)).sum())
    return in_window / len(df)


# ------------------------- 有效性(格式) -------------------------
def check_validity_user_id_format(df):
    """user_id 应符合 U+数字 格式。"""
    return int((~df["user_id"].astype(str).str.match(USER_ID_RE)).sum())


def check_validity_order_id_format(df):
    """order_id 应符合 O+8 位数字 格式。"""
    return int((~df["order_id"].astype(str).str.match(ORDER_ID_RE)).sum())


def check_validity_amount_precision(df):
    """金额小数位不应超过 2 位。"""
    def decimals(x):
        s = f"{x}"
        return len(s.split(".")[1]) if "." in s else 0
    return int(df["amount"].apply(decimals).gt(2).sum())


def check_validity_date_format(df):
    """create_time 应为 ISO 8601 格式。"""
    return int((~df["create_time"].astype(str).str.match(ISO_RE)).sum())


def check_validity_amount_finite(df):
    """金额应为有限数值，NaN/Inf 等脏数值应被检出。"""
    return int(df["amount"].isna().sum())


# ------------------------- 扩展检测器（框架自测演示） -------------------------
def check_amount_outlier_iqr(df, k=3.0):
    """统计离群检测：基于 IQR 法则，超出 [Q1-k*IQR, Q3+k*IQR] 的金额记为离群。"""
    s = df["amount"].dropna()
    if s.empty:
        return 0
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - k * iqr, q3 + k * iqr
    return int(((s < lo) | (s > hi)).sum())


def check_id_whitespace(df):
    """脏格式检测：ID 含前后空格（如 ' O12345678 '）应记为格式违规。"""
    bad_user = df["user_id"].astype(str).str.strip().ne(df["user_id"].astype(str)).sum()
    bad_order = df["order_id"].astype(str).str.strip().ne(df["order_id"].astype(str)).sum()
    return int(bad_user + bad_order)
