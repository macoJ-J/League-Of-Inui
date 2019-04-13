#!usr/bin/python3
# -*- coding: utf-8 -*-

import matplotlib as mpl
import matplotlib.pyplot as plt
import json
from requests_oauthlib import OAuth1Session
import sys
import collections
import config_of_inui
import enum
from time import sleep

API_KEY = config_of_inui.API_KEY
ACCOUNT_NAME = config_of_inui.ACCOUNT_NAME
SERVER_ID = config_of_inui.SERVER_ID

MATCH_LIST_URL ="https://" + SERVER_ID + ".api.riotgames.com/lol/match/v4/matchlists/by-account/"
ACCOUNT_ID_URL = "https://" + SERVER_ID + ".api.riotgames.com/lol/summoner/v4/summoners/by-name/" + ACCOUNT_NAME
GAME_INFO_URL = "https://" + SERVER_ID + ".api.riotgames.com/lol/match/v4/matches/"
LATEST_VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"

lol_version = json.loads(OAuth1Session(API_KEY).get(LATEST_VERSION_URL).text)[0]

CHAMPION_DATA_URL = "http://ddragon.leagueoflegends.com/cdn/" + lol_version + "/data/ja_JP/champion.json"
ITEM_DATA_URL = "http://ddragon.leagueoflegends.com/cdn/" + lol_version + "/data/ja_JP/item.json"

class Queue(enum.IntEnum):	
	SOLO = 420
	NORMAL = 430
	TEAM = 440
	
class SupportItem(enum.IntEnum):
	pass

	
#リストの先頭が最新バージョン,現在未使用
def get_latest_version(riot_api):
	req = riot_api.get(LATEST_VERSION_URL)
	return json.loads(req.text)[0]

def get_champion_data_json():
	req = riot_api.get(CHAMPION_DATA_URL)
	return json.loads(req.text)
	
def get_item_data_json():
	req = riot_api.get(ITEM_DATA_URL)
	return json.loads(req.text)

def get_encrypted_account_id():
	params = {
		"api_key": API_KEY,
	}
	
	req = riot_api.get(ACCOUNT_ID_URL, params = params)
	
	if req.status_code == 200:
		return json.loads(req.text)['accountId']
		
	else:
		print("ERROR:" + str(req.status_code))
		print(req.headers)
		sys.exit()
	
def get_matches_list(account_id,champ_id):
	params = {
		"api_key": API_KEY,
		"champion": champ_id,
		"season": 13,
		"platformId": SERVER_ID,
		"queue" : int(Queue.SOLO)
	}
	
	req = riot_api.get(MATCH_LIST_URL + account_id, params = params)
	
	return [match_info['gameId'] for match_info in json.loads(req.text)['matches']]

def get_game_info(game_id):
	
	params = {
		"api_key": API_KEY,
		"matchId": game_id,
	}
	
	req = riot_api.get( GAME_INFO_URL + str(game_id),params = params)
	
	if req.status_code == 200:
		return json.loads(req.text)
	else:
		print("ERROR:" + str(req.status_code))
		sys.exit()

	
#アカウントのidが一致したらそのプレイヤーのロールをチェック
def get_participant_id(game_info,account_id,won_match_list,lost_match_list,champion_json):
	
	#試合のプレイヤーのidを取得
	for data in game_info['participantIdentities']:
		if data['player']['currentAccountId'] == account_id:
			participant_id = data['participantId']
			break
			
	#プレイヤーidから勝敗、レーン、チームカラー、使用チャンプを取得
	for data in game_info['participants']:		
		if data['stats']['participantId'] == participant_id:
			win = data['stats']['win']	#bool
			lane = check_player_lane(data)
			team_color = data['teamId']
			my_champion_id = data['championId']
			my_champion_name = search_champion_name_from_json(my_champion_id,champion_json)
			break
			
	for data in game_info['participants']:
		if data['teamId'] is not team_color:
			enemy_lane = check_player_lane(data)
			#敵チームで対面なら
			if enemy_lane == lane and lane is not "NONE":
				enemy_champion_id =data['championId']
				enemy_champion_name = search_champion_name_from_json(enemy_champion_id,champion_json)
				if win:
					won_match_list.append(enemy_champion_name)
				else:
					lost_match_list.append(enemy_champion_name)
				#BOTLANEだと対面が2体なのでbreakしない
				if lane is not "BOTTOM":
					break
					
def check_player_lane(data):

	lane = data['timeline']['lane']
	role = data['timeline']['role']
	item_list = [data['stats']['item0'],data['stats']['item1'],data['stats']['item2'],data['stats']['item3'],data['stats']['item4'],data['stats']['item5'],data['stats']['item6']]
	#support_item_list = [3301,3096,3069,3302,3097,3401,3303,3098,3092]
	#強化したもののみでフィルタしてみる
	support_item_list = [3096,3069,3097,3401,3098,3092]
	SMITE_SPELL_ID = 11

	if data['spell1Id'] == SMITE_SPELL_ID or data['spell2Id'] == SMITE_SPELL_ID:
		lane = "JUNGLE"
		
	elif role == "DUO_CARRY":
		lane = "BOTTOM"
		
	#綺麗な書き方がわからない	
	elif [lambda:None for item in item_list if item in support_item_list]:
		lane = "BOTTOM"	
	#サポートアイテム、スマイトもってないのにduo_supportならmidで決め打ち
	elif role == "DUO_SUPPORT":
		lane = "MIDDLE"
						
	return lane
	
def search_champion_name_from_json(champion_id,champion_json):
			
	for champion_data in champion_json['data'].items():
		if champion_data[1]["key"] == str(champion_id):
			return champion_data[1]['name']
			
def translate_champ_id_from_name(champ_name):
	for champion_data in champion_json['data'].items():
		if champion_data[0] == champ_name:
			return champion_data[1]["key"]
		else:
			pass
	print("チャンピオン名はこれであっていますか？ / is this correct champ name?:" + champ_name)
	
			
def create_stacked_bar_chart(g_list,won_game_value,lost_game_value):
	
	mpl.rcParams['font.family'] = 'Kozuka Mincho Pro'
	fig, axes = plt.subplots(figsize=(90, 4))
	axes.set_title( ACCOUNT_NAME + "stats")

	p1 = axes.bar(g_list, won_game_value)
	p2 =axes.bar(g_list, lost_game_value, bottom=won_game_value)
	axes.legend((p1[0],p2[0]),("win","lose"))
	axes.tick_params(labelsize=90/len(g_list) + 1)
	axes.set_ylabel("Games")
	#plt.tight_layout()
	plt.show()

if __name__ == "__main__":	
	riot_api =	OAuth1Session(API_KEY)
	champion_json = get_champion_data_json()
	print("チャンプ名を英語で入力してください。/ Enter your champion name.")
	print("o:Sona,MonkeyKing,TwistedFate ")
	print("x:ソナ,sona,wukong")
	while True:
		champ_name = input()
		champ_id = translate_champ_id_from_name(champ_name)
		if champ_id is not None:
			break
		print("もう一度入力してください。/ Retry.")
	
	account_id = get_encrypted_account_id()
	match_list = get_matches_list(account_id,champ_id)	
	won_match_list = []
	lost_match_list = []
	item_json = get_item_data_json()
	
	for index, gameid in enumerate(match_list):
		game_info = get_game_info(gameid)
		get_participant_id(game_info,account_id,won_match_list,lost_match_list,champion_json)
		
		if index is 80:
			sleep(30)
	

	counted_won_match_list,won_match_value = zip(*collections.Counter(won_match_list).items())
	counted_lost_match_list,lost_match_value = zip(*collections.Counter(lost_match_list).items())

	g_list = list(set(counted_won_match_list + counted_lost_match_list))
	g_value =[0] * len(g_list)
	g2_value =[0] * len(g_list)
	
	for index,champ in enumerate(g_list):
		
		matched_champ = g_list[index]
		matched_champ_in_glist = g_list.index(matched_champ)
		
		if champ in counted_won_match_list:
			g_value[matched_champ_in_glist] = won_match_value[counted_won_match_list.index(matched_champ)]
			
		if champ in counted_lost_match_list:
			g2_value[matched_champ_in_glist] = lost_match_value[counted_lost_match_list.index(matched_champ)]
	
	create_stacked_bar_chart(g_list,g_value,g2_value)

		

