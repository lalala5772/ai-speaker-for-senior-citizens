url1 = requests.get('https://search.naver.com/search.naver?query= 덕진구 금암1동 날씨')
soup1 = bs(url1.text,'html.parser')
location=soup1.find('h2',"title").text
dust_loc=urllib.parse.quote('덕진구 금암1동'+ ' 미세먼지')
url2=requests.get('https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query='+dust_loc)
soup2=bs(url2.text,'html.parser')

#미세먼지
dust1=soup2.find('div',class_='state_info _fine_dust _info_layer').find('span',class_= 'num _value').text
dust1=int(dust1)
print(dust1)

#초미세먼지
dust2=soup2.find('div',class_='state_info _ultrafine_dust _info_layer').find('span',class_='num _value').text
dust2=int(dust2)
print(dust2)

#온도
temp = soup1.find('div',class_='temperature_text').text
temp = temp[6:10]
temp = float(temp)
print(temp)

#습도
hum = soup1.find('dl',class_='summary_list').text
hum = hum[13:15]
print(hum)
