#!/usr/bin/env python

#ALL NECESSARY IMPORTS
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from time import sleep
import time
import board
import busio
import digitalio
import threading
import sys
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import requests
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import subprocess

#SPOTIFY API CREDENTIALS
DEVICE_ID="98bb0735e28656bac098d927d410c3138a4b5bca"
CLIENT_ID="96d8df64da664f61b8e939c0b08b1a82"
CLIENT_SECRET="4644a83a28c14102888bb441db82c552"

#GLOBAL VARIABLES
global run
run = True
queueRun = True
global list
global isPlaying
isPlaying = False
global sp

#SONGS Dictionary with RFID Tag Keys and Spotify Song URI Values
global songs
songs = {
    817328348089 : '7g7ZSLwsRWWnkuQ2s3Iq8X',
    1092206255097 : '6ZoZ4KGIDD23DohdVk0Ybw',
    336141015878 : '4EWrXJlDRbYbfwA8bJeIow'
}

#FUNCTION THAT UPDATES THE SCREEN WITH THE CURRENT PLAYBACK INFORMATION
def updateScreen(shouldRestart):
    global run
    info = sp.currently_playing(market=None, additional_types=None)
    name = info['item']['name']
    new_name = name

    while(shouldRestart and name == new_name):
        info = sp.currently_playing(market=None, additional_types=None)
        new_name = info['item']['name']
        time.sleep(2)
        
    name = info['item']['name']
    artist = info['item']['artists'][0]['name']
    album = info['item']['album']['name']

    print(name)
    print(artist)
    print(album)

    x = threading.Thread(target=screen, args=(name,artist,album))
    run = True
    x.start()

#FUNCTION USED TO PAUSE OR PLAY THE SONG
def play():
    global isPlaying
    global sp
    isPlaying = not isPlaying

    if(isPlaying == True):
        sp.pause_playback(device_id=DEVICE_ID)
    else:
        sp.start_playback(device_id=DEVICE_ID)


#FUNCTION USED TO CLEAR THE OLED DISPLAY AT THE VERY END OF THE PROJECT
def clearOLED():
    # Display Parameters
    WIDTH = 128
    HEIGHT = 64
    BORDER = 5

    width = 128
    height = 64
    border = 5
    # Display Refresh
    LOOPTIME = 1.0

    i2c = board.I2C()
    oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=None)
    oled.fill(0)
    oled.show()

#FUNCTION USED TO SET UP OLED SCREEN, SET DISPLAY CONTENTS, AND SCROLL THE TEXT
def screen(name,artist,album):
    global run
    WIDTH = width = 128
    HEIGHT = height = 64
    BORDER = border = 5

    LOOPTIME = 1.0

    i2c = board.I2C()
    disp = oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=None)
    image = Image.new("1", (128, 64))

    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 128, 64), outline=255, fill=255)
    font = ImageFont.truetype('PixelOperator.ttf', 35)

    if(name == 'QUEUE'):
        text = 'QUEUE'
    elif(name == 'SETUP'):
        text = 'PLEASE SCAN A TAG TO GET STARTED'
    else:
        text = '*SONG: ' + name + '* *ARTIST: ' + artist + '* *ALBUM: ' + album + '* '
    maxwidth, unused = draw.textsize(text, font=font)

    velocity = -5
    startpos = width

    pos = startpos
    while run:
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        x = pos
        for i, c in enumerate(text):
            if x > width:
                break
            if x < -10:
                char_width, char_height = draw.textsize(c, font=font)
                x += char_width
                continue
            y = 0
            draw.text((x, y), c, font=font, fill=255)
            char_width, char_height = draw.textsize(c, font=font)
            x += char_width
        disp.image(image)
        disp.show()
        pos += velocity
        if pos < -maxwidth:
            pos = startpos
        time.sleep(0.1)
    oled.fill(0)
    oled.show()

#FUNCTION THAT RETURNS A BOOLEAN VALUE AS TO WHETHER OR NOT THE SCREEN SHOULD RESTART
def shouldRestart(id):
    screen = True
    global list
    if(len(list) == 0):
        list.append(id)
        return screen;

    list.append(id)
    if(list[-1] == list[-2]):
        screen = False
    return screen

# ACTUAL RFID READING AND FUNCTION CALLS
while True:
    try:
        global list
        list = []
        
        #SETUP THE READER AND SPOTIFY API
        global sp
        reader=SimpleMFRC522()
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                       client_secret=CLIENT_SECRET,
                                                       redirect_uri="http://localhost:8080",
                                                       scope="user-read-playback-state,user-modify-playback-state"))
        
        #SETS THE VOLUME TO A LOWER VALUE FOR THE PURPOSES OF OUR DEMONSTRATION SO THAT THE AUDIENCE CAN CLEARLY HEAR US
        sp.volume(75, device_id=DEVICE_ID)
        
        x = threading.Thread(target=screen, args=('SETUP','SETUP','SETUP'))
        run = True
        x.start()
        
        # create an infinite while loop that will always be waiting for a new scan
        while True:
            print("Waiting for record scan...")
            id= reader.read()[0]
            print("Card Value is:",id)

            # DONT include the quotation marks around the card's ID value, just paste the number
            if (id == 817328348089): #Wait 4 U
                currentTag= 817328348089
                z = shouldRestart(currentTag)

                sp.transfer_playback(device_id=DEVICE_ID, force_play=False)
                run = False
                sp.start_playback(device_id=DEVICE_ID, uris=['spotify:track:'+songs.get(currentTag)])

                updateScreen(z)


            elif (id == 336141015878): #Is there someone else
                currentTag= 336141015878
                z = shouldRestart(currentTag)

                sp.transfer_playback(device_id=DEVICE_ID, force_play=False)
                run = False
                sp.start_playback(device_id=DEVICE_ID, uris=['spotify:track:'+songs.get(currentTag)])

                updateScreen(z)

            elif (id== 1092206255097): #Wants and Needs
                currentTag= 1092206255097
                z = shouldRestart(currentTag)
                
                sp.transfer_playback(device_id=DEVICE_ID, force_play=False)
                run = False

                sp.start_playback(device_id=DEVICE_ID, uris=['spotify:track:'+songs.get(currentTag)])
                updateScreen(z)

            elif (id== 276607474989):
                sleep(1.5)
                queueRun = True
                print('entered queue')
                run = False
                sleep(2)
                x = threading.Thread(target=screen, args=('QUEUE','QUEUE','QUEUE'))
                run = True
                x.start()
                
                while queueRun:
                    sleep(1.5)
                    print("Waiting for queue scan...")
                    id = reader.read()[0]
                    print("Card Value is:",id)
                    sp.transfer_playback(device_id=DEVICE_ID, force_play=True)
                    if(id == 276607474989):
                        queueRun = False
                        run = False
                        sleep(2)
                        updateScreen(False)
                    elif(id == 817328348089):
                        sp.add_to_queue(songs.get(id), device_id=None)

                    elif(id == 1092206255097):
                        sp.add_to_queue(songs.get(id), device_id=None)

                    elif(id == 336141015878):
                        sp.add_to_queue(songs.get(id), device_id=None)
                print('exiting queue')

            elif (id == 284752812675):
                sp.transfer_playback(device_id=DEVICE_ID, force_play=False)
                run = False
                sp.next_track(device_id=None)

                updateScreen(True)

            elif (id == 770146997281):
                sp.transfer_playback(device_id=DEVICE_ID, force_play=True)
                run = False
                sp.previous_track(device_id=None)
                updateScreen(False)

            elif(id == 14183308342):
                sp.transfer_playback(device_id='e9317398260e02b5961ddb4b19d2ac091da8bd77', force_play=True)

            elif(id == 634410184642):
                #TWITTER POST
                BASE_URL = 'https://api.thingspeak.com/apps/thingtweet/1/statuses/update/'
                KEY = 'GQXIKXA2U65PVDCO'

                info = sp.currently_playing(market=None, additional_types=None)
                name = info['item']['name']
                artist = info['item']['artists'][0]['name']
                album = info['item']['album']['name']
                status = 'I am currently listening to ' + name + ' by ' + artist + '. This is fire.'
                data = {'api_key' : KEY, 'status' : status}
                response = requests.post(BASE_URL, json=data)
                print(response.status_code)

            elif(id == 485513569410):
                play()
                sleep(3)
    except Exception as e:
        print(e)
        pass

    finally:
        print("Cleaning  up...")
        run = False
        sp.pause_playback(device_id=DEVICE_ID)
        clearOLED()
        GPIO.cleanup()
