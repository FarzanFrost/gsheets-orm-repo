from setuptools import setup, find_packages

setup(
    name="gsheets-orm",
    version="0.1.2",
    author="FarzanFrost",
    description="A lightweight Object-Relational Mapper (ORM) backed by Google Sheets",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/FarzanFrost/gsheets-orm-repo",
    packages=find_packages(exclude=["tests*", "docs*"]),
    install_requires=[
        "gspread>=5.10.0",
        "google-auth>=2.20.0",
        "python-dotenv>=1.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
