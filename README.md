# 📊 电商订单数据质量校验框架

> 基于 Python + Pytest + Pandas 构建的数据质量校验框架，对订单数据做完整性 / 一致性 / 唯一性 / 时效性校验——数据科学专业做测试开发的差异化方向。

![pytest](https://img.shields.io/badge/pytest-5%2F5%20passed-brightgreen)
![python](https://img.shields.io/badge/python-3.12-blue)
![pandas](https://img.shields.io/badge/pandas-2.x-orange)

## 技术栈
Python · Pytest · Pandas · Pytest-HTML

## 项目亮点
- **规则化校验**：4 类数据质量规则（完整性 / 一致性 / 唯一性 / 时效性），5 条用例
- **大样本验证**：10 万行样本一次校验，检出 3,000 条脏数据
- **可视化报告**：`run_report.py` 生成 HTML 质量报告
- **可复用**：可作为数据团队质量门禁嵌入流水线

## 目录结构
```
data-quality-test/
├── test_order_quality.py  # 4 类校验规则（pytest 用例）
├── run_report.py          # 运行全部规则并生成 report.html
├── pytest.ini
├── requirements.txt
└── report.html            # 数据质量报告（运行后产生）
```

## 运行
```bash
pip install -r requirements.txt
pytest                 # 生成 pytest 报告
python run_report.py   # 生成 report.html 可视化报告
```

## 测试结果
- ✅ **5/5 用例全部通过**
- 10 万行样本 → 检出 3,000 条脏数据（缺失 / 重复 / 负值；状态枚举与时效性为 0 违规 sanity check）
