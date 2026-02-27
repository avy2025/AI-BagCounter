from setuptools import setup, find_packages

setup(
    name="AI-BagCounter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ultralytics==8.2.0",
        "opencv-python==4.9.0.80",
        "numpy<2.0.0",
        "PyYAML==6.0.1",
        "matplotlib==3.8.4",
        "tqdm==4.66.2",
    ],
    entry_points={
        "console_scripts": [
            "bag-counter=main:main",
        ],
    },
    author="Your Name",
    description="AI-powered jute sack counting system for warehouse logistics",
    license="MIT",
    url="https://github.com/yourusername/AI-BagCounter",
)
