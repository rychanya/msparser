from itertools import chain, combinations
from random import choice
from typing import Iterable, List, Tuple, Union

from bson import ObjectId
from openpyxl import Workbook
from openpyxl.styles import Alignment, NamedStyle
from openpyxl.worksheet import worksheet
from pydantic import BaseModel, Field
from pymongo import MongoClient

client = MongoClient()
db = client.get_database("qa")
collection = db.get_collection("1")


class QA(BaseModel):
    id: str = Field(None, alias="_id")
    type: str
    question: str
    answers: List[str]
    correct: Union[None, str, List[str]]
    incorrect: List[Union[str, List[str]]] = []

    def get_answer(self):
        if self.correct is not None:
            return self.correct
        if self.type == "Выберите один правильный вариант":
            if self.incorrect:
                ans = set(self.answers).difference(self.incorrect)
                if ans:
                    return choice(list(ans))
            return choice(self.answers)
        elif self.type == "Выберите все правильные варианты":
            answers = comb(self.answers)
            if self.incorrect:
                incorrect = list([set(ans) for ans in self.incorrect])
                answers = [ans for ans in answers if set(ans) not in incorrect]
            return choice(list(answers))

    @staticmethod
    def load(question: str, answers: List[str], type: list):
        data = collection.find_one(
            {"question": question, "answers": {"$all": answers}, "type": type}
        )
        if data is None:
            _id = ObjectId()
            collection.insert_one(
                {"question": question, "answers": answers, "type": type, "_id": _id}
            )
            qa = QA(
                **{
                    "question": question,
                    "answers": answers,
                    "_id": str(_id),
                    "type": type,
                }
            )
            assert qa.id is not None
            return qa
        data["_id"] = str(data["_id"])
        qa = QA(**data)
        assert qa.id is not None
        assert qa.question
        return qa

    def set_correct_answer(self, answer: Union[str, Tuple[str]]):
        assert self.question
        self.correct = answer
        res = collection.update_one(
            {"_id": ObjectId(self.id)}, {"$set": {"correct": answer}}
        )
        assert res.matched_count == 1

    def add_incorrect_answer(self, answer: Union[str, Tuple[str]]):
        assert self.question
        self.incorrect.append(answer)
        res = collection.update_one(
            {"_id": ObjectId(self.id)}, {"$addToSet": {"incorrect": answer}}
        )
        assert res.matched_count == 1


def comb(i: Iterable):
    return chain(*[combinations(i, n) for n in range(1, len(i) + 1)])


def import_to_xl():
    alignment = Alignment(horizontal="justify", vertical="justify", wrap_text=True)
    st = NamedStyle(name="st", alignment=alignment,)
    data = collection.find({"correct": {"$exists": True}})
    wb = Workbook()
    ws: worksheet = wb.active
    ws.title = "Cats"
    for col in "ABC":
        dimensions = ws.column_dimensions[col]
        dimensions.width = 50
        dimensions.collapsed = True
    ws.append(["Вопрос", "Ответы", "Правильный"])
    for row, el in enumerate(data, start=1):
        correct = el["correct"]
        if type(correct) != str:
            correct = ", ".join(correct)

        cel1 = ws.cell(row, 1, el["question"])
        cel1.style = st

        cel2 = ws.cell(row, 2, correct)
        cel2.style = st

        cel3 = ws.cell(row, 3, "\n".join(el["answers"]))
        cel3.style = st
    wb.save("out.xlsx")


if __name__ == "__main__":
    import_to_xl()
