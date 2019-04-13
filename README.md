![乾](https://github.com/macoJ-J/League-Of-Inui/blob/images/inuiFace.jpg)

# League-Of-Inui
リーグオブレジェンドのサモナーネームと調べたいchampを入力すると自分のそのchampの戦績がグラフで表示されます。  
  
If you enter the summoner name and the champion name you want to check, the results of your own champ will be displayed in a graph.

## Demo
![sample](https://github.com/macoJ-J/League-Of-Inui/blob/images/sample.png)

Blue bar meaning "win",orange bar meaning "lose".  
If you pick ADC or Support, then analyze both enemy champ in bot lane.

## Requirement
matplotlib  
request_oauthlib  
config_of_inui.py(config file)

## Usage
create config_of_inui.py

then input those.
```
config_of_inui.py
# -*- coding: utf-8 -*-  
  
API_KEY = "" #https://developer.riotgames.com  
ACCOUNT_NAME = "" #your account name  
SERVER_ID = "" # https://developer.riotgames.com/regional-endpoints.html  
```

run league-of-inui.py

input your champion name what want to analyze.

## Author

[macoj](https://github.com/macoJ-J)
