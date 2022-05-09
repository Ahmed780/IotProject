import RPi.GPIO as GPIO
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_daq as daq
from dash.dependencies import Input, Output
from paho.mqtt import client as mqtt_client
import paho.mqtt.subscribe as subscribe
import random
import smtplib
import time
from time import sleep
from datetime import datetime
import sqlite3

#Default Values of the user
username = 'Unknown'
rfid = 'User RFID'
desirePic = 'https://external-content.duckduckgo.com/iu/?u=http%3A%2F%2F4.bp.blogspot.com%2F-hmVjTOeadVQ%2FVoF_IiuCpFI%2FAAAAAAAAFo4%2FsdQMt9_U36U%2Fs400%2F063.gif&f=1&nofb=1'
desireTemperature = 29
desireHumidity = 40
desireLight = 1000

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#For LED
LED_PIN = 26

#For DC Motor
global ENABLE
ENABLE = 17
PIN_1 = 27
PIN_2 = 22

GPIO.setup(ENABLE, GPIO.OUT)
global pwm
pwm = GPIO.PWM(ENABLE, 50)


FROM = "bunny10bear@gmail.com"
PASSWORD = "Ineedjesus101"
TO = "bunny10bear@gmail.com"

def on_message(client, userdata, message):
    print("somehing")
    print("hello")
    time.sleep(500)
    return message.payload.decode("utf-8");

def readValue(desireLight,desireTemperature):
    
    global lightSrc
    global lightOn
    global fanSrc
    global fanToggle
    global fanOn
    global lightEmailSent

    #For sending and displaying values related to the light
    global lightNumber
    lightMessage = subscribe.simple("IoTLab/light", msg_count=1, retained=True)
    lightPayload = lightMessage.payload.decode("utf-8")
    lightNumber = float(lightPayload)
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PIN, GPIO.OUT)

    if lightNumber < desireLight:
        GPIO.output(LED_PIN, GPIO.HIGH)
        lightSrc = 'https://pluspng.com/img-png/light-bulb-png-file-light-bulb-yellow-icon-svg-image-820-1024.png'
        lightOn = "Light is ON -> Email was sent"

        if lightEmailSent == False:
            sendLightEmail()
            lightEmailSent = True
    else:
        GPIO.output(LED_PIN, GPIO.LOW)
        lightSrc = 'https://thearcofnova-wphost.netdna-ssl.com/content/uploads/sites/6/2017/04/light-bulb-idea-icon-light-bulb-11-icon.png'
        lightOn = 'Light is OFF'
        lightEmailSent = False


    #For sending and displaying values related to the temperature
    global temperatureNumber
    temperatureMessage = subscribe.simple("IoTLab/temperature",msg_count=1, retained=True)
    temperaturePayload = temperatureMessage.payload.decode("utf-8")
    temperatureNumber = float(temperaturePayload)
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ENABLE, GPIO.OUT)
    GPIO.setup(PIN_1, GPIO.OUT)
    GPIO.setup(PIN_2, GPIO.OUT)

    if temperatureNumber > desireTemperature:
        GPIO.output(PIN_1, 1)
        GPIO.output(PIN_2, 0)

        pwm.start(0)
        pwm.ChangeDutyCycle(50)

        GPIO.output(ENABLE, 1)
        GPIO.output(ENABLE, 0)
        
        response = "YES"
#         sendTemperatureEmail()
#         response = receiveResponse()
        
        if response == "YES":
            fanSrc = 'https://youraircomfort.com/wp-content/uploads/2017/07/fan-gif.gif'
            fanOn = "Fan is ON"
            fanToggle = True
        else:
            GPIO.output(PIN_1, 1)
            GPIO.output(PIN_2, 0)

            pwm.start(0)
            pwm.ChangeDutyCycle(0)

            GPIO.output(ENABLE, 1)
            GPIO.output(ENABLE, 0)
            
            fanSrc = 'https://cdn.onlinewebfonts.com/svg/img_537094.png'
            fanOn = "Fan is OFF"
            fanToggle = False      
    else:
        GPIO.output(PIN_1, 1)
        GPIO.output(PIN_2, 0)

        pwm.start(0)
        pwm.ChangeDutyCycle(0)

        GPIO.output(ENABLE, 1)
        GPIO.output(ENABLE, 0)
        
        fanSrc = 'https://cdn.onlinewebfonts.com/svg/img_537094.png'
        fanOn = "Fan is OFF"
        fanToggle = False

    global humidityNumber
    humidityMessage = subscribe.simple("IoTLab/humidity",msg_count=1, retained=True)
    humidityPayload = humidityMessage.payload.decode("utf-8")
    humidityNumber = float(humidityPayload)

    return lightNumber, temperatureNumber, humidityNumber, fanToggle, lightSrc, fanSrc, lightOn, fanOn

def readUser():
    global userNumber
    userMessage = subscribe.simple("IoTLab/rfid", msg_count=1, retained=True)
    userPayload = userMessage.payload.decode("utf-8")
    userNumber = str(userPayload)
 
    return userNumber

def sendLightEmail():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    TEXT = "Light is now ON \n\nAt: " + current_time + " time"

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(FROM, PASSWORD)

    msg = """From: %s\nTo: %s\nSubject: %s\n\n%s""" % (FROM, TO, "Light Status", TEXT)
    server.sendmail(FROM, TO, msg)
    server.quit()
    
def sendTemperatureEmail():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    TEXT = "YES or NO? \n\nAt: " + current_time + " time"

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(FROM, PASSWORD)

    msg = """From: %s\nTo: %s\nSubject: %s\n\n%s""" % (FROM, TO, "Turn On Fan?", TEXT)
    server.sendmail(FROM, TO, msg)
    server.quit()
    
def sendEmailRFID(user_id,username):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    TEXT = "User " + user_id + ": "+ username + " entered at: " + current_time + " time"

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(FROM, PASSWORD)

    msg = """From: %s\nTo: %s\nSubject: %s\n\n%s""" % (FROM, TO, "User Entered", TEXT)
    server.sendmail(FROM, TO, msg)
    server.quit()
    
def receiveResponse():
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(FROM, PASSWORD)
    
    mail.list()
    mail.select("Inbox")
    data = mail.uid('search', None, "SUBJECT","Response",'UNSEEN')
    if(len(data[1][0].decode('utf-8'))!=0):
        ids = data[1] #gives message
        stringlist=[x.decode('utf-8') for x in ids]#translates all UIDs to strings from bytes, at this step they are still 1 string in an array
        latest_uid = stringlist[0].split(' ')[-1]#now we have the message, its an array of response,content
        latest_mail = mail.uid('fetch', latest_uid, '(RFC822)')[1][0]
        latest_content = latest_mail[-1].decode().split("\r\n\r\n")[-1].strip()
        latest_content= upper(latest_content)
        if(latest_content=="YES"):
            return latest_content
        else:
            return "NO"

def makeDashboard():
    app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

    header_height, footer_height = "6rem", "10rem"
    sidebar_width, adbar_width = "12rem", "12rem"

    HEADER_STYLE = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "right": 0,
        "height": header_height,
        "padding": "2rem 1rem",
        "background-color": "#111111",
        "color": "#7FDBFF",
        "textAlign": "center"
    }

    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": header_height,
        "left": 0,
        "bottom": 0,
        "width": sidebar_width,
        "padding": "1rem 1rem",
        "background-color": "#111111",
        "color": "#7FDBFF"
    }

    ADBAR_STYLE = {
        "position": "fixed",
        "top": header_height,
        "right": 0,
        "bottom": 0,
        "width": adbar_width,
        "padding": "1rem 1rem",
        "background-color": "#111111",
        "color": "#7FDBFF",
    }

    CONTENT_STYLE = {
        "margin-top": header_height,
        "margin-left": sidebar_width,
        "margin-right": adbar_width,
        "margin-bottom": 0,
        "padding": "1rem 1rem",
        "background-color": "#303030",
    }

    theme = {
        'dark': True,
        'detail': '#007439',
        'primary': '#00EA64',
        'secondary': '#6E6E6E',
    }

    header = html.Div([
        html.H1("Welcome to  your Dashboard")], style=HEADER_STYLE
    )

    adbar = html.Div([
        html.H2("Made by"),
        html.P('Maria Ramlochan'),
        html.P('Updated: 02/05/2022'),
        ], style=ADBAR_STYLE
    )

    sidebar = html.Center([html.Div(children=[
            html.Img(id='my-pic', src= desirePic, style={'width': '100px', 'heigth': '100px', 'border-radius': '50px'}),
            html.H2(id='my-username', children=[username]),
            html.Hr(),
            html.P(id='my-rfid', children=[rfid]),
            html.Br(),
            html.Hr(),
            dbc.Nav([
                    dbc.NavLink("Home", href="/page-1", id="page-1-link"),
    #                 dbc.NavLink("Settings", href="/page-2", id="page-2-link"),
    #                 dbc.NavLink("Page 3", href="/page-3", id="page-3-link"),
                ], vertical=True, pills=True,
            ),
            html.Hr(),
            daq.LEDDisplay(
                id='my-light-desire',
                label='Desired Light',
                value= desireLight,
                color="#FFD700",
            ),
            html.Hr(),        
            daq.LEDDisplay(
                id='my-temp-desire',
                label='Desired Temperature',
                value= desireTemperature,
                color="#00FA9A",
            ),
            html.Hr(),
            daq.LEDDisplay(
                id='my-humid-desire',
                label='Desired Humidity',
                value= desireHumidity,
                color="#DC143C",
            ),
        ])
    ])
    

    cdivs = [html.Div(id="page-content", children=[
                html.Div(children=[
                    daq.DarkThemeProvider(theme=theme),
                        
                    html.Div([
                        html.H3("Humidity"),
                        ], style={'width': '50%','display':'inline-block', 'color': '#7FDBFF', 'text-align': 'center'}
                    ),
                        
                    html.Div([
                        html.H3("Temperature"),
                        ], style={'width': '50%','display':'inline-block', 'color': '#7FDBFF', 'text-align': 'center'}
                    ),
                        
                    daq.Gauge(
                        style={'width': '50%','display':'inline-block', 'float': 'left', 'margin-top': '5%'},
                        id='my-gauge-1',
                        color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
                        value=0,
                        label=' ',
                        max=100,
                        min=0,
                        units="%",
                        className='dark-theme-control',
                        showCurrentValue=True,
                    ),
                    daq.Thermometer(
                        style={'width': '50%','display':'inline-block', 'margin-top': '2%'},
                        id='my-thermometer-1',
                        color=theme['primary'],
                        className='dark-theme-control',
                        value=0,
                        min=0,
                        max=50,
                        units="Celsius",
                        showCurrentValue=True,
                    ),
                ], style={
                    'border': 'solid 1px #666666',
                    'border-radius': '5px',
                    'padding': '10px',
                    'margin-top': '29px',
                    'background-color':'#262626'
                }),
                    
                html.Div(children=[
                        daq.DarkThemeProvider(theme=theme),
                        
                    html.Div([
                            html.H3("Light"),
                            ], style={'width': '50%','display':'inline-block', 'color': '#7FDBFF', 'text-align': 'center'}
                        ),
                        
                        html.Div([
                            html.H3("Fan"),
                            ], style={'width': '50%','display':'inline-block', 'color': '#7FDBFF', 'text-align': 'center'}
                        ),
                        
                    html.Div(style={'width': '50%','display':'inline-block', 'margin-left': '18%'}, children=[
                        html.Img(id='my-lightBulb',
                            src='https://thearcofnova-wphost.netdna-ssl.com/content/uploads/sites/6/2017/04/light-bulb-idea-icon-light-bulb-11-icon.png',
                            style={'width': '200px', 'heigth': '200px'},
                        ),
                    ]),

                    html.Div(style={'display':'inline-block'}, children=[
                        html.Img(id='my-fan',
                            src='https://cdn.onlinewebfonts.com/svg/img_537094.png',
                            style={'width': '200px', 'heigth': '200px'},
                        ),
                    ]),

                    daq.LEDDisplay(
                        style={'width': '50%','display':'inline-block', 'color': 'white'},
                        id='my-light',
                        label="Light is OFF",
                        labelPosition='bottom',
                        value= 0,
                        color="#7FDBFF",
                    ),

                    daq.PowerButton(
                        style={'width': '50%','display':'inline-block', 'color': 'white'},
                        label='Fan is OFF',
                        labelPosition='bottom',
                        disabled=True,
                        on=False,
                        color=theme['primary'],
                        id='my-power-button',
                        className='dark-theme-control'
                    ),

                    ], style={
                        'border': 'solid 1px #666666',
                        'border-radius': '5px',
                        'padding': '10px',
                        'margin-top': '20px',
                        'background-color':'#262626'
                    }),

                 ],
            ),
        ]

    content = html.Div(children=[daq.DarkThemeProvider(theme=theme, children=cdivs)], style=CONTENT_STYLE)
    sidebarContent = html.Div(children=[daq.DarkThemeProvider(theme=theme, children=sidebar)], style=SIDEBAR_STYLE)

    app.layout = html.Div([dcc.Location(id="url"), header, sidebarContent, adbar, content,dcc.Interval(id="interval-component",interval=1*2000,n_intervals=0)])


    # this callback uses the current pathname to set the active state of the
    # corresponding nav link to true, allowing users to tell see page they are on
    @app.callback(
        [Output(f"page-{i}-link", "active") for i in range(1, 2)],
        [Input("url", "pathname")],
    )

    def toggle_active_links(pathname):
        if pathname == "/":
            # Treat page 1 as the homepage / index
            return True, False, False
        return [pathname == f"/page-{i}" for i in range(1, 2)]


    @app.callback(Output("page-content", "children"),
                  [Input("url", "pathname")])
    
    def render_page_content(pathname):
        if pathname in ["/", "/page-1"]:
            return cdivs
#         elif pathname == "/page-2":
#             return cdivs2
#         elif pathname == "/page-3":
#             return html.P("Oh cool, this is page 3!")
        # If the user tries to reach a different page, return a 404 message
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )

    @app.callback(Output('my-light', 'value'),
                  Output('my-thermometer-1', 'value'),
                  Output('my-gauge-1', 'value'),
                  Output('my-power-button', 'on'),
                  Output('my-lightBulb', 'src'),
                  Output('my-fan', 'src'),
                  Output('my-light', 'label'),
                  Output('my-power-button', 'label'),
                  Output('my-username', 'children'),
                  Output('my-rfid', 'children'),
                  Output('my-pic', 'src'),
                  Output('my-light-desire', 'value'),
                  Output('my-temp-desire', 'value'),
                  Output('my-humid-desire', 'value'),
                  [Input('interval-component', 'n_intervals')])
    def update_output(n):
        
        infoUser = readUser()
            
        dbconnect = sqlite3.connect("iotproject.db")
        dbconnect.row_factory = sqlite3.Row;
        cursor = dbconnect.cursor();
        select_stmt = "SELECT * FROM user WHERE user_rfid = user_rfid"
        cursor.execute(select_stmt, { 'user_rfid': infoUser })

        for row in cursor:
            
            if infoUser == row['user_rfid']:
                rfid = row['user_rfid']
                username = row['username']
                desirePic = row['user_pic']
                desireTemperature = row['user_temp']
                desireHumidity = row['user_humid']
                desireLight = row['user_light']
                
                info = readValue(desireLight, desireTemperature)
#                 sendEmailRFID(rfid,username)
                    
                dbconnect.close()
                print (info[0],info[1],info[2],info[3],info[4],info[5],info[6],info[7],username,rfid,desirePic,desireLight,desireTemperature,desireHumidity)
                return info[0],info[1],info[2],info[3],info[4],info[5],info[6],info[7],username,rfid,desirePic,desireLight,desireTemperature,desireHumidity           
            

        username = 'Unknown'
        rfid = 'User RFID'
        desirePic = 'https://external-content.duckduckgo.com/iu/?u=http%3A%2F%2F4.bp.blogspot.com%2F-hmVjTOeadVQ%2FVoF_IiuCpFI%2FAAAAAAAAFo4%2FsdQMt9_U36U%2Fs400%2F063.gif&f=1&nofb=1'
        desireTemperature = 29
        desireHumidity = 40
        desireLight = 1000
        
        userRFIDSent = False
        info = readValue(desireLight, desireTemperature)
        dbconnect.close()
        print (info[0],info[1],info[2],info[3],info[4],info[5],info[6],info[7],username,rfid,desirePic,desireLight,desireTemperature,desireHumidity)
        return info[0],info[1],info[2],info[3],info[4],info[5],info[6],info[7],username,rfid,desirePic,desireLight,desireTemperature,desireHumidity
        
    if __name__ == "__main__":
         app.run_server(debug=True)
         
makeDashboard()