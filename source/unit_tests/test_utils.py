#########################################################################################
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.                    #
# SPDX-License-Identifier: MIT-0                                                        #
#                                                                                       #
# Permission is hereby granted, free of charge, to any person obtaining a copy of this  #
# software and associated documentation files (the "Software"), to deal in the Software #
# without restriction, including without limitation the rights to use, copy, modify,    #
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to    #
# permit persons to whom the Software is furnished to do so.                            #
#                                                                                       #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,   #
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A         #
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT    #
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION     #
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE        #
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                #
#########################################################################################
import pytest
from source.python.Utilities import validate_config_input

@pytest.mark.parametrize("inputKey, regex, lb, ub,ValidoutPut",[
    #positive smoke test
    ("smokevalidtest","^[A-Za-z0-9-:_]{1,1000}$",1,1000,True)
])
def test_valid_config_validation(inputKey,regex, lb, ub,ValidoutPut):
    assert validate_config_input (inputKey,regex, lb, ub) == ValidoutPut

@pytest.mark.parametrize("inputKey, regex, lb, ub,InvalidoutPut",[
    #negative testing length checks, lb
    ("","^[A-Za-z0-9-:_]{1,1000}$",1,1,False),
    #negative testing length checks, ub
    ("Morethan10characterslong","^[A-Za-z0-9-:_]{1,10}$",1,1,False),
    #negative, Testing reg expression check
    ("Somestringwith+","^[A-Za-z0-9-:_]{1,100}$",1,1,False)
])
def test_Invalid_config_validation(inputKey,regex, lb, ub,InvalidoutPut):
    assert validate_config_input (inputKey,regex, lb, ub) == InvalidoutPut

