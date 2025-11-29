# Introduction

This is a python script for batch run the tests in HKUST COMP 2012H programming assignment.

# Basic Setup

1. drop the `run_tests.py` to the same directory as your source code
2. move all the test input to `tests/in`, all the test output to `test/out`, in the same directory of run_tests.py
3. Set the `CLANG` variable in `run_tests.py` to your compiler path(e.g. g++ or clang++, if you dont sure just type `g++`)
4. Set the `CLANG_ARGS` variable in `run_tests.py` to your compiler args, if you dont sure just copy-and-paste the `CPPFLAGS` in your makefile.
5. add a placehold before `return 0` to let script know where to seperate normal output and memery report:
```c++
int main() {
  /* existing code */
	std::cout << "EOS"; // <- add this line
	return 0;
}
```
6. If you are using MacOS, you need to add a suppression due to the existance of false positive from the mem leak by dynamic linking:
   - Create a `lsan.supp` file in the same directory
   - Add following content:
	```
	leak:libobjc.A.dylib
	leak:libxpc.dylib
	leak:dyld
	leak:libsystem_malloc.dylib
	leak:libSystem.B.dylib
	```
   - In the terminal you are going to use to run the python script, execute:
	```
	export LSAN_OPTIONS=suppressions=lsan.supp
	```

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
