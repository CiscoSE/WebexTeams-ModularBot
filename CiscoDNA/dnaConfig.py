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

# Location for temporary files
dirpath = os.getcwd()
tmpdir = "{}/../tmp".format(dirpath)

# TLS certificate verification boolean
# Should always be True unless using with development systems which don't use valid certificates
sslverify = True

# Set the hostname, port, username, password for connecting to Cisco DNA Center
dna_host = "ciscodnac.example.com"
dna_port = 443
dna_username = "ciscodnacusername"
dna_password = "ciscodnacpassword"