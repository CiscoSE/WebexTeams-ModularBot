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

#Location for temporary files
dirpath = os.getcwd()
tmpdir = "{}/../tmp".format(dirpath)


# API Server and port information for the base URL
api_host = "api.ciscospark.com"
api_port = 443


# TLS certificate verification boolean
# Should always be True unless using with development systems which don't use valid certificates
sslverify = True

# Set the bearer token, email, name, etc. for each bot to be handled in this script.
# Additional info may be added (e.g. room creation, webhook APIs, adding users to rooms) with future functionality
botinfo = {
    'dnabot': {
        'bearer': "MD...",
        'bot_email': "bot1email@webex.bot",
        'bot_name': "BOTName",
        'bot_org_id': "...",
        'bot_secret': "...",
        'auth_users': [
            'username@example.com'
        ]
    },
    'bot2': {
        'bearer': "N...",
        'bot_email': "bot2email@webex.bot",
        'bot_name': "BOT2Name",
        'bot_org_id': "...",
        'bot_secret': "...",
        'auth_users': [
            'username@example.com'
        ]
    },
    'bot3': {
        'bearer': "...",
        'bot_email': "bot3email@webex.bot",
        'bot_name': "BOT2Name",
        'bot_org_id': "...",
        'bot_secret': "...",
        'auth_users': [
            'username@example.com'
        ]
    }
}