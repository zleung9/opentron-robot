from setuptools import setup, find_packages

setup(
    name='auto',
    version='0.0.1',
    description="A platform for controling all the robots in Automat's lat ",
    license='See license',
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "paramiko",
        "scp",
    ],
    entry_points={ # create scripts and add to sys.PATH
        'console_scripts': [
            # to be added
        ],
    },
)