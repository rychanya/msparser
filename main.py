import typer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from parsers import QAIter
from parsers.utils import Login, Run

urls = [
    "https://mstudy.mvideo.ru/_ems/assessment/6933527863096261495",
    "https://mstudy.mvideo.ru/_ems/assessment/6933533644755699520",
    "https://mstudy.mvideo.ru/_ems/assessment/6933536973668776172",
    "https://mstudy.mvideo.ru/_ems/assessment/6933542010422430449",
    "https://mstudy.mvideo.ru/_ems/assessment/6933549990634539188",
]


def main(user: str, password: str, n: int = 10, headless: bool = True):
    for _ in range(1, n + 1):
        print(f"start {n} wave")
        try:
            options = Options()
            options.headless = headless
            driver = webdriver.Chrome(
                executable_path="/home/rychanya/msparser/chromedriver", options=options
            )
            with Login(user, password, driver):
                for url in urls:
                    with Run(driver, url):
                        qa = QAIter(driver)
                        for i in qa:
                            pass
        except Exception as error:
            driver.quit
            print(error)


if __name__ == "__main__":
    typer.run(main)
