# Introduction

This is a python script for batch run the tests in HKUST COMP 2012H programming assignment.

# Basic Setup

1. drop the `run_tests.py` to the same directory as your source code
2. move all the test input to `tests/in`, all the test output to `test/out`, in the same directory of run_tests.py
3. Set the `CLANG` variable in `run_tests.py` to your compiler path(e.g. g++ or clang++, if you dont sure just type `g++`)
4. Set the `CLANG_ARGS` variable in `run_tests.py` to your compiler args, if you dont sure just copy-and-paste the `CPPFLAGS` in your makefile.

# Running the tests

For interactive run, simply:
```
python ./run_tests.py
# If python is not found, try:
python3 ./run_tests.py
```

If you want to have it automated, and export the logs, do:
```
echo y | python ./run_tests.py > tests.log
# If python is not found, try:
echo y | python3 ./run_tests.py > tests.log
```
