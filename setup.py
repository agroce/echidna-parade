#-*- coding:utf-8 -*-

from setuptools import setup

setup(
    name='echidna-hammer',
    version='0.1',
    description='Meta-tool to hammer a contract with various configs, using Echidna',
    long_description_content_type="text/markdown",    
    long_description=open('README.md').read(),
    packages=['echidna_hammer',],
    license='MIT',
    entry_points="""
    [console_scripts]
    echidna-hammer = echidna_hammer.echidna_hammer:main
    """,
    keywords='testing tstl',
    test_suite='nose.collector',
    tests_require=['nose'],
    classifiers=[
      "Intended Audience :: Developers",
      "Development Status :: 4 - Beta",
      "Programming Language :: Python :: 2",
      "Programming Language :: Python :: 3",
      ],
    install_requires=[
      'pyyaml',
      'slither-analyzer',
      'crytic-compile'
    ],
    url='https://github.com/agroce/echidna-hammer',
)
