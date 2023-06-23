import json

import requests
import websocket
from decouple import config
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from websocket import WebSocket


#  the first url https://wss.hyper-api.com/authorize.php?app_id=16e7b3c2f99fa1e39005697c8c5df038&grant=oauth&response_type=code&client_id=16e7b3c2f99fa1e39005697c8c5df038&state=xyz
# the redirect url https://wss.hyper-api.com/crypto-prices.py/authorize?code=e0abbb4fec3d0cb923f24bcd9ab467e8e8847cb0&state=xyz
# new https://wss.hyper-api.com/crypto-prices.py/authorize?code=190450c7c947f299e0927f4639513cbfdf4505bc&state=xyz

class ClickAutomation:
    def __init__(self):
        s = Service(ChromeDriverManager().install())
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('headless')
        # keep chrome open
        # self.options.add_experimental_option("detach", True)
        self.options.add_experimental_option(
            "excludeSwitches",
            ['enable-logging'])
        self.driver = webdriver.Chrome(
            options=self.options,
            service=s)
        self.driver.implicitly_wait(50)
        self.APP_ID = config("APP_ID")
        self.BASE_URL = f"https://wss.hyper-api.com/authorize.php?app_id={self.APP_ID}&grant=oauth&response_type=code&client_id={self.APP_ID}&state=xyz"

        self.collection = []
        super(ClickAutomation, self).__init__()

    def __enter__(self):
        self.driver.get(self.BASE_URL)

    def login_submit(self):
        self.driver.get(self.BASE_URL)
        # add email
        self.driver.find_element(by=By.CSS_SELECTOR, value='input[name="user_email"]').send_keys(config("EMAIL"))
        # add password
        self.driver.find_element(by=By.CSS_SELECTOR, value='input[name="user_password"]').send_keys(config("PASSWORD"))
        #  submit
        self.driver.find_element(by=By.CSS_SELECTOR, value='button[type="submit"]').click()
        # click yes to get the code
        # Wait until the element is clickable
        wait = WebDriverWait(self.driver, 10)
        element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[value="yes"]')))

        # Click the element
        element.click()

        # https://wss.hyper-api.com/crypto-prices.py/authorize?code=f4ed85a78142527d10c05cc11b100eacee128c9c&state=xyz
        code = self.driver.current_url.split("code=")[1].split("&")[0]

        return code


def get_authorization_code():
    """
    this is used to get the authorization code from selenium  webscraping bot
    :return:

    """
    bot = ClickAutomation()
    # login the mail
    try:
        code = bot.login_submit()
        print("code :", code)
    except Exception as a:
        print("Error Getting Code :", a)
        exit()
    return code


def get_authorization_token(code):
    """this is used ti get the authorization token"""

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    url = "https://wss.hyper-api.com/token.php"

    data = {
        "code": code,
        "grant_type": "authorization_code"
    }

    auth = (config("APP_ID"), config("API_KEY"))  # Replace with your application ID and key

    response = requests.post(url, headers=headers, data=data,
                             auth=auth
                             )
    json_object = response.json()
    print(json_object)
    if response.status_code == 200:
        access_token = json_object["access_token"]

        print("Access Token:", access_token)

        return access_token
    return None


def test_access_token():
    """
    this is used to access the market subscribe route
    :param access_token:
    :return:
    """

    # Set the server URL
    server_url = 'wss://wss.hyper-api.com:5553/spectreai/'

    # Set your Application ID
    application_id = config("APP_ID")

    # Establish WebSocket connection
    if websocket.enableTrace:
        websocket.enableTrace(True)

    ws = websocket.WebSocket()
    ws.connect(server_url, header=['Sec-WebSocket-Protocol: ' + application_id])

    # Check if the connection is open
    if ws.connected:
        print("Connected to server.")

        # Send/receive messages or perform other operations here

        # Close the connection
        ws.close()
    else:
        print("Failed to connect to the server.")


def get_market_subscribe(access_token):
    # Connect to the server
    socket = websocket.WebSocket()
    server_url = 'wss://wss.hyper-api.com:5553/spectreai/'
    # socket.connect(serverUrl)
    # Set your Application ID
    application_id = config("APP_ID")

    # Establish WebSocket connection
    if websocket.enableTrace:
        websocket.enableTrace(True)

    socket.connect(server_url, header=['Sec-WebSocket-Protocol: ' + application_id])

    # Construct the MarketDataSubscribe request payload
    payload = {
        "action": "marketdatasubscribe",
        "data": {
            "subscribe": 1,
            "asset_id": 100,
            "period": 60
        },
        "token": access_token,
        "id": 1
    }

    # Convert the payload to JSON string
    request_json = json.dumps(payload)

    # Send the request using the socket
    socket.send(request_json)

    # Handle the server response
    response = socket.recv()
    server_response = json.loads(response)

    print(server_response)


#  this is used to get the token
code = get_authorization_code()
access_token = get_authorization_token(code)
# test connection
# test_access_token()

# get market subscribe
get_market_subscribe(access_token)
