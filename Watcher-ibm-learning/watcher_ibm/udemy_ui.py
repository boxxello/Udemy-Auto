import json
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Dict, Optional

import requests
from price_parser import Price
from regex import regex
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from watcher_ibm.exceptions import LoginException, RobotException, CourseNotFoundException
from watcher_ibm.logging import get_logger
from watcher_ibm.settings import Settings
from watcher_ibm.utils import get_app_dir, validateJSON

logger = get_logger()


@dataclass(unsafe_hash=True)
class RunStatistics:
    prices: List[Decimal] = field(default_factory=list)

    expired: int = 0
    enrolled: int = 0
    already_enrolled: int = 0
    unwanted_language: int = 0
    unwanted_category: int = 0

    start_time = None

    currency_symbol = None

    def savings(self):
        return sum(self.prices) or 0

    def table(self):
        # Only show the table if we have something to show
        if self.prices:
            if self.currency_symbol is None:
                self.currency_symbol = "¤"
            run_time_seconds = int(
                (datetime.utcnow() - self.start_time).total_seconds()
            )

            logger.info("==================Run Statistics==================")
            logger.info(f"Enrolled:                   {self.enrolled}")
            logger.info(f"Unwanted Category:          {self.unwanted_category}")
            logger.info(f"Unwanted Language:          {self.unwanted_language}")
            logger.info(f"Already Claimed:            {self.already_enrolled}")
            logger.info(f"Expired:                    {self.expired}")
            logger.info(
                f"Savings:                    {self.currency_symbol}{self.savings():.2f}"
            )
            logger.info(f"Total run time (seconds):   {run_time_seconds}s")
            logger.info("==================Run Statistics==================")


class UdemyStatus(Enum):
    """
    Possible statuses of udemy course
    """

    ALREADY_ENROLLED = "ALREADY_ENROLLED"
    ENROLLED = "ENROLLED"
    NOTUNROLLED = "NOTUNROLLED"
    EXPIRED = "EXPIRED"
    UNWANTED_LANGUAGE = "UNWANTED_LANGUAGE"
    UNWANTED_CATEGORY = "UNWANTED_CATEGORY"


class UdemyActionsUI:
    """
    Contains any logic related to interacting with udemy website
    """

    DOMAIN = "https://ibm-learning.udemy.com/"
    REQUEST_URL_NUM_LECTURES = "https://ibm-learning.udemy.com/api-2.0/courses/{}/?fields[course]=title,num_lectures,completion_ratio"
    REQUEST_URL_NUM_QUIZZES = "https://ibm-learning.udemy.com/api-2.0/courses/{}/?fields[course]=num_quizzes"
    REQUEST_URL_URL = "https://ibm-learning.udemy.com/api-2.0/courses/{}/?fields[course]=url"
    REQUEST_LECTURES = "https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/{}/lectures"
    REQUEST_LECTURES_NEXT = "https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/673024/lectures/?page=4"
    URL_TO_COURSE_ID = "https://ibm-learning.udemy.com/course/{}/"
    HEADERS = {
        "origin": "https://ibm-learning.udemy.com/",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "Content-Type": "application/json;charset=utf-8",
        "x-requested-with": "XMLHttpRequest",
        "x-checkout-version": "2",
        "referer": "https://ibm-learning.udemy.com/",
    }
    COURSE_DETAILS = (
        "https://ibm-learning.udemy.com/api-2.0/courses/{}/?fields[course]=title,url,context_info,primary_category,primary_subcategory,avg_rating_recent,visible_instructors,locale,estimated_content_length,num_subscribers,num_quizzes,num_lectures,completion_ratio"
    )
    ENROLLED_COURSES_URL = ("https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/?page_size=1400")

    QUIZ_URL = "https://ibm-learning.udemy.com/api-2.0/courses/{}/subscriber-curriculum-items/?page_size=1400&fields[lecture]=title,object_index,is_published,sort_order,created,asset,supplementary_assets,is_free&fields[quiz]=title,object_index,is_published,sort_order,type&fields[practice]=title,object_index,is_published,sort_order&fields[chapter]=title,object_index,is_published,sort_order&fields[asset]=title,filename,asset_type,status,time_estimation,is_external&caching_intent=Truefields[course]=title,url,context_info,primary_category,primary_subcategory,avg_rating_recent,visible_instructors,locale,estimated_content_length,num_subscribers,num_quizzes,num_lectures,completion_ratio"
    RESPONSES_URL = "https://ibm-learning.udemy.com/api-2.0/quizzes/{}/assessments/?version=1&page_size=1400&fields[assessment]=id,assessment_type,prompt,correct_response,section,question_plain,related_lectures"
    COMPLETED_QUIZ_IDS = "https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/359550/progress/?page_size=1400&fields[course]=completed_lecture_ids,completed_quiz_ids,last_seen_page,completed_assignment_ids,first_completion_time"
    BOH = "https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/359550/quizzes/95416/?draft=false&fields[quiz]=id,type,title,description,object_index,num_assessments,version,duration,is_draft,pass_percent,changelog"
    URL_SEND_RESPONSE = (
        "https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/user-attempted-quizzes/{quiz_id}/assessment-answers/")
    #	/api-2.0/users/me/subscribed-courses/359550/quizzes/95420/user-attempted-quizzes/latest/
    # https://ibm-learning.udemy.com/course/mastering-object-oriented-design-in-java/learn/quiz/95416#overview
    LAST_ID_QUIZ = "https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/quizzes/{quiz_id}/user-attempted-quizzes/latest"
    URL_COURSE_NO_API = "https://ibm-learning.udemy.com/course/{course_id}/"
    URL_QUIZ_NOAPI="https://ibm-learning.udemy.com/course/{url_no_id}/learn/quiz/{assessment_id}#overview"
    URL_GET_ALREADY_DONE_ASSESSMENTS="https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/user-attempted-quizzes/"
    def __init__(self, driver: WebDriver, settings: Settings, cookie_file_name: str = ".cookie"):

        self.driver = driver
        self.settings = settings
        self.logged_in = False
        self.stats = RunStatistics()
        self.session = requests.Session()
        self.stats.start_time = datetime.utcnow()
        self._cookie_file = os.path.join(get_app_dir(), cookie_file_name)
        self.already_rolled_courses = []

    def login(self, is_retry=False) -> None:
        """
        Login to your udemy account

        :param bool is_retry: Is this is a login retry and we still have captcha raise RobotException

        :return: None
        """
        if not self.logged_in:
            cookie_details = self._load_cookies()

            if cookie_details is None:
                self.driver.get(f"{self.DOMAIN}")

                # Prompt for email/password if we don't have them saved in settings
                if self.settings.email is None:
                    self.settings.prompt_email()
                if self.settings.password is None:
                    self.settings.prompt_password()

                try:
                    xpath_email = '//*[@id="credsDiv"]'
                    try:
                        button = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, xpath_email))
                        )
                    except TimeoutException:

                        raise LoginException("Udemy user failed to identify w3id button")
                    button.click()
                    try:
                        input_email = "user-name-input"
                        button = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, input_email))
                        )
                        button.click()
                        email_element = self.driver.find_element_by_id(input_email)
                        email_element.send_keys(self.settings.email)
                        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, "checkbox1_lbl"))
                                                             )
                        password_element = self.driver.find_element_by_name("password")
                        password_element.send_keys(self.settings.password)
                        remind_button = self.driver.find_element_by_name("checkbox1_lbl")
                        remind_button.click()

                        login_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "login-button"))
                        )

                        login_button.click()
                        # if
                        # else
                        try:
                            one_timepasscodeinput = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.ID, "otp-input"))
                            )
                            if one_timepasscodeinput:
                                input(
                                    "Solve otp insertion. Hit enter once solved "
                                )
                                try:
                                    submit_btn = self.driver.find_element_by_id("submit_btn")
                                    submit_btn.click()
                                except NoSuchElementException:
                                    pass
                        except TimeoutException:
                            logger.info("No otp found")
                            pass
                        cookie_details = self.driver.get_cookies()
                        refactored_cookies = []
                        for cookie in cookie_details:
                            if cookie.get('name') == 'csrftoken' \
                                    or cookie.get('name') == 'client_id' \
                                    or cookie.get('name') == 'access_token':
                                refactored_cookies.append(cookie)
                        print(refactored_cookies)
                        self._cache_cookies(refactored_cookies)

                        # check if file is empty
                        if os.stat(self._cookie_file).st_size == 0:
                            raise LoginException("Udemy user failed to login")

                    except TimeoutException:
                        raise LoginException("Udemy user failed to login")

                except NoSuchElementException as e:
                    is_robot = self._check_if_robot()
                    if is_robot and not is_retry:
                        input(
                            "Before login. Please solve the captcha before proceeding. Hit enter once solved "
                        )
                        self.login(is_retry=True)
                        return
                    if is_robot and is_retry:
                        raise RobotException("I am a bot!")
                    raise e
                else:
                    user_dropdown_xpath = "//a[@data-purpose='user-dropdown']"
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, user_dropdown_xpath))
                        )
                    except TimeoutException:
                        is_robot = self._check_if_robot()
                        if is_robot and not is_retry:
                            input(
                                "After login. Please solve the captcha before proceeding. Hit enter once solved "
                            )
                            if self._check_if_robot():
                                raise RobotException("I am a bot!")
                            self.logged_in = True
                            return
                        raise LoginException("Udemy user failed to login")


            else:
                dummy_url = '/404error'
                self.driver.get(f"{self.DOMAIN + dummy_url}")
                for cookie in cookie_details:
                    self.driver.add_cookie(cookie)
                self.driver.get(f"{self.DOMAIN}")

            try:
                ibm_learning_subm = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.ID, "ibm-learning"))
                )
                logger.info("Logged in to udemy, trying to retrieve button")
                self.logged_in = True
                my_learning = self.driver.find_elements_by_tag_name('span')
                for x in my_learning:
                    if x.text.upper() == 'My Learning'.upper():
                        x.click()
                        break

                self.logged_in = True
            except TimeoutException:
                raise LoginException("Udemy user failed to login")

            # for cookie in self._load_cookies():
            #     self.session.cookies.set(cookie['name'], cookie['value'])
            for cookie in self.driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])
            bearer_token = None

            for x in self._load_cookies():
                bearer_token = x if x.get('name') == 'access_token' else bearer_token
            logger.info(f"printing bearer token {bearer_token}")

            self.session.headers = self.HEADERS
            if bearer_token is not None:
                bearer_string = f"Bearer {bearer_token['value']}"
                self.session.headers.update(
                    {
                        "authorization": bearer_string,
                        "x-udemy-authorization": bearer_string,
                        "x-csrftoken": bearer_token['value'],
                    }
                )

    def _get_course_quizzes_number(self, course_id):
        """
        Get the number of quizzes for a course
        :param course_id:
        :return:
        """

        response = self.session.get(self.REQUEST_URL_NUM_QUIZZES.format(course_id))
        response_json = response.json()
        if response.status_code == 200:
            return response_json['num_quizzes']
        else:
            return -1

    def enroll(self, url: str) -> tuple:
        """
        Redeems the course url passed in

        :param str url: URL of the course to redeem
        :return: A string detailing course status
        """
        logger.info("Enrolling in course url {}".format(url))
        self.driver.get(url)
        logger.info("Setting up course")
        course_name = self.driver.title
        logger.info("Starting language check")
        if not self._check_languages(course_name):
            return UdemyStatus.UNWANTED_LANGUAGE.value, None, None

        logger.info("Check languages done")
        logger.info("Starting categories check")
        if not self._check_categories(course_name):
            return UdemyStatus.UNWANTED_CATEGORY.value, None, None
        logger.info("Check Categories done")

        try:
            # check if element is present before clicking
            buy_course_button_xpath = "//button[@data-purpose='buy-this-course-button']"
            # We need to wait for this element to be clickable before checking if already purchased
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, buy_course_button_xpath))
            )

        except TimeoutException:
            logger.info("Course is already purchased")
        else:
            # Check if already enrolled. If add to cart is available we have not yet enrolled
            logger.info("Checking if already enrolled")

            element_present = EC.presence_of_element_located(
                (By.XPATH, buy_course_button_xpath)
            )
            WebDriverWait(self.driver, 10).until(element_present).click()

            logger.info(f"Successfully enrolled in: '{course_name}'")
            self.stats.enrolled += 1
        cs_link, course_id = self._get_course_link_wrapper(url)
        logger.info(f"Course id: {course_id} and link: {cs_link}")
        return UdemyStatus.ALREADY_ENROLLED.value, cs_link, course_id

    def _find_all_lectures(self, first_link_to) -> List[str]:
        logger.info(f"Finding all lectures in: '{first_link_to}'")
        resp_json_json = self._resp_from_url_with_session(first_link_to)

        next_links_lst = []
        next_links_lst.append(first_link_to)

        extracted_link = resp_json_json.get("next")

        flag = True

        while flag:
            # get next from json
            if extracted_link is not None:
                if not extracted_link in next_links_lst:

                    next_links_lst.append(extracted_link)
                    response_got = self._resp_from_url_with_session(extracted_link)
                    extracted_link = response_got.get('next')
                else:
                    flag = False
            else:
                flag = False
        return next_links_lst

    def _get_course_id(self, url: str):
        self.driver.get(url)
        dummy_elm_xpath = (
            "//div[starts-with(@class, 'ud-app-loader')][@data-module-args]"
        )
        try:
            dummy_element = (
                WebDriverWait(self.driver, 10)
                .until(EC.presence_of_element_located((By.XPATH, dummy_elm_xpath))))
        except TimeoutException:
            return None
        else:
            dummy_element = self.driver.find_elements_by_xpath(dummy_elm_xpath)
            for x in dummy_element:
                if x.get_attribute("data-module-args") is not None:
                    attr = x.get_attribute("data-module-args")
                    json_attr = json.loads(attr)
                    return json_attr.get("courseId")

    @staticmethod
    def extract_cs_id(url: str) -> int:
        pattern = r"^https:\/\/(www\.)?ibm-learning\.udemy\.com\/course-dashboard-redirect\/\?course_id=(?P<extract_num>\d+)$"
        matches = regex.search(pattern, url, regex.M)
        if not matches:
            new_pattern = r"https:\/\/(www\.)?ibm-learning\.udemy\.com\/course\/(?P<extract_num>\d+)\/?$"
            matches = regex.search(new_pattern, url, regex.M)
        if matches:
            numb = int(matches.group('extract_num'))
            return numb

    def _get_all_lectures_id(self, course_link) -> List[int]:

        list_of_links = self._find_all_lectures(course_link)
        next_lectures_lst = []
        for link in list_of_links:
            resp_json_json = self._resp_from_url_with_session(link)
            for lecture in resp_json_json['results']:
                next_lectures_lst.append(lecture['id'])
        return next_lectures_lst

    def _resp_from_url_with_session(self, url: str):
        return self.session.get(url).json()

    def _get_course_links_lectures(self, number_course_id: int) -> json:
        """
        Returns a list of all the lecture ids in the course
        :return: List of lecture ids
        """

        return self.session.get(self.REQUEST_LECTURES.format(number_course_id)).json()

    def get_all_links_from_page(self, url: str = None) -> List[str]:
        """
        Gets all the links from a page
        :param str url: URL of the page to get links from
        :return: A list of links
        """
        if url is not None:
            self.driver.get(url)

        links = self.driver.find_elements_by_tag_name('a')
        links = [link.get_attribute('href') for link in links]
        return links

    def _load_cookies(self) -> Dict:
        """
        Loads existing cookie file

        :return:
        """
        cookies = None

        if os.path.isfile(self._cookie_file):
            logger.info("Loading cookie from file")
            with open(self._cookie_file) as f:
                cookies = json.loads(f.read())
        else:
            logger.info("No cookie available")
        return cookies

    def _cache_cookies(self, cookies: List) -> None:
        """
        Caches cookies for future logins

        :param cookies:
        :return:
        """
        logger.info("Caching cookie for future use")
        with open(self._cookie_file, "w") as f:
            json.dump(cookies, f)

    def _delete_cookies(self) -> None:
        """
        Remove existing cookie file

        :return:
        """
        logger.info("Deleting cookie")
        os.remove(self._cookie_file)

    def _check_languages(self, course_identifier):
        is_valid_language = True
        if self.settings.languages:
            locale_xpath = "//div[@data-purpose='lead-course-locale']"
            try:
                element_text = (
                    WebDriverWait(self.driver, 10)
                    .until(EC.presence_of_element_located((By.XPATH, locale_xpath)))
                    .text
                )
            except TimeoutException:
                logger.error("Couldn't find the language element")
                return True
            else:
                logger.info(f"Found language element: {element_text}")
                if element_text not in self.settings.languages:
                    logger.info(f"Course language not wanted: {element_text}")
                    logger.info(
                        f"Course '{course_identifier}' language not wanted: {element_text}"
                    )
                    self.stats.unwanted_language += 1
                    is_valid_language = False
        return is_valid_language

    def _check_categories(self, course_identifier):
        is_valid_category = True
        if self.settings.categories:
            # If the wanted categories are specified, get all the categories of the course by
            # scraping the breadcrumbs on the top

            breadcrumbs_path = "udlite-breadcrumb"
            breadcrumbs_text_path = "udlite-heading-sm"
            breadcrumbs: WebElement = self.driver.find_element_by_class_name(
                breadcrumbs_path
            )
            breadcrumbs = breadcrumbs.find_elements_by_class_name(breadcrumbs_text_path)
            breadcrumb_text = [bc.text for bc in breadcrumbs]  # Get only the text

            for category in self.settings.categories:
                if category in breadcrumb_text:
                    is_valid_category = True
                    break
            else:
                logger.info(
                    f"Skipping course '{course_identifier}' as it does not have a wanted category"
                )
                self.stats.unwanted_category += 1
                is_valid_category = False
        return is_valid_category

    def _check_price(self, course_name):
        course_is_free = True
        price_xpath = "//div[contains(@data-purpose, 'total-amount-summary')]//span[2]"
        price_element = self.driver.find_element_by_xpath(price_xpath)

        # We are only interested in the element which is displaying the price details
        if price_element.is_displayed():
            _price = price_element.text
            # This logic should work for different locales and currencies
            checkout_price = Price.fromstring(_price)

            # Set the currency for stats
            if (
                    self.stats.currency_symbol is None
                    and checkout_price.currency is not None
            ):
                self.stats.currency_symbol = checkout_price.currency

            if checkout_price.amount is None or checkout_price.amount > 0:
                logger.info(
                    f"Skipping course '{course_name}' as it now costs {_price}"
                )
                self.stats.expired += 1
                course_is_free = False

        # Get the listed price of the course for stats
        if course_is_free:
            list_price_xpath = (
                "//div[starts-with(@class, 'order-summary--original-price-text')]//span"
            )
            list_price_element = self.driver.find_element_by_xpath(list_price_xpath)
            list_price = Price.fromstring(list_price_element.text)
            if list_price.amount is not None:
                self.stats.prices.append(list_price.amount)
        return course_is_free

    def _check_if_robot(self) -> bool:
        """
        Simply checks if the captcha element is present on login if email/password elements are not

        :return: Bool
        """
        is_robot = True
        try:
            self.driver.find_element_by_id("px-captcha")
        except NoSuchElementException:
            is_robot = False
        return is_robot
    def _get_course_link_wrapper(self, course_link):
        if (return_st:=self._get_course_link_from_redirect(course_link))[1]:

            return return_st[0], return_st[1]
        elif (return_st:=self._get_course_id(course_link)):
            return self.REQUEST_LECTURES.format(return_st), return_st

        raise CourseNotFoundException(course_link)


    def _get_course_link_from_redirect(self, course_link) -> tuple:
        number_extr = self.extract_cs_id(course_link)
        return self.REQUEST_LECTURES.format(number_extr), number_extr

    def _get_completition_course_link(self, course_link):
        number_extr = self.extract_cs_id(course_link)
        return self.REQUEST_URL_NUM_LECTURES.format(number_extr)

    def _get_completetion_ratio(self, course_link):
        response_details = self.session.get(course_link).json()
        return response_details['completion_ratio']

    @staticmethod
    def _build_json_complete_course(course_id: int):
        return {"lecture_id": course_id, "downloaded": False}

    def _get_course_details(self, course_id: int):
        """
        Retrieves details relating to the course passed in

        :param int course_id: Id of the course to get the details of
        :return: dictionary containing the course details
        """
        return self.session.get(self.COURSE_DETAILS.format(course_id)).json()

    def _get_already_rolled_courses(self) -> List[int]:
        """
        Retrieves the already enrolled courses
        """
        logger.info("Getting already enrolled courses")
        list_of_links = self._find_all_lectures(self.ENROLLED_COURSES_URL)
        logger.info("Found {} enrolled courses pages".format(len(list_of_links)))
        for x in list_of_links:
            response = self.session.get(x)
            resp_json = response.json()

            if response.status_code == 200:
                if re_res := resp_json['results']:
                    for x in re_res:
                        if x['id'] not in self.already_rolled_courses:
                            self.already_rolled_courses.append(x['id'])

        return self.already_rolled_courses

    def _get_assessment_ids(self, course_id: int):
        """
        Retrieves the assessment ids for the course passed in
        :param int course_id: Id of the course to get the assessment ids of
        :return: list of assessment ids
        """
        logger.info(f"CALLING FUNCTION GET_ASSESSMENT_IDS with url {self.QUIZ_URL.format(course_id)}")
        assessment_json = self.session.get(self.QUIZ_URL.format(course_id)).json()

        results = assessment_json['results']
        assessment_lst_id = []
        for x in results:
            if x['_class'] != 'lecture':

                if x['_class'] == 'quiz':
                    assessment_lst_id.append(x['id'])
        # logger.info("Printing all quizs_ids")
        # for x in assessment_lst_id:
        #     logger.info(f"Found quiz id {x}")
        return assessment_lst_id

    def _get_assessments(self, course_id: int):
        assessment_lst_ids = self._get_assessment_ids(course_id)
        if assessment_lst_ids:
            assessment_lst = []
            for x in assessment_lst_ids:
                logger.info(f"CALLING FUNCTION _get_assessments with url {self.RESPONSES_URL.format(x)}")
                assessment_json = self.session.get(self.RESPONSES_URL.format(x)).json()
                results = assessment_json.get('results')

                for y in results:
                    y.update({'assessment_initial_id': x})
                    if y.get('_class') != 'lecture':

                        if y.get('_class') == 'assessment':
                            assessment_lst.append(y)
            for y in assessment_lst:
                logger.info(f"Found assessment id {y['id']}, quiz id {y['assessment_initial_id']}")
            return assessment_lst

    def _send_completition_req(self, course_link: str, list_of_lectures_ids: List, course_id: int) -> json:
        url_pattern = r"https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/{}/completed-lectures/"
        new_url_xpath = r"api-2.0/users/me/subscribed-courses/{}/completed-lectures/"
        course_details = self._get_course_details(course_id)
        course_url = course_details['url']
        logger.info(f"\n\nLogging course details {course_details}\n\n{course_url}")
        new_session = requests.Session()
        new_session.headers.update(self.session.headers)
        new_session.cookies.update(self.session.cookies)
        new_session.headers.update({"xpath": new_url_xpath.format(course_id)})
        new_session.headers.update({"Accept": "application/json"})
        new_session.headers.update({"authority": "ibm-learning.udemy.com"})
        # https://ibm-learning.udemy.com/api-2.0/users/me/subscribed-courses/1602900/user-attempted-quizzes/778172944/coding-exercise-answers/
        processes = []

        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            for lect in list_of_lectures_ids:
                logger.info(f"Sending request to mark lecture {lect} as completed of course {course_id}")
                processes.append(executor.submit(self._send_completition_req_helper, new_session, lect, course_id, url_pattern))
        for task in as_completed(processes):
            logger.info(task.result())
        logger.info(f'Time taken to complete {len(list_of_lectures_ids)} lectures: {time.time() - start}')

    def _send_completition_req_helper(self, new_session, lect, course_id, url_pattern):
        # logger.info(self._build_json_complete_course(lect))
        response = new_session.post(url_pattern.format(course_id), json=self._build_json_complete_course(lect))
        return response.status_code, response.text


    @staticmethod
    def _build_json_complete_part_quiz(x: json):
        # mapping number to character
        # corresponding_char = chr(ord('a') + idx)
        correct_response = x.get('correct_response')
        rand_duration = random.randint(1, 150)

        json_to_ret = {"assessment_id": x.get('id'), "response": correct_response,
                       "duration": rand_duration}
        logger.info(json_to_ret)
        return json_to_ret

    def _solve_first_quiz_with_driver(self, course_id: int, x: json):
        self.driver.get(self.URL_COURSE_NO_API.format(course_id=course_id))
        dummy_elm_xpath = (
            "//div[starts-with(@class, 'ud-app-loader')][@data-module-args]"
        )
        try:
            dummy_element = (
                WebDriverWait(self.driver, 10)
                .until(EC.presence_of_element_located((By.XPATH, dummy_elm_xpath))))
        except TimeoutException:
            logger.warning("Couldn't find dummy element to solve quiz")
            return None
        else:
            current_url = self.driver.current_url
            if url_to_use:= self.validate_basic_quiz_url(current_url):
                url_of_quiz=self.URL_QUIZ_NOAPI.format(url_no_id=url_to_use,assessment_id=x['assessment_initial_id'])
                self.driver.get(url_of_quiz)
                logger.info(f"Found quiz url {url_of_quiz}")
                try:
                    resume_play_quiz_btn = "//button[@data-purpose='start-or-resume-quiz']"
                    not_found_resume="//div[contains(@class, 'results-page--results-page')]"
                    try:

                        WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, resume_play_quiz_btn))
                        ).click()

                    except TimeoutException:
                        logger.warning("couldn't find resume button, already completed quiz")
                        WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, not_found_resume))
                        ).click()
                        return True
                    try:
                        locale_xpath_ul_resp = "//ul[@aria-labelledby='question-prompt']"
                        menu_items = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, locale_xpath_ul_resp))
                        )
                        items = self.driver.find_element_by_xpath(locale_xpath_ul_resp)
                    except TimeoutException:
                        logger.error("TimeoutException, couldn't find quiz menu/answers")
                        return None

                    ul_elements=items.find_elements_by_tag_name('li')
                    # logger.debug(ul_elements)
                    correct_response = x.get('correct_response')
                    print(correct_response)
                    lst_of_correct_responses = []
                    for y in correct_response:
                        ord_of_char = ord(y)
                        reset_to_0=ord_of_char-97
                        lst_of_correct_responses.append(reset_to_0)
                    # regex_extract=r'[a-zA-Z]+'
                    # correct_response_lst = re.findall(regex_extract, correct_response)
                    # print(correct_response_lst)
                    for idx,x in enumerate(ul_elements):
                        if idx in lst_of_correct_responses:
                            x.click()
                    #data-purpose="next-question-button"
                    #get last entry of console logs
                    last_entry = self.driver.get_log('performance')[-1]
                    last_timestamp=last_entry['timestamp']
                    print(last_timestamp)
                    try:
                        next_question_btn = "//button[@data-purpose='next-question-button']"
                        WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, next_question_btn))
                        ).click()
                    except TimeoutException:
                        logger.error(f"TimeoutException - couldn't find next button")
                        return None


                    filtered_logs = [x for x in self.driver.get_log('performance') if x['timestamp'] > last_timestamp]
                    lst_of_logs=[]
                    for x in filtered_logs:
                        for k,v in x.items():
                            if (json_dict:=validateJSON(v))[0]:
                                for x,y in json_dict[1].items():
                                    if type(y) is dict:
                                        if y['method']=='Network.requestWillBeSent':
                                                if y['params']['request']['method']=='POST':
                                                    lst_of_logs.append(y['params']['request']['url'])
                    #check with validate_assessment_url function if the url in list lst_of_logs
                    non_duplicate_lst = list(set(lst_of_logs))
                    lst_of_assessments_ids=[x for x in non_duplicate_lst if self.validate_assessment_url(x)]

                    if len(lst_of_assessments_ids)>1:
                        logger.error("Something went wrong, it was supposed to be a lst of ids of length=1")
                        return None
                    else:
                        return lst_of_assessments_ids[0]

                except TimeoutException as e:
                    logger.error("Could not find some of the buttons to quiz")
                    logger.warning(e)

                    return None
    # oneliner up
    # def _get_log(self, _last_timestamp):
    #     last_timestamp = _last_timestamp
    #     entries = self.driver.get_log("performance")
    #     filtered = []
    #
    #     for entry in entries:
    #         # check the logged timestamp against the
    #         # stored timestamp
    #         if entry["timestamp"] > _last_timestamp:
    #             filtered.append(entry)
    #
    #             # save the last timestamp only if newer
    #             # in this set of logs
    #             if entry["timestamp"] > last_timestamp:
    #                 last_timestamp = entry["timestamp"]
    #
    #     return filtered
    @staticmethod
    def validate_assessment_url(url) -> Optional[str]:
        """
        Validates the url passed in, if it is a valid url for the udemy course then returns the url
        :param str url: url to validate
        :return: url if valid else None
        """
        if url is None:
            return None
        url_pattern_basic_url = "^https:\/\/(www\.)?ibm-learning\.udemy\.com\/api-2\.0\/users\/me\/subscribed-courses\/\d+\/user-attempted-quizzes\/(?P<assessment_id_n>\d+)\/assessment-answers\/?$"
        # https://regex101.com/r/ngK7fj/1
        matches = regex.search(url_pattern_basic_url, url, flags=(regex.M))
        if matches:
            assessment_id_n = matches.group('assessment_id_n')
            logger.info(f"RETURNING THIS {assessment_id_n}")
            return assessment_id_n
        return None

    @staticmethod
    def validate_basic_quiz_url(url) -> Optional[str]:
        """
        Validates the url passed in, if it is a valid url for the udemy course then returns the url
        :param str url: url to validate
        :return: url if valid else None
        """
        if url is None:
            return None
        url_pattern_basic_url = "^https:\/\/(www\.)?ibm-learning\.udemy\.com\/course\/(?P<important_part>.+[^\/])\/learn\/(?:(quiz)|(lecture)|(practice))\/\d+.*$"
        # https://regex101.com/r/gJkFFJ/1
        matches = regex.search(url_pattern_basic_url, url, flags=(regex.M))
        if matches:
            cs_url_no_id = matches.group('important_part')
            return cs_url_no_id
        return None


    @staticmethod
    async def validate_quiz_url(url) -> Optional[str]:
        if url is None:
            return None
        url_pattern_quiz = r"^https:\/\/(www\.)?ibm-learning\.udemy\.com\/course\/.+[^\/]\/learn\/quiz\/\d+#overview$"
        # https://regex101.com/r/XGiyCw/1
        matching = re.match(url_pattern_quiz, url, flags=(re.IGNORECASE | re.M))
        if matching is not None:
            matching = matching.group()
            return matching
        else:
            return None


    def _solve_quiz(self, course_id: int):
        new_session = requests.Session()
        new_session.headers.update(self.session.headers)
        new_session.cookies.update(self.session.cookies)
        new_session.headers.update({"Accept": "application/json"})
        new_session.headers.update({"authority": "ibm-learning.udemy.com"})
        assessment_lst = self._get_assessments(course_id)


        for idx, x in enumerate(assessment_lst):
            assessment_lst_already_done = self._get_already_done_assessments(course_id, x.get('assessment_initial_id'))
            if assessment_lst_already_done is None:
                print(f"Quiz idx: {idx}\n{x} \n\n")
                if not x.get('assessment_initial_id') in self._get_completed_assessments(course_id):
                    logger.info(f"Found the first assessment real id for {x.get('assessment_initial_id')}")
                    self._solve_first_quiz_with_driver(course_id, x)
            else:
                logger.info(f"Else, sending xhr req")

                req_json = self._build_json_complete_part_quiz(x)
                logger.info(
                    f"Sending to {self.URL_SEND_RESPONSE.format(course_id=course_id, quiz_id=assessment_lst_already_done)} what is {req_json}")
                response = new_session.post(
                    self.URL_SEND_RESPONSE.format(course_id=course_id, quiz_id=assessment_lst_already_done),
                    json=req_json)
                logger.info(f"Response is {response.status_code}, text is {response.text}")
    def _get_completed_assessments(self, course_id: int)->List:

        response = self.session.get(self.COMPLETED_QUIZ_IDS.format(course_id=course_id))
        if response.status_code == 200 or response.status_code == 201:
            json_resp = response.json()
            return json_resp.get('completed_assignment_ids')
    def _get_already_done_assessments(self, course_id, assessment_id_fake)->list[str]:
        print(self.LAST_ID_QUIZ.format(course_id=course_id, quiz_id=assessment_id_fake))
        response = self.session.get(self.LAST_ID_QUIZ.format(course_id=course_id, quiz_id=assessment_id_fake))

        if response.status_code == 200 or response.status_code == 201:
            logger.info("resp status code is 200/201 for the assessment")
            resp_json = response.json()
            if resp_json.get('_class') =='user_attempted_quiz':
                logger.info(f"returning assessment id {resp_json.get('id')}")
                return resp_json.get('id')



