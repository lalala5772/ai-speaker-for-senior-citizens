from __future__ import print_function
from urllib.request import urlopen, Request
import urllib
import bs4
from bs4 import BeautifulSoup as bs
import requests
import re
import ex1_kwstest as kws
import ex2_getVoice2Text as gv2t
import ex4_getText2VoiceStream as tts
import ex5_queryText as qt
import ex6_queryVoice as dss
import Adafruit_DHT as dht
import time
import random
import MicrophoneStream as MS
from datetime import datetime
import threading
import RPi.GPIO as GPIO
import argparse, pafy, ffmpeg, pyaudio

from googleapiclient.discovery import build 
from googleapiclient.errors import HttpError

##=====================================================================

url1 = requests.get('https://search.naver.com/search.naver?query= 날씨')
soup1 = bs(url1.text,'html.parser')
#지역
location=soup1.find('div',class_='select_box').find('span',class_='btn_select').text

humidity_loc=urllib.parse.quote(location+ ' 습도')
url2=requests.get('https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query='+humidity_loc)
soup2=bs(url2.text,'html.parser')
data1=soup1.find('div',class_='detail_box')
data2 = data1.findAll('dd')

##===============================================================
DEVELOPER_KEY = 'AIzaSyBdKmCZbg1aV1LDuwBYJtWEfG5G3MZUFA8'
YOUTUBE_API_SERVICE_NAME = 'youtube' 
YOUTUBE_API_VERSION = 'v3'

GPIO.cleanup()
GPIO.setmode(GPIO.BOARD) 
GPIO.setwarnings(False) 
GPIO.setup(29, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(31, GPIO.OUT)
btn_status = False

play_flag =0
num1=0
num2=0
start=0
##===============================================================
def callback(channel):    
    print("falling edge detected from pin {}".format(channel))
    global btn_status  
    btn_status = True  
    print(btn_status)  
    global play_flag
    global num1, num2
    
    
    #play_flag==0(youtube playing), 노래를 중단하고 대기상태
    if play_flag==0 and num1>0 and num2==0:
        play_flag=2
        
    elif play_flag==0 and num2>0 and num1==0:
        play_flag=3
        
    elif play_flag==0 and num1==0 and num2==0:
        play_flag=1
    
    elif play_flag==2:
        play_flag=3
        num1=0
        num2=0
    
    elif play_flag==3:
        play_flag=1
        num1=0
        num2=0
        
        

GPIO.add_event_detect(29, GPIO.FALLING, callback=callback, bouncetime=10)

def youtube_search(options):  
    #try:    
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
        parser = argparse.ArgumentParser()    
        parser.add_argument('--q', help='Search term', default=options)    
        parser.add_argument('--max-results', help='Max results', default=25)    
        args = parser.parse_args()
    
        search_response = youtube.search().list(      
            q=args.q,      
            part='id,snippet',      
            maxResults=args.max_results    
        ).execute()
    
        videos = []    
        url = []
    
        for search_result in search_response.get('items', []):      
            if search_result['id']['kind'] == 'youtube#video':        
                videos.append('%s (%s)' % (search_result['snippet']['title'],search_result['id']['videoId']))        
                url.append(search_result['id']['videoId'])
            
        resultURL = "https://www.youtube.com/watch?v=" + url[0]    
        return resultURL

    #except :    
        print("Youtube Error")

        
def play_with_url(play_url):
    #print("print url!!:")
    print(play_url)  
    video = pafy.new(play_url)  
    best = video.getbestaudio()  
    playurl = best.url  
    global play_flag, num1, num2
    play_flag = 0
    
    
    pya = pyaudio.PyAudio()  
    stream = pya.open(format=pya.get_format_from_width(width=2), channels=1, rate=16000,                    
                      output=True)
    try:      
        process = (ffmpeg          
                   .input(playurl, err_detect='ignore_err', reconnect=1, reconnect_streamed=1,                 
                          reconnect_delay_max=5)          
                   .output('pipe:', format='wav', audio_bitrate=16000, ab=64, ac=1, ar='16k')          
                   .overwrite_output()          
                   .run_async(pipe_stdout=True)      
        )
        
        while True:        
            if play_flag == 0 :          
                in_bytes = process.stdout.read(4096)          
                if not in_bytes:              
                    break          
                stream.write(in_bytes)        
            else:          
                break  
    finally:      
        stream.stop_stream()      
        stream.close()

##===============================================================
def nowdate():
    now = datetime.now()
    nowdate = str(now.month).zfill(2) + str(now.day).zfill(2)
    nowdate = int(nowdate)
    return nowdate
def nowtime():
    now = datetime.now()
    nowtime = str(now.hour).zfill(2) + str(now.minute).zfill(2)
    nowtime = int(nowtime)
    return nowtime

#온도
def temp():
    temp=soup1.find('p', class_='info_temperature').find('span', class_='todaytemp').text
    return temp

#습도
def hum():
    humidity_withpersent=soup2.find('div',class_='info_list humidity _tabContent').find('dd',class_='weather_item _dotWrapper').text
    hum=int(re.findall('\d+',humidity_withpersent)[0])
    return hum

#미세먼지
def fine_dust():
    fine_dust=data2[0].find('span',class_='num').text
    return fine_dust

#초미세먼지
def ultra_fine_dust():
    ultra_fine_dust = data2[1].find('span',class_='num').text
    return ultra_fine_dust

#미세먼지를 수치로
def fd_level():
    fine_dust_num=int(re.findall('\d+',fine_dust())[0])
    if (fine_dust_num<=30):
        return("좋음")
    elif(fine_dust_num>=31)and(fine_dust_num<=80):
        return("보통")
    elif(fine_dust_num>=81)and(fine_dust_num<=150):
        return("나쁨")
    else:
        return("매우 나쁨")
    
#초미세먼지를 수치로
def ufd_level():
    ultra_fine_dust_num=int(re.findall('\d+',ultra_fine_dust())[0])
    if (ultra_fine_dust_num<=15):
        return("좋음")
    elif(ultra_fine_dust_num>=16)and(ultra_fine_dust_num<=50):
        return("보통")
    elif(ultra_fine_dust_num>=51)and(ultra_fine_dust_num<=100):
        return("나쁨")
    else:
        return("매우 나쁨")
    
##===============================================================
down_t = ["창문을 열어 환기를 시켜주세요",
          "선풍기를 집 밖을 향해서 틀어주세요",
          "커튼을 쳐주세요",
          "물을 마셔주세요",
          "따뜻한 물로 샤워해주세요"]  # 3 

down_h = ["창문을 열어 환기를 시켜주세요",
          "제습기를 틀어주세요",
          "환풍기를 틀어주세요",
          "물을 마셔주세요"] # 3

down_t_dust = ["선풍기를 집 밖을 향해서 틀어주세요",
               "커튼을 쳐주세요",
               "물을 마셔주세요",
               "따뜻한 물로 샤워해주세요"] # 2


down_h_dust = ["제습기를 틀어주세요",
              "환풍기를 틀어주세요",
              "물을 마셔주세요"]   # 2

up_t = ["난방을 틀어주세요.",
        "따뜻한 물로 샤워해주세요.",
        "따뜻한 물을 마셔주세요.",
        "내복을 입어주세요.",
        "양말을 신어주세요.",  
        "목에 손수건을 둘러주세요." ]   # 1

up_h = ["가습기를 틀어주세요",
        "빨래나 물에 젖은 손수건을 널어주세요",
        "목에 손수건이 스카프를 둘러주세요",
        "물을 마셔주세요" ]   # 1

##==========================================================
def season_select():
    season = ""
    date = nowdate()

    if 622 <= date < 823:
        season = "여름"
    elif 1122 <= date <= 1231 or date < 306:
        season = "겨울"
    else:
        season = "그외"
    
    return season

##==========================================================

def giveSolution():
    today_t= float(temp())
    today_h = float(hum())
    fine_dust2 = int(re.findall('\d+',fine_dust())[0])
    humidity, temperature = dht.read_retry(dht.DHT22, 4)
    h= humidity
    t= temperature
    ans = ""
    season = season_select()
    
    #12345
    global play_flag
    global num1, num2, start
    ###
    if play_flag==0:
        play_flag=1
        
        dt = random.randrange(0,3)
        dh = random.randrange(0,3)
        dtd = random.randrange(0,2)
        dhd = random.randrange(0,2)
        ut = random.randrange(0,1)
        uh = random.randrange(0,1)
        
    elif play_flag==1:
        play_flag=2   
        dt = random.randrange(0,3)
        dh = random.randrange(0,3)
        dtd = random.randrange(0,2)
        dhd = random.randrange(0,2)
        ut = random.randrange(0,1)
        uh = random.randrange(0,1)
    
    if play_flag==2 and num1<5:
        num1+=1
        num2=0
        dt = random.randrange(0,3)
        dh = random.randrange(0,3)
        dtd = random.randrange(0,2)
        dhd = random.randrange(0,2)
        ut = random.randrange(0,1)
        uh = random.randrange(0,1)
        
        
    elif play_flag==3 and num2<5:
        num1=0
        num2+=1
        dt = random.randrange(3,5)
        dh = random.randrange(3,4)
        dtd = random.randrange(2,4)
        dhd = random.randrange(2,3)
        ut = random.randrange(1,5)
        uh = random.randrange(1,4)
        

    elif play_flag==2 and num1==5:
        num1=0
        num2=0
        play_flag=1
        
    elif play_flag==3 and num2==5:
        num1=0
        num2=0
        play_flag=1
    
    if season == '여름':
        if today_t - t >= 8:
            print("현재 밖과의 온도차가 매우 큽니다.")
            print("에어컨이나 선풍기의 전원을 꺼주세요.")
            ans = "현재 밖과의 온도차가 매우 큽니다. 에어컨이나 선풍기의 전원을 꺼주세요."
        else:
            if t >= 30 and h >= 65:
                print("현재 온도는 높고 습도도 높습니다.")

                if fine_dust2 >= 75 or today_h > h :
                    ans = down_t_dust[dtd] + '그리고' + down_h_dust[dhd]
                else:
                    ans = down_t[dt] + '그리고' + down_h[dh]

            elif t >= 30 and h <= 35:
                print("현재 온도는 높고 습도는 낮습니다.")
                ans = down_t[dt] + '그리고' + up_h[uh]
                
            elif t >= 30 and 35 < h < 65:
                print("현재 온도가 높습니다. ")
                ans = down_t[dt]
                 
            elif t < 30 and h >= 65:
                print("현재 습도가 높습니다. ")
                if fine_dust2 >= 75 or today_h > h :
                    ans = down_h_dust[dhd]
                else:
                    ans = down_h[dh]

            elif t < 30 and h <= 35:
                print("현재 습도가 낮습니다. ")
                ans = up_h[uh]
                
            else:
                print("현재 온도와 습도가 모두 쾌적한 상태입니다, ")
                ans = "현재 온도와 습도가 모두 쾌적한 상태입니다"

    elif season == '겨울':
        if t <= 22 and h >= 65:
            print("현재 온도는 낮고 습도는 높습니다.")
            if fine_dust2 >= 75 or today_h > h :
                ans = up_t[ut] + '그리고' + down_h_dust[dhd]
            else:
                ans = up_t[ut] + '그리고' + down_h[dh]

        elif t <= 22 and h <= 35:
            print("현재 온도는 낮고 습도도 낮습니다.")
            ans = up_t[ut] + '그리고' + up_h[uh]

        elif t <= 22 and 35<h<65:
            print("현재 온도가 낮습니다.")
            ans = up_t[ut]

        elif t > 22 and h >= 65:
            print("현재 습도가 높습니다.")
            if fine_dust2 >= 75 or today_h > h :
                ans = down_h_dust[dhd]
            else:
                ans = down_h[dh]

        elif t > 22 and h <= 35:
            print("현재 습도가 낮습니다. ")
            ans = up_h[uh]

        else:
            print("온도와 습도가 모두 쾌적한 상태입니다.")
            ans = "현재 온도와 습도가 모두 쾌적한 상태입니다"

    else:
        if today_t - t >= 8:
            print("현재 밖과의 온도 차이가 매우 큽니다.")
            print("에어컨이나 선풍기의 전원을 꺼주세요.")
            ans = "현재 밖과의 온도 차이가 매우 큽니다. 에어컨이나 선풍기의 전원을 꺼주세요."

        else:
            if 29 <= t and h >= 65:
                print("현재 온도가 높고 습도도 높습니다. ")
                if fine_dust2 >= 75 or today_h > h :
                    ans = down_t_dust[dtd] + '그리고' + down_h_dust[dhd]
                else:
                    ans = down_t[dt] + '그리고' + down_h[dh]

            elif 29 <= t and h <= 35:
                print("현재 온도가 높고 습도는 낮습니다.")
                ans = down_t[dt] + '그리고' + up_h[uh]

            elif 22 >= t and h >= 65:
                print("현재 온도는 낮고 습도는 높습니다.")
                if fine_dust2 >= 75 or today_h > h :
                    ans = up_t[ut] + '그리고' + down_h_dust[dhd]
                else:
                    ans = up_t[ut] + '그리고' + down_h[dh]

            elif 22 >= t and h <= 35:
                print("현재 온도는 낮고 습도도 낮습니다.")
                ans = up_t[ut] + '그리고' + up_h[uh]

            elif 29 <= t and 35 < h < 65 :
                print("현재 온도가 높습니다.")
                ans = down_t[dt]

            elif 22 >= t and 35 < h < 65 :
                print("현재 온도가 낮습니다.")
                ans = up_t[ut]

            elif 22 < t < 29 and h >= 65 :
                print("현재 습도가 높습니다.")
                if fine_dust2 >= 75 or today_h > h :
                    ans = down_h_dust[dhd]
                else:
                    ans = down_h[dh]

            elif 22 < t < 29 and h <= 35 :
                print("현재 습도가 낮습니다.")
                ans = up_h[uh]

            else:
                print("현재 온도와 습도가 모두 쾌적한 상태입니다,")
                ans = "현재 온도와 습도가 모두 쾌적한 상태입니다"
                
    return ans


##===============================================================
def gs_call():
    global Time
    Time = 1200
    
    global num1, num2,play_flag, start
    
    if num1 == 0 or num1==1 or num2==0 or num2==1:
        Time = 1200
    elif num1==2 or num2==2:
        Time = 800
    elif num1==3 or num2==3:
        Time = 600
    elif num1==4 or num2==4:
        Time = 400
    
    if start==0:
        print('start function started')
        tts.getText2VoiceStream(giveSolution(), "result_TTS.wav")
        MS.play_file("result_TTS.wav")
        start=1
        threading.Timer(Time, gs_call).start()
    
   #12345     
    if play_flag!=0 and start!=0 and start!=1:

        print('flag function started')
        tts.getText2VoiceStream(giveSolution(), "result_TTS.wav")
        MS.play_file("result_TTS.wav")
    
        threading.Timer(Time, gs_call).start()
    
    if play_flag==1 and start==1:
        start=2

##===============================================================
def checkCommand(result):
    humidity, temperature = dht.read_retry(dht.DHT22, 4)
    
    text = result
    ###
    if (text.find("온도 알려줘") >= 0)or(text.find("지금 몇도야")>=0):
        print("현재 실내 온도는 {0:0.1f} 도 입니다 ".format(temperature))
        return("현재 실내 온도는 {0:0.1f} 도 입니다ㅏ, ,".format(temperature))
    
    ###
    elif text.find("습도 알려줘") >= 0:
        print("현재 실내 습도는 {0:0.1f} 퍼센트 입니다 ".format(humidity))
        return("현재 실내 습도는 {0:0.1f} 퍼센트 입니다ㅏ. ".format(humidity))
    
    ###
    elif text.find("날씨 알려줘") >= 0:
        #print("현재 온도는 {0:0.1f}도 이고, 습도는 {1:0.1f} 퍼센트 입니다 ".format(temperature, humidity))
        #return ("현재 온도는 {0:0.1f}도 이고, 습도는 {1:0.1f} 퍼센트 입니다 ".format(temperature, humidity))
        print("현재 {0:s}의 온도는 {1:s} 도 이고, 미세먼지는 {2:s}, 초미세먼지는 {3:s}이고, 습도는 {4:d} 퍼센트입니다 ".format(location,temp(),fd_level(),ufd_level(),hum()))
        return("현재 {0:s}의 온도는 {1:s} 도 이고, 미세먼지는 {2:s}, 초미세먼지는 {3:s}이고, 습도는 {4:d} 퍼센트입니다 ".format(location,temp(),fd_level(),ufd_level(),hum()))

        #return ("현재 {0:s}의 온도는 {1:s} 도 이고, 미세먼지는 {2:s}, 초미세먼지는 {3:s} 입니다ㅏ.".format(location,temp(),fd_level(),ufd_level()))
    
    ###
    elif text.find("미세먼지")>=0:
        print("현재 {0:s}의 미세먼지는 {1:s}로 {2:s}, 초미세먼지는 {3:s}로 {4:s}입니다. ".format(location,fine_dust(),fd_level(),ultra_fine_dust(),ufd_level()))
        return ("현재 {0:s}의 미세먼지는 {1:s}로 {2:s}, 초미세먼지는 {3:s}로 {4:s}입니다ㅏ. ".format(location,fine_dust(),fd_level(),ultra_fine_dust(),ufd_level()))
    ###
    elif text.find("현재 상태 알려줘")>=0:
        return giveSolution()
    
        
    ###
     ###
    elif text.find("틀어줘") >= 0 or text.find("들려줘") >=0 :
        
        search_text=''
        if(text.find("노래 틀어줘")>=0):
            for i in range (0,text.find("노래 틀어줘")):
                search_text+=text[i]
            print(search_text)
            
        elif(text.find("노래 들려줘")>=0):
            for i in range (0,text.find("노래 들려줘")):
                search_text+=text[i]
            print(search_text)

        elif(text.find("틀어줘")>=0):
            for i in range (0,text.find("틀어줘")):
                search_text+=text[i]
            print(search_text)

        elif(text.find("들려줘")>=0):
            for i in range (0,text.find("들려줘")):
                search_text+=text[i]
            print(search_text)
        
        ####
        result_url = youtube_search(search_text)
        play_with_url(result_url)
        return("유튜브에서 " + search_text + "노래를 재생했어요.")
    
    ###
    else:
        return qt.queryByText(text)
    ###
##===============================================================

##===============================================================
def main(): #Example7 KWS+STT
    KWSID = ['기가지니', '지니야', '친구야', '자기야']
    gs_call()  
    while 1:
            recog = kws.test(KWSID[0])
            if recog == 200:
                print('KWS Dectected …\n Start STT…')
                print('play_flag : ' + str(play_flag))
                print('num1 : '+str(num1))
                print('num2 : '+str(num2))
                text = gv2t.getVoice2Text()
                print('Recognized Text: '+ text)
                tts.getText2VoiceStream(checkCommand(text), "result_TTS.wav")
                MS.play_file("result_TTS.wav")
                #time.sleep(2)
               		
                            
            else:
                print('KWS Not Dectected …')
                
        
if __name__ == '__main__':
    main()
    
