from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Run:
    def __init__(self, driver: WebDriver, url: str) -> None:
        self.driver = driver
        self.url = url
        self.driver.get(self.url)

    def __enter__(self):
        print(f"start test {self.url}")
        self.parent_window = self.driver.current_window_handle
        main = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "v-main"))
        )
        subtitle = WebDriverWait(main, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "v-list-item__subtitle"))
        )
        button = WebDriverWait(subtitle, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "button"))
        )
        WebDriverWait(button, 10).until(lambda d: button.text == "ПРОДОЛЖИТЬ")
        button.click()
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
