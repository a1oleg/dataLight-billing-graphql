"""Verify the recalculated columns in the original workbook."""
from __future__ import annotations

import openpyxl

PATH = "data/DeepSeek_peak_offpeak_октябрь_2026_Тест.xlsx"

workbook = openpyxl.load_workbook(PATH, read_only=True, data_only=True)
print("sheets:", workbook.sheetnames)
ws = workbook["Сырые логи"]
rows = ws.iter_rows(min_row=4, max_row=4, values_only=True)
header = list(next(rows))
print("header length:", len(header))
print("last columns:", header[31:])
index = {name: i for i, name in enumerate(header) if name}
calc_total = index["calculated_total_cost"]
diff_total = index["difference_total_cost"]
old_total = index["total_cost"]

count_calc = 0
count_diff = 0
row_count = 0
sample = {}
for row in ws.iter_rows(min_row=5, values_only=True):
    row_count += 1
    if row[calc_total] is not None:
        count_calc += 1
    if row[diff_total] is not None:
        count_diff += 1
    if row_count in (1, 5):
        sample[row_count] = {
            "total_cost": row[old_total],
            "calculated_total_cost": row[calc_total],
            "difference_total_cost": row[diff_total],
        }

print("data rows:", row_count)
print("calculated_total filled:", count_calc)
print("difference_total filled:", count_diff)
print("sample:", sample)
workbook.close()
