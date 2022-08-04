import aiohttp
from bs4 import BeautifulSoup

from udemy_enroller.logging import get_logger

logger = get_logger()
#import driver manager instance from cli file


async def get(url, headers=None):
    """
    Send REST get request to the url passed in

    :param url: The Url to get call get request on
    :param headers: The headers to pass with the get request
    :return: data if any exists
    """

    #can't do it no more because html gets created by js.
    #got to use the driver.


    # if headers is None:
    #     headers = {}
    # try:
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(url, headers=headers) as response:
    #             text = await response.read()
    #             return text
    # except Exception as e:
    #     logger.error(f"Error in get request: {e}")
