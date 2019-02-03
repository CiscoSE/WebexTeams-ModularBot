"""
Copyright (c) 2018 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.0 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
import os
import time

"""
Location for temporary files
"""
dirpath = os.getcwd()
tmpdir = "{}/tmp".format(dirpath)

"""
Logfile name and location

The 'logname' variable will be used by the apiHandler to define a logging instance with the same name
"""
logname = "apihandler"
timestamp = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())
logfile = "{0}_{1}.log".format(logname, timestamp)

