#!/usr/bin/env python3
"""
Fidelity Portfolio Tracker - Automated portfolio data collection and analysis
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name='fidelity-portfolio-tracker',
    version='2.0.0',
    description='Automated Fidelity portfolio data collection and analysis tool',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='Randy Lust',
    author_email='your_email@example.com',
    url='https://github.com/yourusername/fidelity-portfolio-tracker',
    license='MIT',

    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,

    install_requires=[
        'fidelity-api>=0.0.16',
        'python-dotenv>=1.0.1',
        'yfinance>=0.2.52',
        'click>=8.1.7',
        'rich>=13.7.0',
        'pyyaml>=6.0.1',
        'keyring>=24.3.0',
        'loguru>=0.7.2',
        'apscheduler>=3.10.4',
        'streamlit>=1.29.0',
        'plotly>=5.18.0',
        'pandas>=2.2.0',
        'tqdm>=4.66.1',
    ],

    extras_require={
        'dev': [
            'pytest>=7.4.3',
            'pytest-cov>=4.1.0',
            'black>=23.12.0',
            'flake8>=7.0.0',
            'mypy>=1.8.0',
        ],
    },

    entry_points={
        'console_scripts': [
            'portfolio-tracker=fidelity_tracker.cli.commands:cli',
        ],
    },

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Office/Business :: Financial :: Investment',
    ],

    python_requires='>=3.8',

    keywords='fidelity portfolio investment tracking finance',
)
