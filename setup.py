from setuptools import setup, find_packages


with open('requirements.txt') as req_txt:
    required = req_txt.read().splitlines()

setup(name='declaranet',
    version='0.0.0.9000',
    description='Tools to scrape DeclaraNet',
    author='Jordan T. Bates',
    author_email='jtbates@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=required,
)
