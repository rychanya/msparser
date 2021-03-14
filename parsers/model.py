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


def check_db():
    data = collection.find()
    for el in data:
        incorrect = el.get("incorrect", [])
        if "correct" not in el:
            answers = el["answers"]
            if el["type"] == "Выберите один правильный вариант":
                if len(incorrect) >= len(answers):
                    print(el)
            else:
                if len(incorrect) >= len(comb(answers)):
                    print(el)
            continue
        correct = el["correct"]

        if type(correct) != str:
            correct = set(correct)
            incorrect = list([set(a) for a in incorrect])

        if correct in incorrect:
            print(el)


if __name__ == "__main__":
    check_db()
