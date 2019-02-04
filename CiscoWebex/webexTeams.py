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

"""
/**********************************************************************************************************************
This package contains code used to interface with the Webex Teams API.
/**********************************************************************************************************************
"""

from . import webexConfig
import requests
import hmac
import hashlib
import magic
import logging
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder

class webexTeams:

    # Define global HTTP headers for requests.  Authorization via bearer token will be initialized during __init__
    globalHeaders = {
        "Content-Type": "application/json",
        "Authorization": ""
    }

    # Define global URLs for interacting with Webex Teams API here
    urlBase = "https://{0}:{1}".format( webexConfig.api_host, webexConfig.api_port)
    urlMessage = "{}/v1/messages".format(urlBase)
    urlPeople = "{}/v1/people".format(urlBase)

    def __init__( self, botname, logname=__name__, tmp=webexConfig.tmpdir):
        """
        Class initialization.

        :param botname:
            Name of the bot being used.  Used to read correct configuration stanzas
        :param logname:
            Name of the calling logger.  If not given, use the package name
        :param tmp:
            Directory for storing temporary files.  If not given, use value from config file.
        """

        # If the logger name was passed, append this package's name to it.  Otherwise, create a new logger with
        # only the package name
        if logname != __name__:
            logname = "{0}.{1}".format(logname, __name__)
        self.logger = logging.getLogger(logname)

        # Now do some init stuff:
        # - Pull in the config for this bot (specified by 'botname')
        # - Set the tmp folder for file attachments
        # - Set the global Authorization bearer token value in the global headers
        self.botConfig = webexConfig.botinfo[botname]
        self.tmpfolder = tmp
        self.globalHeaders['Authorization'] = "Bearer {}".format(self.botConfig['bearer'])

    def __enter__(self):
        """
        Enter method - allows us to use 'with' when instantiating this class and do any cleanup at the end via the
        __exit__ method

        :return:
            self (for now)
        """
        return self

    def cleanHeaders(self, headers, addHeaders):
        """
        Take the default headers and compare to items in the additional headers
        requested by a method.  If any matching key has a value of None, remove
        that key from the header dict.

        :param headers:
            The headers which will be sent in the HTTP request
        :param addHeaders:
            Delta header dictionary used to check for 'None' values
        :return:
            Dictionary containing the cleaned headers
        """
        for key in addHeaders.keys():
            if key == None and headers[key] != "":
                del headers[key]

        return (headers)

    def urlget(self, url, addHeaders={}):
        """
        Generic 'GET' method for HTTP requests.  Will attempt a GET request and catch exceptions.

        :param url:
            URL to perform HTTP GET
        :param addHeaders:
            Dictionary containing additional headers (if needed)
        :return:
            The server's response if successful, otherwise False
        """
        retval = False

        # Make a copy of the global headers.  If the calling function must add values, update the copy with the
        # difference.  Also, is the calling function sets a header key to 'None,' remove that key (via the
        # cleanHeaders function)
        headers = self.globalHeaders.copy()
        headers.update(addHeaders)
        headers = self.cleanHeaders(headers, addHeaders)

        try:
            r = requests.get(url, headers=headers, verify=webexConfig.sslverify)
            self.logger.debug("urlget: HTTP GET sent:\n\tURL: %s\n\tResponse: %s", url, r.text)
            r.raise_for_status()
            retval = r.json()
        except requests.exceptions.HTTPError as errh:
            self.logger.error("urlget: Http Error: %s", errh, exc_info=True)
        except requests.exceptions.ConnectionError as errc:
            self.logger.error("urlget: Error Connecting: %s", errc, exc_info=True)
        except requests.exceptions.Timeout as errt:
            self.logger.error("urlget: Timeout Error: %s", errt, exc_info=True)
        except requests.exceptions.RequestException as err:
            self.logger.error("urlget: Generic Request Exception: %s", err, exc_info=True)

        return retval

    def urlpost(self, url, data, addHeaders={}):
        """
        Generic HTTP POST wrapper which catches exceptions.

        :param url:
            URL for the HTTP POST
        :param data:
            What to POST
        :param addHeaders:
            Dictionary containing additional headers if needed
        :return:
            The server's response if successful, otherwise False
        """
        retval = False

        # Make a copy of the global headers.  If the calling function must add values, update the copy with the
        # difference.  Also, is the calling function sets a header key to 'None,' remove that key (via the
        # cleanHeaders function)
        headers = self.globalHeaders.copy()
        headers.update(addHeaders)
        headers = self.cleanHeaders(headers, addHeaders)

        try:
            self.logger.debug("Sending HTTP POST to %s", url)
            r = requests.post(url, data, headers=headers, verify=webexConfig.sslverify)
            self.logger.debug("urlpost: HTTP POST sent:\n\tURL: %s\n\tResponse: %s", url, r.text)
            r.raise_for_status()
            retval = r
        except requests.exceptions.HTTPError as errh:
            self.logger.error("urlpost: Http Error: %s", errh, exc_info=True)
        except requests.exceptions.ConnectionError as errc:
            self.logger.error("urlpost: Error Connecting: %s", errc, exc_info=True)
        except requests.exceptions.Timeout as errt:
            self.logger.error("urlpost: Timeout Error: %s", errt, exc_info=True)
        except requests.exceptions.RequestException as err:
            self.logger.error("urlpost: Generic Request Exception: %s", err, exc_info=True)

        return retval

    def sendMessage( self, roomid, message, richmessage=""):
        """
        Send a message to the specified roomid.  The message is expected; if a rich-formatted message is given then
        also include that for client which support rich text (e.g. Webex Teams client)

        :param roomid:
            Room ID to send the message
        :param message:
            Non-rich text message to send
        :param richmessage:
            Optional - rich formatted text to send
        :return:
            The server's response if successful, otherwise False
        """
        retval = False
        webexmsg = {
                        'roomId': roomid,
                        'text': message
                    }

        # Include the rich message if it was passed to us
        if richmessage != "":
            webexmsg['markdown'] = richmessage

        self.logger.debug("sendMessage: Sending message:\n\tRoom ID: %s\n\tMessage:%s", roomid, message)
        # url = self.urlMessage

        if self.urlpost(self.urlMessage, json.dumps(webexmsg)) != False:
            retval = True

        return retval

    def getMimeType(self, file):
        """
        Given a file, use the 'magic' module (from python-magic) to try to identify the file's MIME type.  Used when
        attaching a file to a Webex Teams message.

        :param file:
            Full path of the file needing a MIME type
        :return:
            MIME type of the specified file
        """
        mime = magic.Magic(mime=True)
        self.logger.debug("getMimeType: File %s has MIME type of: %s", file, mime)
        return(mime.from_file(file))


    def attachFile(self, roomid, file, message):
        """
        Send a file attachment to the specified Webex Teams room.  Get the MIME type of the file, update
        The Content-Type header, and attach the file with a caption

        :param roomid:
            Room ID where the file will be posted
        :param file:
            Path and filename of the file attachment
        :param message:
            Caption sent with the file attachment
        :return:
            True on success, False otherwise
        """
        retval = False
        media = MultipartEncoder(
                                    {
                                        'roomId': roomid,
                                        'text': message,
                                        'files': (
                                            message,
                                            open(file, 'rb'),
                                            self.getMimeType(file)
                                        )
                                    }
                                 )

        # Set the Content-Type header to send to the POST wrapper
        headers = {'Content-Type': media.content_type}
        # url = self.urlMessage
        self.logger.debug("attachFile: Sending file:\n\tFilename: %s\n\tRoom ID: %s\n\tMessage:%s", file, roomid, message)

        if self.urlpost(self.urlMessage, media, headers) != False:
            retval = True

        return retval

    def getMessage(self, messageid):
        """
        Given a message ID, get the message contents

        :param messageid:
            ID of the message to retrieve
        :return:
            API response of the message GET request on success, False otherwise
        """
        retval = False
        self.logger.debug("getMessage: Getting message ID {}".format(messageid))

        # Construct the URL and send the GET request
        url = self.urlMessage + "/{}".format(messageid)
        r = self.urlget(url)

        # Verify the response.  If not False, return the message contents
        if r != False:
            self.logger.debug("getMessage: Successfully retrieved message.")
            retval = r
        else:
            self.logger.error("getMessage: Problem retrieving message!  Check logfile for details.", exc_info=True)

        return retval


    def getPerson( self, person):
        """
        Given a person ID, get that person's information

        :param person:
            ID of the person to retrieve
        :return:
            API response of the person GET request on success, False otherwise
        """
        retval = False
        self.logger.debug("getPerson: Getting person with ID {}".format(person))

        # Construct the URL and send the GET request
        url = self.urlPeople + "/{}".format(person)
        r = self.urlget(url)

        # Verify response.  If not False, return person information
        if r != False:
            retval = r
            self.logger.debug("getPerson: Successfully retrieved person")
        else:
            self.logger.error("getPerson: Problem retrieving person!  Check logfile for details.", exc_info=True)
        return retval


    def validateMessage(self, msg, headers): #, botconfig):
        """
        Validate incoming messages.  Check the X-Spark-Signature against our secret key for the webhook,
        Verify the person is allowed to send messages to the bot, and verify that the requestor is not the bot itself
        If all steps pass, the message is valid and may be acted upon.

        :param msg:
            RAW incoming message received by the webhook
        :param headers:
            The request headers received by the webhook
        :return:
            True if message is valid, False otherwise.
        """
        retval = False

        hashedsig = hmac.new(bytes(self.botConfig['bot_secret'].encode("utf-8")),
                             bytes(msg.encode("utf-8")), hashlib.sha1
                             )
        validatedsig = hashedsig.hexdigest()
        if validatedsig == headers.get( 'X-Spark-Signature'):
            self.logger.debug("validateMessage: Header validation succeeded.  Continue validation...")
            msg = json.loads(msg)
            requestor = msg['data']['personEmail']
            if requestor != self.botConfig['bot_email']:
                self.logger.debug("validateMessage: Requestor is not the same as the bot.  Continue validation...")
                person = self.getPerson(msg['data']['personId'])
                self.logger.debug("validateMessage: Person org ID:\n%s", person['orgId'])
                if person != False:
                    if person['orgId'] == self.botConfig['bot_org_id']\
                            or requestor in self.botConfig['auth_users']:
                        self.logger.debug("validateMessage: Requestor has been validated.  Validation complete.")
                        retval = True
                    else:
                        self.logger.info("validateMessage: Validation of the requestor failed.  Message not valid.")
                else:
                    self.logger.warning("validateMessage: Problem getting person from message - check logfile for details.")
            else:
                self.logger.debug("validateMessage: Requestor is the same as the bot.  Message not valid.")
        else:
            self.logger.debug("validateMessage: Header validation failed.  Message not valid.")
        return retval

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit method - in conjunction with __enter__, allows us to use 'with' when instantiating this class.
        Any object cleanup tasks go here.

        :return:
            True (for now)
        """
        return True
