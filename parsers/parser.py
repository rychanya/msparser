from time import sleep
from typing import List, Optional

from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .model import QA


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
            WebDriverWait(self.curent, 30).until(
                lambda d: self.curent.value_of_css_property("visibility") == "hidden"
            )

        body: WebElement = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "wtq-body"))
        )
        final: WebElement = body.find_element_by_class_name("wtq-final")
        header: WebElement = WebDriverWait(self.driver, 30).until(
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

        questions = WebDriverWait(self.driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "wtq-question"))
        )
        try:
            question = [q for q in questions if q.is_displayed()][0]
        except IndexError:
            rubric: WebElement = body.find_element_by_class_name("wtq-rubric")
            rubric.find_element_by_class_name("wtq-btn-next").click()
            WebDriverWait(rubric, 30).until_not(lambda d: rubric.is_displayed())
            return
        answers: List[WebElement] = question.find_elements_by_class_name(
            "wtq-item-text-cell-main"
        )
        question_text = question.find_element_by_class_name("wtq-q-question-text").text
        question_type = question.find_element_by_class_name("wtq-q-instruction").text
        assert question_text != ""
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
        elif (
            qa.type
            == "Перетащите варианты так, чтобы они оказались в правильном порядке"
        ):
            ActionChains(self.driver).drag_and_drop(answers[0], answers[1]).perform()
            sleep(3)

        btn: WebElement = WebDriverWait(question, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "wtq-btn-submit"))
        )
        WebDriverWait(btn, 30).until(
            lambda d: "wtq-btn-disabled" not in btn.get_attribute("class")
        )
        btn.click()


class Run:
    def __init__(self, driver: WebDriver, url: str) -> None:
        self.driver = driver
        self.url = url
        self.driver.get(self.url)

    def __enter__(self):
        print(f"start test {self.url}")
        self.parent_window = self.driver.current_window_handle
        main = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "v-main"))
        )
        subtitle = WebDriverWait(main, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "v-list-item__subtitle"))
        )
        button = WebDriverWait(subtitle, 30).until(
            EC.visibility_of_element_located((By.TAG_NAME, "button"))
        )
        WebDriverWait(button, 30).until(
            lambda d: button.text in ("ПРОДОЛЖИТЬ", "НАЗНАЧИТЬ", "НАЧАТЬ")
        )
        button.click()
        if button.text in ("ПРОДОЛЖИТЬ", "НАЧАТЬ"):
            self.driver.switch_to.window(self.driver.window_handles[-1])
            print("switch to test window")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            self.driver.close()
        except NoSuchWindowException:
            pass
        self.driver.switch_to.window(self.parent_window)
        print("switch to parent window")


class Login:
    def __init__(self, user_name, password, driver: WebDriver) -> None:
        self.driver: WebDriver = driver
        self.user_name = user_name
        self.password = password

    def __enter__(self):
        print("start login")
        self.driver.maximize_window()
        self.driver.get("https://mstudy.mvideo.ru/")
        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.element_to_be_clickable((By.TAG_NAME, "form")))
        inputs = wait.until(
            EC.visibility_of_any_elements_located((By.TAG_NAME, "input"))
        )
        inputs[0].send_keys(self.user_name)
        inputs[1].send_keys(self.password)
        current_url = self.driver.current_url
        self.driver.find_elements_by_tag_name("button")[1].click()
        wait.until(EC.url_changes(current_url))
        print("logined")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.driver.quit()
