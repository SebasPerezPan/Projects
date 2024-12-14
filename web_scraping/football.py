from bs4 import BeautifulSoup   
import requests

url = 'https://www.365scores.com/es-mx/football/league/liga-portugal-73/matches#results'
response = requests.get(url)


if response.status_code == 200:
    print('Success!')
    soup = BeautifulSoup(response.text, 'html.parser')
    div_on = soup.find_all('div', class_="list_container__AMVNC")
    for div in div_on:
        print(div)
        
else:
    print(f"Error. {response.status_code}")