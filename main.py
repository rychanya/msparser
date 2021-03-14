import json
from itertools import cycle

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
    user, password = next(user_cycle).values()
    while True:
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
            print(error)
        finally:
            driver.quit()


if __name__ == "__main__":
    typer.run(main)
