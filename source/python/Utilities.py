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

import re

# fucntion to read configurations from a ini configuration file
def read_configuration_value(configfile,SectionName, RequestedParam):
    try:
        from configparser import ConfigParser
    except ImportError:
        print("error importing required library for reading configurations")

    # instantiate
    config = ConfigParser()

    # parse existing file
    config.read(configfile)

    return config.get(SectionName, RequestedParam)


# Function to validate inputs against a regular expression and length inputs
def validate_config_input(inputKey, regex, lb=1, ub=10):
    inputType = type(inputKey)
    if inputType == int:
        #skip length check and just match the pattern
        return re.match(regex,inputKey) is not None
    elif inputType== str:
        if len(inputKey) <= lb or len(inputKey) > ub:
            return False
    # Match returns none if pattern not found
    else:
        return "unknown input type"
    return re.match(regex, inputKey) is not None
