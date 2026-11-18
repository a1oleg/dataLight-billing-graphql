"""Check the discrepancy_reason column in the original workbook."""
from __future__ import annotations

from collections import Counter

import openpyxl

PATH = "data/DeepSeek_peak_offpeak_октябрь_2026_Тест.xlsx"

workbook = openpyxl.load_workbook(PATH, read_only=True, data_only=True)
ws = workbook["Сырые логи"]
header = list(next(ws.iter_rows(min_row=4, max_row=4, values_only=True)))
print("columns:", len(header), "last:", header[-3:])
index = {name: i for i, name in enumerate(header) if name}
reason_index = index["discrepancy_reason"]
calc_total = index["calculated_total_cost"]
diff_total = index["difference_total_cost"]
old_total = index["total_cost"]

counts = Counter()
rows = 0
samples = {}
for offset, row in enumerate(ws.iter_rows(min_row=5, values_only=True)):
    rows += 1
    counts[row[reason_index]] += 1
    if offset in (0, 4):
        samples[offset + 5] = {
            "reason": row[reason_index],
            "total_cost": row[old_total],
            "calculated_total_cost": row[calc_total],
            "difference_total_cost": row[diff_total],
        }

print("data rows:", rows)
print("reasons:", counts)
print("samples:", samples)
workbook.close()
