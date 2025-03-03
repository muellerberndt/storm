from setuptools import setup, find_packages

setup(
    name="storm",
    version="0.1.0",
    description="A tool for flood testing and light fuzzing of blockchain node APIs",
    author="Storm Team",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "asyncio>=3.4.3",
    ],
    entry_points={
        "console_scripts": [
            "storm=storm.__main__:main",
        ],
    },
    python_requires=">=3.7",
) 