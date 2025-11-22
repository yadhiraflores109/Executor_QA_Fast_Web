from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import os

class BrowserManager:
    """Maneja la creación y cierre de navegadores Selenium."""

    def __init__(self, browser_type="chrome", headless=False):
        self.browser_type = browser_type
        self.headless = headless
        self.driver = None

    def start_browser(self):
        """Inicia el navegador según el tipo seleccionado."""
        if self.browser_type == "chrome":
            options = ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver_path = os.path.join("app", "drivers", "chromedriver.exe")
            service = ChromeService(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)

        elif self.browser_type == "firefox":
            options = FirefoxOptions()
            if self.headless:
                options.add_argument("--headless")
            driver_path = os.path.join("app", "drivers", "geckodriver.exe")
            service = FirefoxService(driver_path)
            self.driver = webdriver.Firefox(service=service, options=options)

        else:
            raise ValueError("Navegador no soportado. Use 'chrome' o 'firefox'.")

        self.driver.maximize_window()
        return self.driver

    def close_browser(self):
        """Cierra el navegador si está activo."""
        if self.driver:
            self.driver.quit()
