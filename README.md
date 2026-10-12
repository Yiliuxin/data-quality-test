# 📊 电商订单数据质量校验框架

> 基于 Python + Pytest + Pandas 构建的数据质量校验框架，对订单数据做完整性 / 一致性 / 唯一性 / 时效性 / 有效性校验——数据科学专业做测试开发的差异化方向。

![pytest](https://img.shields.io/badge/pytest-19%2F19%20passed-brightgreen)
![python](https://img.shields.io/badge/python-3.12-blue)
![pandas](https://img.shields.io/badge/pandas-2.x-orange)

## 技术栈
Python · Pytest · Pandas · Pytest-HTML

## 项目亮点
- **规则化校验**：5 大类数据质量规则（完整性 / 唯一性 / 一致性 / 时效性 / 有效性），15 条核心规则
- **大样本验证**：10 万行样本一次校验，检出 8,361 条脏数据
- **可复用引擎**：15 条规则重构为纯函数 `quality_engine.py`，便于跨项目复用
- **框架自测**：`test_framework_selfcheck.py` 4 条用例验证引擎可靠性——干净数据误报校准、空表鲁棒性、统计离群检测（IQR）、ID 空格脏格式检测
- **可视化报告**：`run_report.py` 生成 HTML 质量报告（15 项规则一目了然）
- **可复用**：可作为数据团队质量门禁嵌入流水线

## 目录结构
```
data-quality-test/
├── quality_engine.py        # 15 条核心规则 + 2 条扩展检测器（纯函数，可复用）
├── test_order_quality.py    # 5 大类校验规则（15 条 pytest 用例）
├── test_framework_selfcheck.py  # 框架自测（4 条：误报校准/空表鲁棒/离群/脏格式）
├── run_report.py            # 运行全部规则并生成 report.html
├── pytest.ini
├── requirements.txt
└── report.html              # 数据质量报告（运行后产生）
```

## 运行
```bash
pip install -r requirements.txt
pytest                 # 生成 pytest 报告
python run_report.py   # 生成 report.html 可视化报告
```

## 测试结果
- ✅ **19/19 用例全部通过**（15 条核心规则 + 4 条框架自测）
- 10 万行样本 → 检出 8,361 条脏数据（空值 / 重复 / 非法金额 / 超限金额 / 非法状态 / 非法格式 / 越界时间 / 日期乱码 / NaN / 复合键重复 / 状态空值 / 时间窗口占比）
- 5 大类：完整性、唯一性、一致性（正负/上下界/枚举）、时效性（超前/早于下界）、有效性（user_id / order_id / 金额精度 / 日期格式 / 金额有限值）
- 框架自测：干净数据误报校准（15 规则全 0 违规）、空表鲁棒性、统计离群检测（IQR）、ID 空格脏格式检测
