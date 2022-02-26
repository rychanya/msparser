import json
from itertools import cycle
import pathlib

import typer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from parsers import Login, QAIter, Run


def main(headless: bool = True):
    with open("settings.json", mode="r") as file:
        data = json.load(file)
        urls = data["urls"]
        users = data["users"]
        user_cycle = cycle(users)

    while True:
        try:
            driver_path = pathlib.Path().resolve().joinpath("chromedriver")
            options = Options()
            options.headless = headless
            driver = webdriver.Chrome(executable_path=str(driver_path), options=options)
            user, password = next(user_cycle).values()
            with Login(user, password, driver):
                for url in urls:
                    with Run(driver, url):
                        qa = QAIter(driver)
                        for i in qa:
                            pass
        except Exception as error:
            print("*" * 10)
            print(error)
            print(error.__traceback__)
        finally:
            driver.quit()


if __name__ == "__main__":
    typer.run(main)
