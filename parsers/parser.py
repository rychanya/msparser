from typing import List, Optional

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .model import QA

# def stat_parser(driver: WebDriver):
#     header: WebElement = WebDriverWait(driver, 10).until(
#         EC.visibility_of_element_located(
#             (By.XPATH, '//div[@class="wtq-header-main"][@wtq-elem="header-stat-ass"]')
#         )
#     )
#     passed: WebElement = header.find_element_by_class_name(
#         "wtq-stat-passed"
#     ).find_element_by_class_name("wtq-stat-value")
#     failed: WebElement = header.find_element_by_class_name(
#         "wtq-stat-failed"
#     ).find_element_by_class_name("wtq-stat-value")
#     return (passed.text, failed.text)


class QAIter:
    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver
        self.curent: Optional[WebElement] = None
        self.last_passed_count = None
        self.last_answer = None
        self.last_qa: Optional[QA] = None

    def __iter__(self):
        return self

    def _agregate_last_qa(self, passed_count: int):
        if (passed_count - self.last_passed_count) >= 1:
            self.last_qa.set_correct_answer(self.last_answer)
        else:
            self.last_qa.add_incorrect_answer(self.last_answer)

    def __next__(self):

        if self.curent is not None:
            WebDriverWait(self.curent, 10).until(
                lambda d: self.curent.value_of_css_property("visibility") == "hidden"
            )

        body: WebElement = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "wtq-body"))
        )
        final: WebElement = body.find_element_by_class_name("wtq-final")
        header: WebElement = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    '//div[@class="wtq-header-main"][@wtq-elem="header-stat-ass"]',
                )
            )
        )
        passed = int(
            header.find_element_by_class_name("wtq-stat-passed")
            .find_element_by_class_name("wtq-stat-value")
            .text
        )

        if final.is_displayed():
            self._agregate_last_qa(passed)
            raise StopIteration

        questions = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "wtq-question"))
        )
        question = [q for q in questions if q.is_displayed()][0]
        answers: List[WebElement] = question.find_elements_by_class_name(
            "wtq-item-text-cell-main"
        )
        question_text = question.find_element_by_class_name("wtq-q-question-text").text
        question_type = question.find_element_by_class_name("wtq-q-instruction").text

        qa = QA.load(
            question=question_text,
            answers=list([a.text for a in answers]),
            type=question_type,
        )
        assert qa.id is not None

        print(qa.question)
        for ans in qa.answers:
            print(f"\t{ans}")

        if self.last_passed_count is not None:
            self._agregate_last_qa(passed)

        self.curent = question
        self.last_passed_count = passed
        self.last_qa = qa
        self.last_answer = qa.get_answer()

        print(f"check: {self.last_answer}")

        if qa.type == "Выберите один правильный вариант":
            for ans in answers:
                if ans.text == self.last_answer:
                    ans.click()
                    break
        elif qa.type == "Выберите все правильные варианты":
            for ans in answers:
                if ans.text in self.last_answer:
                    ans.click()

        btn: WebElement = WebDriverWait(question, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "wtq-btn-submit"))
        )
        WebDriverWait(btn, 10).until(
            lambda d: "wtq-btn-disabled" not in btn.get_attribute("class")
        )
        btn.click()
