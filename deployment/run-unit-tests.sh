#!/bin/bash
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./run-unit-tests.sh
#

source_template_dir="$PWD"
source_code_dir="../source"
unit_test_dir="$source_code_dir/unit_tests"


# enter the main test directory
cd $unit_test_dir

# Run all tests int he directory
py.test



