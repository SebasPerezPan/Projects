from bs4 import BeautifulSoup   
import requests

url = 'https://dockerlabs.es/'
response = requests.get(url)

if response.status_code == 200:
    print('Success!')
    soup = BeautifulSoup(response.text, 'html.parser')
    div_on = soup.find_all('div', onclick=True)
    for part_div in div_on:
        div_text = part_div['onclick']
        div_name = div_text.split("'")[1]
        
else:
    print(f"Error. {response.status_code}")