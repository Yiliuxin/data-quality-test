# -*- coding: utf-8 -*-
"""
数据质量校验报告生成器：运行全部规则，输出可视化 HTML 报告。
用法：python run_report.py
"""
from test_order_quality import make_sample
import pandas as pd
from datetime import datetime

VALID_STATUS = {"paid", "refunded", "shipped", "cancelled"}
COLS = ["order_id", "user_id", "amount", "status", "create_time"]


def run_checks(df: pd.DataFrame):
    rows = len(df)
    checks = []

    nulls = int(df[COLS].isnull().sum().sum())
    checks.append(("关键字段完整性(无空值)", f"空值 {nulls} 条", nulls < rows * 0.02))

    dup = int(df["order_id"].duplicated().sum())
    checks.append(("订单ID唯一性", f"重复 {dup} 条", 0 < dup < rows * 0.02))

    bad = int((df["amount"] <= 0).sum())
    checks.append(("金额合法性(>0)", f"非法 {bad} 条", bad >= 1))

    invalid = int((~df["status"].isin(VALID_STATUS)).sum())
    checks.append(("状态枚举合法", f"非法 {invalid} 条", invalid == 0))

    now = pd.Timestamp.now()
    future = int((pd.to_datetime(df["create_time"]) > now).sum())
    checks.append(("时间时效性(不超前)", f"超前 {future} 条", future == 0))

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
    invalid = int((~df["status"].isin(VALID_STATUS)).sum())
    dirty = nulls + dup + bad + invalid
    html = build_html(rows, checks, dirty)
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)
    passed = sum(1 for *_, ok in checks if ok)
    print(f"样本 {rows:,} 行 | 规则 {len(checks)} 项 | 通过 {passed}/{len(checks)} | 检出脏数据 {dirty:,} 条 | 报告已生成 report.html")


if __name__ == "__main__":
    main()
