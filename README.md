# Udemy-Auto
[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)
* ALPHA IS A PRE DEVELOPMENT BRANCH!

* ANY DEVELOPER WILLING TO CONTRIBUTE FEEL FREE TO FORK IT/OPEN PULL REQUESTS

ARE YOU BORED ABOUT SPENDING TIME TO GET BADGES ON UDEMY TO CERTIFY YOUR KNOWLEDGE?
Don't worry, with the power of web-scraping and automation, this script will watch it for you and also solve boring quizzes!<br>
<b>Only multiple choices quizzes are addressed in the current version</b>



In case of any bugs or issues, please open an issue.

Also, don't forget to **Fork & Star the repository if you like it!**


** **_Disclaimer & WARNINGS:_**

1. **Use** this ONLY for **Educational Purposes!** By using this code you agree
   that **I'm not responsible for any kind of trouble** caused by the code. **THIS PROJECT IS NOT AFFILIATED WITH UDEMY.**
2. **Make sure web-scraping is legal in your region.**
3. This is **NOT a hacking script**!
---

** Requirements:

*** How to Install the Requirements?

**Tested Python version:** [Python 3.8+](https://www.python.org/downloads/)

**(Windows users only) Required Microsoft Visual C++ 14.0+ version:** [Microsoft Visual C++ 14.0+](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

![alt text](https://docs.microsoft.com/answers/storage/attachments/34873-10262.png)

**You must have pip or poetry installed. Please look up how to install them in your OS.**

Download a release of this project or clone the repository then navigate to the
folder where you placed the files on. <br>
Type `pip install -r requirements.txt` to
get all the requirements installed in one go. Similar instructions applies for poetry.

---

1 . Install the required packages

2 . Run the script and the cli will guide you through the settings required
3 . If you decide to save the settings they will be stored in your home directory: <br>
    **Windows**:
    `C:/Users/CurrentUserName/.watcher_udemy` <br>
    **Linux**:
    `/home/CurrentUserName/.watcher_udemy` <br>
    **The values in settings.yaml should be in the same language as the site you are browsing on**

4 . The script can be passed arguments:

- `--help`: View full list of arguments available
- `--browser=<BROWSER_NAME>`: Run with a specific browser 
- `--udemybase`: Run the udemy scraper only (TODO: Add functionality for free users and not business users only).
- `--max-pages=<NUMBER>`: Max number of pages to scrape from sites before exiting the script (default is 5)
- `--delete-settings`: Delete existing settings file
- `--delete-cookie`: Delete the cookie file if it exists
- `--debug`: Enable debug logging
- `--file=<name_of_the_file.txt>` : Name of the file you want to scrape urls from
- `--scrape_from_file` : Enable scraping from file instead of scraping from the "in progress" courses.

5 . Run the script in terminal with your target arguments:

- `udemy_watcher`
- `udemy_watcher --browser=chrome --scrape_from_file=True --file=file.txt`

## FAQs

*** 1. Can I use this script with a non business udemy acccount?<br>
Well, short answer is NO.<br>
Could I do with by making some minor changes to the code?  Yes.<br>

## Support & Maintenance Notice

By using this repo/script, you agree that the authors and contributors are under no obligation to provide support for the script and can discontinue it's development, as and when necessary, without prior notice.
