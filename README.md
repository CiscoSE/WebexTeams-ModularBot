# WebexTeams-ModularBot
Modular Bot for Cisco Webex Teams

This application is designed to integrate any number of Cisco intent-based networking APIs with Webex Teams.

Initial operational capability is provided for a subset of Cisco DNA Center tasks - basic health status of the network, software image status, and the ability to generate a CSV file containing the inventory of network devices.

# Making the App work

### 1: Pre-requisites 
1.Python3

2.Requirements pip install -r requirements.txt

To register a Bot, you’ll need to be logged in to Webex For-Developers Page with a “real” user – each bot needs to be tied to an actual user account. Adding one is extra simple, On the page, select “Create a Bot”; there’s only a couple fields to fill out

Display Name is how you want the bot to show up in a room (like “DNABot-Demo”); 

Bot Username is the email address, since every Spark user is registered under an email – this should be similar to the Display Name, but it can be unique.  Note that you are not populating the entire email – they will always end with @sparkbot.io, can’t make on with a gmail.com email or anything similar, so you’re just adding the prefix. The username prefix does need to be unique; if you don’t get a green check at the end of the @sparkbot.io reference, then the username was already taken. The Icon is the avatar for the bot, which will also show inside a room. 

Once the bot is created, you’ll need to save the access token that is provided – keep it someplace safe.  The token effectively never expires (it’s good for 100 years) but if you forget it, you’ll have to generate a new one. There’s no way to get it back.

#### 2: Create an Outbound Webhook

Your webhook URL needs to be accessible on the public Internet – if you want to use your local machine, you can use a service like Ngrok to make your personal machine accessible to the world on a specific port for free.

But that means the webhook only works when you machine is up and live. 

Once you have an endpoint to use, create the webhook using the request on this page.
https://developer.ciscospark.com/endpoint-webhooks-post.html


Make sure that the bearer token used in creating the webhook is the bearer token of the bot.

## Running the Code

#### 1. Clone the code

```
git clone https://github.com/psample-Cisco/WebexTeams-ModularBot.git
```

#### 2. Create a Python Virtual Environment

```
python3 -m venv venv
source venv/bin/activate
```

#### 3. Setup the dependencies

```
pip3 install -r requirements.txt
```

#### 4. Configure the CiscoWebex/webexConfig.py file
Multiple bots may be configured here.  The idea is that each app (represented via API call to the main program) can be handled by a separate bot.  The webexConfig.py file includes a Python dictionary structure similar to:


```
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
    }
```
For each bot, configure the relevant information.

#### 5. Configure the CiscoDNA/dnaConfig.py file
Set the values for the host, port, username, and password:
```
dna_host = "ciscodnac.example.com"
dna_port = 443
dna_username = "ciscodnacusername"
dna_password = "ciscodnacpassword"
```
These values will be used to obtain a Token for subsequent API calls.

#### 6. Run the application via uwsgi
From a command prompt, ensure you have loaded the virtual environment for the application.  Afterward, you may start the app handler using the installed 'uwsgi' handler

```
uwsgi --callable app ./uwsgi.ini
```

#### 7. Interact with the bot
Using the Webex Teams client, send a direct message to the Bot to interact.  Not sure which one?  Try 'help' - this will show a list of commands available to execute.

## Examples:
