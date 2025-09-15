from setuptools import setup, find_packages

setup(
    name="creiq",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
    ],
    python_requires=">=3.6",
    author="CREIQ Team",
    author_email="example@example.com",
    description="A package for processing roll numbers and generating URLs",
    keywords="roll numbers, URLs",
    entry_points={
        "console_scripts": [
            "creiq=creiq.cli:main",
        ],
    },
)