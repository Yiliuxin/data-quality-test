# -*- coding: utf-8 -*-
"""
数据质量校验报告生成器：运行全部规则，输出可视化 HTML 报告。
用法：python run_report.py
"""
import re

from test_order_quality import make_sample
import pandas as pd
from datetime import datetime

VALID_STATUS = {"paid", "refunded", "shipped", "cancelled"}
COLS = ["order_id", "user_id", "amount", "status", "create_time"]
USER_ID_RE = re.compile(r"^U\d+$")
ORDER_ID_RE = re.compile(r"^O\d{8}$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
LOWER_TIME = pd.Timestamp("2025-01-01")
AMOUNT_UPPER = 1_000_000


def _decimals(x):
    s = f"{x}"
    return len(s.split(".")[1]) if "." in s else 0


def run_checks(df: pd.DataFrame):
    rows = len(df)
    checks = []

    nulls = int(df[COLS].isnull().sum().sum())
    checks.append(("关键字段完整性(无空值)", f"空值 {nulls} 条", nulls < rows * 0.02))

    dup = int(df["order_id"].duplicated().sum())
    checks.append(("订单ID唯一性", f"重复 {dup} 条", 0 < dup < rows * 0.02))

    bad = int((df["amount"] <= 0).sum())
    checks.append(("金额合法性(>0)", f"非法 {bad} 条", bad >= 1))

    huge = int((df["amount"] > AMOUNT_UPPER).sum())
    checks.append(("金额上限(<=100万)", f"超限 {huge} 条", huge >= 1))

    invalid = int((~df["status"].isin(VALID_STATUS)).sum())
    checks.append(("状态枚举校验", f"非法 {invalid} 条", invalid >= 1))

    now = pd.Timestamp.now()
    ts = pd.to_datetime(df["create_time"], errors="coerce", format="mixed")
    future = int((ts > now).sum())
    checks.append(("时间时效性(不超前)", f"超前 {future} 条", future == 0))

    past = int((ts < LOWER_TIME).sum())
    checks.append(("时间下界(>=2025-01-01)", f"早于下界 {past} 条", past >= 1))

    bad_user = int((~df["user_id"].astype(str).str.match(USER_ID_RE)).sum())
    checks.append(("user_id格式(U+数字)", f"非法 {bad_user} 条", bad_user >= 1))

    bad_order = int((~df["order_id"].astype(str).str.match(ORDER_ID_RE)).sum())
    checks.append(("order_id格式(O+8位数字)", f"非法 {bad_order} 条", bad_order >= 1))

    bad_prec = int(df["amount"].apply(_decimals).gt(2).sum())
    checks.append(("金额精度(<=2位小数)", f"超精度 {bad_prec} 条", bad_prec >= 1))

    date_bad = int((~df["create_time"].astype(str).str.match(ISO_RE)).sum())
    checks.append(("日期格式合规(ISO)", f"乱码 {date_bad} 条", date_bad >= 1))

    amount_nan = int(df["amount"].isna().sum())
    checks.append(("金额有限值(非NaN)", f"NaN {amount_nan} 条", amount_nan >= 1))

    comp_dup = int(df.duplicated(subset=["user_id", "create_time"]).sum())
    checks.append(("复合唯一性(user_id+时间)", f"重复 {comp_dup} 条", comp_dup >= 1))

    ts_fr = pd.to_datetime(df["create_time"], errors="coerce")
    in_window = int(((ts_fr >= LOWER_TIME) & (ts_fr <= now)).sum())
    fresh_ratio = in_window / rows
    checks.append(("时间窗口内占比(>=95%)", f"{fresh_ratio:.3f}", fresh_ratio >= 0.95))

    status_null = int(df["status"].isnull().sum())
    checks.append(("状态字段非空", f"空值 {status_null} 条", status_null >= 1))

    return rows, checks


def build_html(rows, checks, dirty_total):
    passed = sum(1 for *_, ok in checks if ok)
    total = len(checks)
    color = "#2e7d32" if passed == total else "#c62828"
    rows_html = "".join(
        f"<tr><td>{name}</td><td>{detail}</td>"
        f"<td style='color:{'#2e7d32' if ok else '#c62828'};font-weight:bold'>"
        f"{'通过' if ok else '异常'}</td></tr>"
        for name, detail, ok in checks
    )
    return f"""<html><head><meta charset='utf-8'><title>数据质量报告</title></head>
<body style='font-family:微软雅黑;padding:24px'>
<h2>电商订单数据质量校验报告</h2>
<p>生成时间：{datetime.now():%Y-%m-%d %H:%M:%S}</p>
<p>校验样本：<b>{rows:,}</b> 行 ｜ 规则：<b>{total}</b> 项 ｜
通过：<b style='color:{color}'>{passed}/{total}</b> ｜ 检出脏数据：<b>{dirty_total:,}</b> 条</p>
<table border='1' cellspacing='0' cellpadding='8' style='border-collapse:collapse'>
<tr style='background:#1F4E79;color:#fff'><th>校验项</th><th>明细</th><th>结果</th></tr>
{rows_html}</table></body></html>"""


def main():
    df = make_sample()
    rows, checks = run_checks(df)
    nulls = int(df[COLS].isnull().sum().sum())
    dup = int(df["order_id"].duplicated().sum())
    bad = int((df["amount"] <= 0).sum())
    huge = int((df["amount"] > AMOUNT_UPPER).sum())
    invalid = int((~df["status"].isin(VALID_STATUS)).sum())
    ts = pd.to_datetime(df["create_time"], errors="coerce", format="mixed")
    past = int((ts < LOWER_TIME).sum())
    bad_user = int((~df["user_id"].astype(str).str.match(USER_ID_RE)).sum())
    bad_order = int((~df["order_id"].astype(str).str.match(ORDER_ID_RE)).sum())
    bad_prec = int(df["amount"].apply(_decimals).gt(2).sum())
    date_bad = int((~df["create_time"].astype(str).str.match(ISO_RE)).sum())
    amount_nan = int(df["amount"].isna().sum())
    comp_dup = int(df.duplicated(subset=["user_id", "create_time"]).sum())
    status_null = int(df["status"].isnull().sum())
    dirty = nulls + dup + bad + huge + invalid + past + bad_user + bad_order + bad_prec + date_bad + amount_nan + comp_dup + status_null
    html = build_html(rows, checks, dirty)
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)
    passed = sum(1 for *_, ok in checks if ok)
    print(f"样本 {rows:,} 行 | 规则 {len(checks)} 项 | 通过 {passed}/{len(checks)} | 检出脏数据 {dirty:,} 条 | 报告已生成 report.html")


if __name__ == "__main__":
    main()
