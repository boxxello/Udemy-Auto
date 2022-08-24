from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager, IEDriverManager
from webdriver_manager.opera import OperaDriverManager

from watcher_udemy.logging import get_logger

logger = get_logger()

VALID_FIREFOX_STRINGS = {"ff", "firefox"}
VALID_CHROME_STRINGS = {"chrome", "google-chrome"}
VALID_CHROMIUM_STRINGS = {"chromium"}
VALID_INTERNET_EXPLORER_STRINGS = {"internet_explorer", "ie"}
VALID_OPERA_STRINGS = {"opera"}
VALID_EDGE_STRINGS = {"edge"}

ALL_VALID_BROWSER_STRINGS = VALID_CHROME_STRINGS.union(VALID_CHROMIUM_STRINGS)


class DriverManager:
    def __init__(self, browser: str):
        self.driver = None
        self.options = None
        self.browser = browser
        self._init_driver()

    def _init_driver(self):
        """
        Initialize the correct web driver based on the users requested browser

        :return: None
        """

        if self.browser.lower() in VALID_CHROME_STRINGS:
            #enabling performance and request profiling
            caps = DesiredCapabilities.CHROME
            # as per latest docs
            caps['goog:loggingPrefs'] = {'performance': 'ALL'}
            #disabling the annoying chrome notification
            self.options = webdriver.ChromeOptions()
            self.options.add_argument("--mute-audio")
            self.options.add_experimental_option("useAutomationExtension", False)
            self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
            self.driver = webdriver.Chrome( ChromeDriverManager().install(), options=self.options, desired_capabilities=caps)



        elif self.browser.lower() in VALID_CHROMIUM_STRINGS:
            self.driver = webdriver.Chrome(
                ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
            )
        elif self.browser.lower() in VALID_EDGE_STRINGS:
            self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())
        elif self.browser.lower() in VALID_FIREFOX_STRINGS:
            self.driver = webdriver.Firefox(
                executable_path=GeckoDriverManager().install()
            )
        elif self.browser.lower() in VALID_OPERA_STRINGS:
            self.driver = webdriver.Opera(
                executable_path=OperaDriverManager().install()
            )
        elif self.browser.lower() in VALID_INTERNET_EXPLORER_STRINGS:
            self.driver = webdriver.Ie(IEDriverManager().install())
        else:
            raise ValueError("No matching browser found")

        # Get around captcha
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "const newProto = navigator.__proto__;"
                "delete newProto.webdriver;"
                "navigator.__proto__ = newProto;"
            },
        )
        # Maximize the browser
        self.driver.maximize_window()



