"""
Copyright (c) 2019 Cisco and/or its affiliates.
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

from . import dnaConfig
import requests
import json
import time
import matplotlib.pyplot as plt
import numpy as np
import csv
import logging
import dateparser
import re
from collections import defaultdict


class dnaCenter:

    # Define global HTTP headers for requests.  Authorization via bearer token will be initialized during __init__
    globalHeaders = {
        "Content-Type": "application/json",
        "x-auth-token": ""
    }

    # Define global URLs for interacting with Webex Teams API here
    baseurl = "https://{0}:{1}".format(dnaConfig.dna_host, dnaConfig.dna_port)

    def __init__(self, logname=__name__, tmp=dnaConfig.tmpdir):
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
        # - Obtain an auth token from Cisco DNA Center and add the x-auth-token header
        # - Set the tmp folder for file attachments
        url = "{0}/dna/system/api/v1/auth/token".format(self.baseurl)

        r = requests.post(url, auth=(dnaConfig.dna_username, dnaConfig.dna_password), verify=dnaConfig.sslverify)
        r = r.json()
        self.globalHeaders['x-auth-token'] = r.get("Token")
        self.tmpfolder = tmp

    def __enter__(self):
        """
        Enter method - allows us to use 'with' when instantiating this class and do any cleanup at the end via the
        __exit__ method

        :return:
            self (for now)
        """
        return self

    def getHelpMessage(self):
        """
        Define the help message to display is an invalid command is entered (or 'help')

        :return:
            Text and rich-text strings to be sent to the requestor which describes available commands
        """

        helpMsgRich = """
Try one of the following commands:

***ASSURANCE:***

**show network health** Send an image displaying the current network health status

**show network health at *date/time*** Shows network health status for given date or time.  Most formats accepted

*Examples:*

*show network health at 06:21* will show health from today at 06:21

*show network health on Jan 1 at 18:00* will show health from January 1st at 18:00

All times and dates are local to the timezone where this script is being executed.

***INVENTORY***

**get inventory** Attach a CSV file with the network inventory

***SOFTWARE IMAGES***

**show software images** List available software images

**show software platforms** Show available platforms for software images

**show software images for *platform*** Show images available for *platform*

**show software recommended image for *platform*:** Show recommended CCO images for *platform*

**show software cco image for *platform*:** Shorter command to show recommended CCO images for *platform*
        """

        helpMsg = """
Try one of the following commands:

ASSURANCE:

show network health Send an image displaying the current network health status
show network health at *date/time Shows network health status for given date or time.  Most formats accepted

Examples:
show network health at 06:21 will show health from today at 06:21
show network health on Jan 1 at 18:00 will show health from January 1st at 18:00

All times and dates are local to the timezone where this script is being executed.


INVENTORY
get inventory Attach a CSV file with the network inventory

SOFTWARE IMAGES
show software images List available software images
show software platforms Show available platforms for software images
show software images for platform Show images available for platform
show software recommended image for platform: Show recommended CCO images for platform
show software cco image for platform: Shorter command to show recommended CCO images for platform
        """

        return self.generateApiResponse('message', helpMsg, richmessage=helpMsgRich)

    def parseTeamsMessage(self, msgdata):
        """
        Given the message from Webex Teams, parse it and determine which command (function) to run
        If no matching command is found, send back the help message

        :param msgdata:
            Message received by Webex Teams bot
        :return:
            API Response (returned by the called function and generated by generateApiResponse())
        """
        modifier = ""
        cmds = msgdata.lower()

        # Un-pretty method of getting a command and any modifiers.  If the message (command) includes any
        # of the keywords in the 'specifier' set, split the message into command and modifiers (NOTE: Only the
        # first occurrence will be split)
        # This can then be used to specify different options to functions - for example, showing a network health
        # image for a specific date / time instead of the current time.
        #
        # After the split, remove trailing whitespace from the cmd and leading whitespace from the modifier
        # There's surely a more elegant approach to this...
        specifier = ("for", "on", "at", "from", "mac", "ip", "address")

        reg = re.compile(r'(?i)\b(?:%s)\b' % '|'.join(specifier))
        if reg.search(cmds):
            cmds, modifier = re.split(reg, cmds, 1)
            cmds = str(cmds).rstrip()
            modifier = str(modifier).lstrip()

        # Now start figuring out which function to call based on 'cmds'.  Some functions may accept
        # modifiers - if so, parse accordingly
        if cmds == "show network health":
            if modifier != "":
                # Get health image for a specific date / time.  The dateparser helps convert various
                # time format strings to a datetime object which can be used to convert to epoch time
                # If an invalid date is entered, healthtime will be None.
                healthtime = dateparser.parse(modifier)
                self.logger.debug("The parsed time for the message is: %s", healthtime)
                # Ensure we have a valid time.  Convert to msecs from epoch if it's valid
                if healthtime != None:
                    healthtime = int(round(time.mktime(healthtime.timetuple()))) * 1000
                    retval = self.getNetworkHealthImage(timestamp=healthtime)
                else:
                    errmsg = "Error getting network health: invalid time entered!"
                    errmsgrich = "Error getting network health: ***invalid time entered!***"
                    self.logger.error(errmsg, exc_info=True)
                    retval = self.generateApiResponse('error', errmsg, richmessage=errmsgrich)
            else:
                # No modifier - just get the current health status image
                retval = self.getNetworkHealthImage()
        elif cmds == "get inventory":
            # Generates a CSV file containing the network inventory
            retval = self.getNetworkInventory()
        elif cmds == "show software platforms" or cmds == "show software platform":
            retval = self.getSoftwareImagePlatforms()
        elif cmds == "show software recommended image" or cmds == "show software cco image":
            if modifier != "":
                retval = self.getSoftwareImages(family=modifier, cco=True)
            else:
                retval = self.getSoftwareImages(cco=True)
        elif cmds == "show software image" or cmds == "show software images":
            if modifier != "":
                retval = self.getSoftwareImages(family=modifier)
            else:
                retval = self.getSoftwareImages()
        else:
            retval = self.getHelpMessage()

        return retval

    def generateApiResponse(self, type, message, richmessage="", file=""):
        """
        Generate a structured response to return to the apiHandler for a correct bot response
        Accepts rich text messages as well as non-formatted messages to support different clients.

        If the response is a simple message, the format is:
        {
            'responseType': 'message',
            'data': {
                'message': message,
                'richmessage': richmessage
            }
        }

        Error messages may be created which will be sent to the requestor:
        {
            'responseType': 'error',
            'data': {
                'message': message,
                'richmessage': richmessage
            }
        }


        For file attachments, we need to tell the bot where the file is... so this will work - note
        we will include the full path to the file
        {
            'responseType': 'file',
            'data': {
                'message': message,
                'richmessage': richmessage
                'file': file
            }
        }

        :param type:
            Type of response e.g. message/file
        :param message:
            The message to be sent from the bot
        :param file:
            For type 'file', the full path to a file attachment
        :return:
            Dictionary in format described above
        """

        if type == 'error':
            responsedata = {'message': message,
                            'richmessage': richmessage
                            }
        elif type == 'message':
            responsedata = {'message': message,
                            'richmessage': richmessage
                            }
        elif type == 'file':
            responsedata = {'message': message,
                            'richmessage': richmessage,
                            'file': file
                            }

        apiResponse = {'responseType': type,
                       'data': responsedata
                       }
        self.logger.debug("API Response from DNA Center:\n{}".format(apiResponse))
        return apiResponse

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

        return headers

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

        url = self.baseurl + url

        try:
            r = requests.get(url, headers=headers, verify=dnaConfig.sslverify)
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

        try:
            r = json.loads(r.text)
            self.logger.debug("DNA JSON Result of GET to %s is:\n%s", url, r)
        except json.decoder.JSONDecodeError as e:
            self.logger.error("JSON Decode error caught: %s", e, exc_info=True)
        else:
            retval = r

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

        url = self.baseurl + url

        try:
            self.logger.debug("Sending HTTP POST to %s", url)
            r = requests.post(url, data, headers=headers, verify=dnaConfig.sslverify)
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

        try:
            r = json.loads(r.text)
            self.logger.debug("DNA JSON Result of GET to %s is:\n%s", url, r)
        except json.decoder.JSONDecodeError as e:
            self.logger.error("JSON Decode error caught: %s", e, exc_info=True)
        else:
            retval = r

        return retval

    def assignHealthColor(self, healthScore):
        """
        Based on a given health score, assign a color for use in graphic representations of health
        Ranges adjusted here for consistency across visuals

        :param healthScore:
            Score representing a healthy percentage
        :return:
            Color name as a string value
        """
        if healthScore > 60:
            color = 'green'
        elif healthScore > 30:
            color = 'goldenrod'
        else:
            color = 'red'

        return color

    def drawHealthChart(self, data, timestamp, filename):
        """
        Uses matplotlib to draw a bar chart and save the PNG to the temporary directory

        Expects a dictionary structure and can generate any number of bars based on the given dict keys

        :param data:
            Structured health data.  This is a dictionary structured as follows:
            {
             'overallScore': (int)
             'health': {
                        (category): {
                                     'total': (int),
                                     'healthy': (int),
                                     'score': (int)
                                    }
                        }
            }

            Multiple categories may be specified e.g. Access, Distribution, WLC, AP.  The image will depict the
            number of healthy clients, the number of bad/unknown represented by (total - healthy), and a color
            based on the score of each category.

        :param timestamp:
            The timestamp when the health data was obtained.  Used in the title of the bar chart
        :param filename:
            Where to save the generated chart
        :return:
            True is the chart is successfully saved
            False otherwise
        """

        retval = False
        labels = list(data['health'].keys())
        colorchart = list()
        bartitles = list()

        numdevices = 0
        numhealthy = 0

        for types in dict.keys(data['health']):
            # print( "Data type and value: {0} {1}".format( types, data[types]))
            colorchart.append(self.assignHealthColor(data['health'][types]['score']))
            bartitles.append("{0}/{1} Healthy\n{2} Poor/Fair/No Data".format(data['health'][types]['healthy'],
                                                                             data['health'][types]['total'],
                                                                             data['health'][types]['total'] -
                                                                             data['health'][types]['healthy']
                                                                             )
                             )
            numdevices += data['health'][types]['total']
            numhealthy += data['health'][types]['healthy']

        # Begin creating the graph
        # plt is the imported matplotlib.pyplot
        # fig,ax creates figures and axes for subplots with figure size of 10 inches wide by 6 inches tall
        plt.rcdefaults()
        fig, ax = plt.subplots(figsize=(10, 6))

        # Evenly distribute the number of bars based on the length of the 'labels' list
        ind = np.arange(len(labels))

        # Set the number of ticks on the X axis to the value obtained by Numpy above
        # Also set the labels on the X axis for each bar
        ax.set_xticks(ind)
        ax.set_xticklabels(labels)

        # Set the Y axis height to 200.  Each bar will be of height '100' to show
        # equal heights.  This being done to represent health data in a similar fashion
        # as that obtained in the Cisco DNA Assurance health status
        ax.set_ylim([0, 200])

        # Set the title and assign to the graph
        title = "Network Device Health as of {0}\n{1}% Healthy".format(time.strftime("%Y-%m-%d %H:%M:%S %Z",
                                                                                     time.localtime(timestamp / 1000)
                                                                                     ),
                                                                       data['overallScore']
                                                                       )
        plt.title(title)

        # Get rid of all the borders around the graph.  Leave the labels in place on the X axis
        for spine in plt.gca().spines.values():
            spine.set_visible(False)
        plt.tick_params(top=False, bottom=False, left=False, right=False, labelleft=False, labelbottom=True)

        # Define (ind) number of bars.
        # All of height 100 and bar width is half of the total width available per section
        # (the number of sections being defined the 'ind') - represented by the .5 in the 3rd argument.
        # Start the bottom of each bar at y=1 so the border appears correctly (since we disabled all borders above).
        # Per-bar color will be assigned based on the values in the 'colorChart' list, and each bar
        # will have a black border.
        ax.bar(ind, 100, .5, bottom=1, color=colorchart, edgecolor='black')

        # Get rectangles (patches) - we will use this collection to add top labels to each bar
        rects = ax.patches

        # Add a top header to each bar which displays some health data
        # The label will be centered and added (height+5) above each bar
        for rect, label in zip(rects, bartitles):
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, height + 5, label,
                    ha='center', va='bottom')

        # Save the health image to (filename)
        try:
            plt.savefig(filename)
            self.logger.debug("Health chart successfully saved")
            retval = True
        except Exception as e:
            self.logger.error("drawHealthChart: There was a problem saving the generated image: %s", e, exc_info=True)

        return retval

    def getSoftwareImagePlatforms(self):
        """
        Generate a list of the available software platforms based on images present in Cisco DNA Center

        :return:
            Dictionary API response for Webex Teams reply
        """
        url = "/dna/intent/api/v1/image/importation"
        r = self.urlget(url)
        r = r['response']

        message = "Software images are available for the following platforms:\n"
        messagerich = "Software images are available for the following platforms:\n\n"

        platforms = set()

        for image in r:
            platforms.add(image['family'])

        for family in platforms:
            message += "{}\n".format(family)
            messagerich += "**{}**\n\n".format(family)

        return self.generateApiResponse('message', message, richmessage=messagerich)

    def getSoftwareImages(self, family="", cco=False):
        """
        Generate a list of the available software images

        :return:
            Dictionary API response for Webex Teams reply
        """
        url = "/dna/intent/api/v1/image/importation"

        if family != "" or cco == True:
            url += "?"
            if family != "":
                url += "family={}".format(family)
                if cco == True:
                    url += "&isCCORecommended=true"
            elif cco != False:
                url += "isCCORecommended=true"

        r = self.urlget(url)
        r = r['response']

        if r == []:
            msg = "No images are available which meet the specified criteria."
        else:
            platform = defaultdict(list)

            for image in r:
                details = {'name': image['name'],
                           'created': image['createdTime']}
                platform[image['family']].append(details)

            msg = "The following images are available:\n\n"
            for fam in platform:
                msg += "Platform: {}\n".format(fam)
                for image in platform[fam]:
                    msg += "\t{0}\n".format(image['name'])
                msg += "\n"

            self.logger.debug("getSoftwareImages:\n%s", msg)

        return self.generateApiResponse('message', msg, richmessage="")

    def getNetworkInventory(self):
        """
        Generate a CSV which contains the entire network inventory.  This is performed using a paginated GET
        request to the network-device API call to avoid timeout or processing too much data.

        Each iteration will retrieve (step) number of devices and process accordingly - the step may be adjusted up
        to the maximum supported by the API call (check Cisco DNA API documentation for details)

        The fields for the CSV are defined in the 'csvheader' variable - any JSON key returned from the URL
        may be included in this list and will be included in the generated inventory file.

        :return:
            Dictionary API response
        """
        step = 100
        start = 1
        end = step

        devices = list()

        csvheader = ['hostname', 'family', 'serialNumber', 'platformId', 'softwareVersion', 'macAddress',
                     'managementIpAddress']

        timestamp = int(round(time.time() * 1000))
        timestr = time.strftime("%Y-%m-%d_%H:%M:%S_%Z", time.localtime(timestamp / 1000))
        filename = "{0}/inventory_{1}.csv".format(self.tmpfolder, timestamp)

        # Begin iterating over the inventory returned from Cisco DNA Center.  Extend the fields list with retrieved
        # fields in the JSON response, then append the generated 'fields' list to the 'devices' list
        while True:
            url = "/dna/intent/api/v1/network-device/{0}/{1}".format(start, end)
            r = self.urlget(url)
            r = r['response']

            if r != []:
                for device in r:
                    fields = list()
                    for head in csvheader:
                        fields.extend([device[head]])
                    devices.append(fields)
                start += step
                end += step
            else:
                break

        # Generate the CSV file with header row
        with open(filename, 'w') as invfile:
            wr = csv.writer(invfile)
            wr.writerow(csvheader)
            for row in devices:
                wr.writerow(row)

        apimsg = "NetworkInventory_{}".format(timestr)
        return self.generateApiResponse('file', apimsg, file=filename)

    def getNetworkHealthImage(self, timestamp=int(round(time.time() * 1000))):
        """


        :param timestamp:
        :return:
        """
        retval = False
        url = "/dna/intent/api/v1/network-health?timestamp={0}".format(timestamp)
        headers = {
            '__runsync': 'true'
        }

        r = self.urlget(url, headers)

        if r == False:
            # There was a problem getting a response from the server.
            msg = "An error was encountered when retrieving network health.  Please contact your " \
                  "system administrator"
            msgrich = msg
            retval = self.generateApiResponse('error', msg, richmessage=msgrich)

        elif 'executionId' in dict.keys(r):
            # Sandbox version 1.2.6 doesn't return the health status anymore - if the JSON response includes
            # "executionId" then it's been placed into limbo and we can't generate an image.  Generate a response
            # to send which tells the requestor that health status information is unavailable
            msg = "There was a problem getting the network health.  " \
                  "This version of Cisco DNA Center may not support the called API. " \
                  "If this request was for a date/time, please make sure that Cisco DNA Center was " \
                  "running at the specified time (otherwise the health data would not be present)"
            msgrich = msg

            retval = self.generateApiResponse('error', msg, richmessage=msgrich)

        elif 'errorResponse' not in dict.keys(r):
            healthData = {'overallScore': r['response'][0]['healthScore']}
            healthData['health'] = dict()

            # Cisco DNA Center 1.2.8 has a typo in the API response (healthDistirubution).  Anticipate
            # that this will be corrected in the future
            if 'healthDistirubution' in r and 'healthDistribution' not in r:
                healthkey = 'healthDistirubution'
            elif 'healthDistribution' in r and 'healthDistirubution' not in r:
                healthkey = 'healthDistribution'

            for healthdist in r[healthkey]:
                healthData['health'][healthdist['category']] = {'total': healthdist['totalCount'],
                                                                'healthy': healthdist['goodCount'],
                                                                'score': healthdist['healthScore'],
                                                                }

            print("Healthdata:\n{}".format(healthData))

            filename = "{0}/NetworkHealth_{1}.png".format(self.tmpfolder, timestamp)

            if self.drawHealthChart(data=healthData, timestamp=timestamp, filename=filename):
                self.logger.debug("Health chart generated")
                apimsg = "NetworkHealth_{}".format(timestamp)
                retval = self.generateApiResponse('file', apimsg, file=filename)
            else:
                self.logger.warning("Problem generating health chart")
                logmsg = "There was a problem generating the health chart.  Check the logs for details"
                retval = self.generateApiResponse('error', logmsg, richmessage=logmsg)

        else:
            errorcode = r['errorResponse']['componentErrorResponse'][0]['compErrorCode']
            errormsg = r['errorResponse']['componentErrorResponse'][0]['compErrorMessage']
            logmsg = "Error getting Cisco DNA network health... Error code {0} ({1})".format(errorcode, errormsg)
            logmsg += "Hint: If you were attempting to obtain health for a specific time, make sure Cisco DNA Center was running on the specified date / time."
            logmsgrich = "\n\nError getting Cisco DNA network health... Error code {0} ({1})\n\n".format(errorcode,
                                                                                                         errormsg)
            logmsgrich += "**Hint:** *If you were attempting to obtain health for a specific time, make sure Cisco DNA Center was running on the specified date / time.*\n\n"

            self.logger.error(logmsg, exc_info=True)
            retval = self.generateApiResponse('error', logmsg, richmessage=logmsgrich)

        return retval

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit method - in conjunction with __enter__, allows us to use 'with' when instantiating this class.
        Any object cleanup tasks go here.

        :return:
            True (for now)
        """
        return False
