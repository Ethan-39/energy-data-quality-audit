# Energy Data Quality Audit

一个面向入门学习者的电表 CSV 质量审计命令行项目。它检查缺失/非法读数、同一电表的重复时间戳、非预期采样间隔，以及基于 MAD 的极端值候选项。它帮助回答“数据是否值得继续分析”，而不是替电表或账单作裁定。

## 运行

需要 Python 3.9 或更高版本，不需要安装第三方包。

```bash
python energy_data_quality_audit.py
python -m unittest discover -s tests -v
```

首次运行会在 `data/meter_readings.csv` 生成固定的教学样例；之后会读取该文件，因此可将其替换为自己有权处理的 CSV。列名需为 `timestamp,meter_id,energy_kwh`。也可指定文件：

```bash
python energy_data_quality_audit.py --input path/to/readings.csv
```

报告写入 `results/report.json` 和 `results/findings.csv`。预期采样间隔暂设为一小时，按项目的具体数据修改源码常量 `EXPECTED_INTERVAL`。

## 术语

- **数据质量审计**：检查格式、覆盖度、唯一性和数值分布的过程。
- **重复时间戳**：同一 `meter_id` 出现相同时间。项目将后续出现的行列为重复候选。
- **不规则间隔**：相邻有效时间戳差值不等于预设采样间隔。
- **MAD（中位数绝对偏差）**：一种较不易被极端值本身影响的离散程度估计。本项目以 modified z-score 大于 3.5 标记候选极端值。

## 数据和边界

样例是由固定公式生成的虚构数据，不代表真实电表精度或账单。异常标记可能来自合法的停机、换表、时区/夏令时处理或真实负荷变化。结果只供人工复核；不能据此认定设备损坏、篡改读数或要求供应方调整费用。时间戳按无时区本地时间处理。
