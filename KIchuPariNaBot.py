from __future__ import print_function

import re
import random

from six.moves import input



import azure.cognitiveservices.speech as speechsdk
import cv2
import requests
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import os
import json
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import requests



#implementing speech to text input
#Step: take input from user through speech
def speech_to_text():
    speech_config = speechsdk.SpeechConfig(subscription="6f24f130fc824d7bab3de9e16526903e", region="westus")

    # Creates a recognizer with the given settings
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    print("Say something...")

    # Performs recognition. recognize_once() returns when the first utterance has been recognized,
    # so it is suitable only for single shot recognition like command or query. For long-running
    # recognition, use start_continuous_recognition() instead, or if you want to run recognition in a
    # non-blocking manner, use recognize_once_async().
    result = speech_recognizer.recognize_once()

    # Checks result.
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(result.text))
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(result.no_match_details))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

    return result.text


#Step 2: if user says play a song the webcam will take a photo
#implementing taking a photo through webcam

def takePhoto():
    cam = cv2.VideoCapture(0)

    cv2.namedWindow("test")

    img_counter = 0

    while True:
        ret, frame = cam.read()
        cv2.imshow("test", frame)
        if not ret:
            break
        k = cv2.waitKey(1)

        if k % 256 == 32:
            print("Press Space to capture Image")
            # SPACE pressed
            img_name = "{}.png".format(img_counter)
            cv2.imwrite(img_name, frame)
            #print("{} written!".format(img_name))
            img_counter += 1
            break

    cam.release()

    cv2.destroyAllWindows()
    return img_name



#Step 3: Detect user emtion from picture
#implementing emotion detector

def emotionDetection(img="4.jpg"):
    subscription_key = "6b75ed8455c34b7fb33b86bbe30edb19"  # DSFace API

    # Set image path from local file.
    image_path = os.path.join(img)

    assert subscription_key

    face_api_url = 'https://westus.api.cognitive.microsoft.com/face/v1.0/detect'

    image_data = open(image_path, "rb")

    headers = {'Content-Type': 'application/octet-stream',
               'Ocp-Apim-Subscription-Key': subscription_key}
    params = {
        'returnFaceAttributes': 'emotion',
    }

    response = requests.post(face_api_url, params=params, headers=headers, data=image_data)
    response.raise_for_status()
    analysis = response.json()
    # print(json.dumps(response.json()))
    # print(analysis)
    emotions = dict()

    emotions[analysis[0]["faceAttributes"]['emotion']['happiness']] = "happy"
    emotions[analysis[0]["faceAttributes"]['emotion']['neutral']] = "sad"
    emotions[analysis[0]["faceAttributes"]['emotion']['sadness']] = "sad"
    emotions[analysis[0]["faceAttributes"]['emotion']['anger']] = "angry"

    max_idx = max(emotions.keys())
    image_caption = emotions[max_idx]

    # Display the original image and overlay it with the face information.
    image_read = open(image_path, "rb").read()
    image = Image.open(BytesIO(image_read))

    print("User emotion is:"+image_caption)
    # plt.figure(figsize=(8, 8))
    # ax = plt.imshow(image, alpha=1)
    # _ = plt.title(image_caption, size="x-large", y=-0.1)
    # _ = plt.axis("off")
    # plt.show()
    if image_caption=="angry":
        return "Rock"
    return image_caption


#Step 4: Recommend youtube songs based on detected emotion
#Implementing Youtube Data API to find music videos
def search_videos(keyword):
    print("Searching for music")
    youtube = build('youtube','v3',developerKey='AIzaSyB9WDG0cjfffK-WZZE5TGimuh6L8P1leHY')

    response = youtube.search().list(q=keyword + "official music video",
                                     part="id,snippet",
                                     maxResults=10
                                     ).execute().get("items", [])

    videos = []

    i = 0
    for record in response:
        if record["id"]["kind"] == "youtube#video":
            title = record["snippet"]["title"]
            videos.append(title)
            print(videos[i])
            i+=1
            if i==5:
                break

    return videos


#implementing web crawler to find lyrics of song
def webCrawler(song):
    url = "https://www.lyrics.com/lyrics/" + song
    r = requests.get(url)
    print("Searching for "+song)
    data = r.text
    soup = BeautifulSoup(data, features="lxml")

    print("Crawling lyrics.....")
    print('\n')
    for link in soup.find_all('a'):
        new_url = link.get('href')
        if (new_url[:6] == "/lyric"):
            # print(new_url)
            break

    new_url = "https://www.lyrics.com" + new_url

    r = requests.get(new_url)
    data = r.text
    soup = BeautifulSoup(data, features="lxml")

    datal = soup.find("pre", {"id": "lyric-body-text"}).text
    print(datal)






reflections = {
  "i am"       : "you are",
  "i was"      : "you were",
  "i"          : "you",
  "i'm"        : "you are",
  "i'd"        : "you would",
  "i've"       : "you have",
  "i'll"       : "you will",
  "my"         : "your",
  "you are"    : "I am",
  "you were"   : "I was",
  "you've"     : "I have",
  "you'll"     : "I will",
  "your"       : "my",
  "yours"      : "mine",
  "you"        : "me",
  "me"         : "you"
}

from nltk.chat.util import reflections

class Chat(object):
    def __init__(self, pairs, reflections={}):
        """
        Initialize the chatbot.  Pairs is a list of patterns and responses.  Each
        pattern is a regular expression matching the user's statement or question,
        e.g. r'I like (.*)'.  For each such pattern a list of possible responses
        is given, e.g. ['Why do you like %1', 'Did you ever dislike %1'].  Material
        which is matched by parenthesized sections of the patterns (e.g. .*) is mapped to
        the numbered positions in the responses, e.g. %1.

        :type pairs: list of tuple
        :param pairs: The patterns and responses
        :type reflections: dict
        :param reflections: A mapping between first and second person expressions
        :rtype: None
        """

        self._pairs = [(re.compile(x, re.IGNORECASE), y) for (x, y) in pairs]
        self._reflections = reflections
        self._regex = self._compile_reflections()

    def _compile_reflections(self):
        sorted_refl = sorted(self._reflections.keys(), key=len, reverse=True)
        return re.compile(
            r"\b({0})\b".format("|".join(map(re.escape, sorted_refl))), re.IGNORECASE
        )

    def _substitute(self, str):
        """
        Substitute words in the string, according to the specified reflections,
        e.g. "I'm" -> "you are"

        :type str: str
        :param str: The string to be mapped
        :rtype: str
        """

        return self._regex.sub(
            lambda mo: self._reflections[mo.string[mo.start() : mo.end()]], str.lower()
        )

    def _wildcards(self, response, match):
        pos = response.find('%')
        while pos >= 0:
            num = int(response[pos + 1 : pos + 2])
            response = (
                response[:pos]
                + self._substitute(match.group(num))
                + response[pos + 2 :]
            )
            pos = response.find('%')
        return response


    def respond(self, str):
        """
        Generate a response to the user input.

        :type str: str
        :param str: The string to be mapped
        :rtype: str
        """

        # check each pattern
        if (str == "play a song" or str == "play a song."):
            img_name = takePhoto()
            emotion = emotionDetection(img_name)
            search_videos(emotion)
        if (str[:7]=="lyrics "):
            webCrawler(str[7:])



        if(str=="listen"):
            print("If you want to play a song say \"Play a song\"")
            print("If you want lyrics of a song say \"Lyrics\" and then the song name")
            str = speech_to_text()
            if(str=="Play a song."):
                img_name = takePhoto()
                emotion = emotionDetection(img_name)
                search_videos(emotion)
            if (str[:7] == "Lyrics "):
                webCrawler(str[7:])

        for (pattern, response) in self._pairs:
            match = pattern.match(str)


            # did the pattern match?
            if match:
                resp = random.choice(response)  # pick a random response
                resp = self._wildcards(resp, match)  # process wildcards

                # fix munged punctuation at the end
                if resp[-2:] == '?.':
                    resp = resp[:-2] + '.'
                if resp[-2:] == '??':
                    resp = resp[:-2] + '?'
                return resp


    # Hold a conversation with a chatbot
    def converse(self, quit="quit"):
        user_input = ""
        while user_input != quit:
            user_input = quit
            try:
                user_input = input(">")
            except EOFError:
                print(user_input)
            if user_input:
                while user_input[-1] in "!.":
                    user_input = user_input[:-1]
                print(self.respond(user_input))

pairs = [
  [
    r"my name is (.*)",
    ["Hello %1, How are you today ?", ]
  ],
  [
    r"what is your name ?",
    ["My name is Chatty and I'm a chatbot ?", ]
  ],
  [
    r"how are you ?",
    ["I'm doing good\nHow about You ?", ]
  ],
  [
    r"sorry (.*)",
    ["Its alright", "Its OK, never mind", ]
  ],
  [
    r"i'm (.*) doing good",
    ["Nice to hear that", "Alright :)", ]
  ],
  [
    r"hi|hey|hello",
    ["Hello", "Hey there", ]
  ],
  [
    r"(.*) age?",
    ["I'm a computer program dude\nSeriously you are asking me this?", ]

  ],
  [
    r"what (.*) want ?",
    ["Make me an offer I can't refuse", ]

  ],
  [
    r"(.*) created ?",
    ["Nagesh created me using Python's NLTK library ", "top secret ;)", ]
  ],
  [
    r"(.*) (location|city) ?",
    ['Chennai, Tamil Nadu', ]
  ],
  [
    r"how is weather in (.*)?",
    ["Weather in %1 is awesome like always", "Too hot man here in %1", "Too cold man here in %1",
     "Never even heard about %1"]
  ],
  [
    r"i work in (.*)?",
    ["%1 is an Amazing company, I have heard about it. But they are in huge loss these days.", ]
  ],

  [
    r"(.*)raining in (.*)",
    ["No rain since last week here in %2", "Damn its raining too much here in %2"]
  ],
  [
    r"how (.*) health(.*)",
    ["I'm a computer program, so I'm always healthy ", ]
  ],
  [
    r"(.*) (sports|game) ?",
    ["I'm a very big fan of Football", ]
  ],
  [
    r"who (.*) sportsperson ?",
    ["Messy", "Ronaldo", "Roony"]

  ],
  [
    r"who (.*) (moviestar|actor)?",
    ["Brad Pitt"]

  ],
  [
    r"quit",
    ["BBye take care. See you soon :) ", "It was nice talking to you. See you soon :)"]

  ],
  [
    r"play a song",
    ["Done"]
  ],

    [
    r"Lyrics (.*)?",
    ["Done.", ]
  ],
]


def chatty():
  print(
    "Hi, I'm KichuPariNa_Bot and I chat a lot ;)\nPlease type English language to start a conversation.\n"
    "Type listen to say something. \nType play a song for song recommendations. \n"
    "Type lyrics and then the name of a song to get the lyrics.\n"
    "Type quit to leave ")  # default message at the start

chatty()
chat = Chat(pairs, reflections)
chat.converse()
