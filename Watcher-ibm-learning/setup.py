import pathlib

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()



setup(
    name="udemy-enroller",
    version="4.1.2",
    long_description_content_type="text/markdown",
    author="aapatre",
    author_email="udemyenroller@gmail.com",
    maintainer="fakeid cullzie",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="udemy, education, enroll",
    packages=find_packages(
        exclude=["*tests*"],
    ),
    python_requires=">=3.8, <4",
    install_requires=[
        "aiohttp[speedups]==3.8.1",
        "beautifulsoup4==4.11.1",
        "ruamel.yaml==0.16.13",
        "requests==2.27.1",
        "cloudscraper==1.2.60",
        "webdriver-manager==3.7.0",
        "selenium==3.141.0",
        "price-parser==0.3.4",
    ],
    setup_requires=["pytest-runner"],
    extras_require={
        "dev": ["black", "isort"],
        "test": ["pytest", "pytest-cov"],
    },
    entry_points={
        "console_scripts": [
            "watcher_ibm=watcher_ibm.cli:main",
        ],
    },
)
