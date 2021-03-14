import datetime
from os import mkdir
from os.path import join

import xlsxwriter

from model import collection

DIR_NAME = "out"

try:
    mkdir(DIR_NAME)
except FileExistsError:
    pass

file_name = f"cats_{datetime.datetime.now()}.xlsx"

wb = xlsxwriter.Workbook(join(DIR_NAME, file_name))
ws = wb.add_worksheet("cats")
data = collection.find({"correct": {"$exists": True}})
ws.set_column(0, 2, 50)
ws.write_row(0, 0, ["Вопрос", "Ответы", "Правильный"])
ws.autofilter(0, 0, 0, 2)
for row, el in enumerate(data, start=1):
    question = el["question"]
    answers = el["answers"] if type(el["answers"]) == str else "\n".join(el["answers"])
    correct = el["correct"] if type(el["correct"]) == str else "\n".join(el["correct"])

    ws.write(row, 0, question)
    ws.write(row, 1, answers)
    ws.write(row, 2, correct)
wb.close()
