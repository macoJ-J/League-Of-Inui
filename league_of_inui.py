#!usr/bin/python3
# -*- coding: utf-8 -*-

import matplotlib as mpl
import matplotlib.pyplot as plt
import json
from requests_oauthlib import OAuth1Session
import sys
import collections
import config_of_inui

#仮
lol_version = "9.6.1"
API_KEY = config_of_inui.API_KEY
ACCOUNT_NAME = config_of_inui.ACCOUNT_NAME
SERVER_ID = config_of_inui.SERVER_ID

MATCH_LIST_URL ="https://jp1.api.riotgames.com/lol/match/v4/matchlists/by-account/"
ACCOUNT_ID_URL = "https://jp1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + ACCOUNT_NAME
GAME_INFO_URL = "https://jp1.api.riotgames.com/lol/match/v4/matches/"
LATEST_VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
CHAMPION_DATA_URL = "http://ddragon.leagueoflegends.com/cdn/" + lol_version + "/data/ja_JP/champion.json"
ITEM_DATA_URL = "http://ddragon.leagueoflegends.com/cdn/" + lol_version + "/data/ja_JP/item.json"

NORMAL_QUEUE = 430
SOLO_QUEUE = 420

#リストの先頭が最新バージョン
def get_latest_version(riot_api):
	req = riot_api.get(LATEST_VERSION_URL)
	return json.loads(req.text)[0]
	
def get_champion_data_json():
	req = riot_api.get(CHAMPION_DATA_URL)
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
		sys.exit()
		
	
def get_matches_list(account_id):
	params = {
		"api_key": API_KEY,
		"champion": 16,
		"season": 13,
		"platformId": SERVER_ID,
		"queue" : SOLO_QUEUE
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
			
	#idから勝敗、レーン、チームカラー、使用チャンプを取得
	for data in game_info['participants']:		
		if data['stats']['participantId'] == participant_id:
			win = data['stats']['win']	#bool
			lane = check_player_lane(data)
			team_color = data['teamId']
			my_champion_id = data['championId']
			my_champion_name = search_champion_name_from_json(my_champion_id,champion_json)
			break
			
	#BOTLANEだと対面が2体なのでbreakしない
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
				
				if lane is not "BOTTOM":
					break
					
def check_player_lane(data):

	lane = data['timeline']['lane']
	role = data['timeline']['role']
	SMITE_SPELL_ID = 11

	if data['spell1Id'] == SMITE_SPELL_ID or data['spell2Id'] == SMITE_SPELL_ID:
		lane = "JUNGLE"
	
	elif role == "DUO_SUPPORT":
		lane = "BOTTOM"
						
	return lane
	
def search_champion_name_from_json(champion_id,champion_json):
			
	for champion_data in champion_json['data'].items():
		if champion_data[1]["key"] == str(champion_id):
			return champion_data[1]['name']

if __name__ == "__main__":	

	riot_api =	OAuth1Session(API_KEY)
	
	lol_version = get_latest_version(riot_api)
	account_id = get_encrypted_account_id()
	match_list = get_matches_list(account_id)
	
	won_match_list = []
	lost_match_list = []
	
	champion_json = get_champion_data_json()
	
	for gameid in match_list:
		game_info = get_game_info(gameid)
		get_participant_id(game_info,account_id,won_match_list,lost_match_list,champion_json)	
	
	mpl.rcParams['font.family'] = 'Kozuka Mincho Pro'

	counted_won_match_list,won_match_value = zip(*collections.Counter(won_match_list).items())
	counted_lost_match_list,lost_match_value = zip(*collections.Counter(lost_match_list).items())

	#w_list =('カルマ', 'カシオペア', 'フィドルスティックス', 'ゼラス', 'ジンクス', 'ゼド', 'ダリウス', 'スレッシュ', 'ヴェイン', 'レオナ', 'ルシアン', 'スウェイン', 'エズリアル', 'アッシュ', 'ドレイヴン', 'トリスターナ')
	#w_value = (1, 1, 3, 1, 1, 1, 1, 6, 4, 5, 3, 1, 1, 1, 1, 1)
	#l_list =('ブリッツクランク', 'エズリアル', 'マルファイト', 'モルガナ', 'ミス・フォーチュン', 'リー・シン', 'ヨリック', 'ヤスオ', 'ルシアン', 'レオナ', 'スレッシュ', 'パイク', 'ガリオ', 'ジン', 'ヴェイン', 'レネクトン', 'ジャックス', 'ルブラン', 'アッシュ', 'シンジド', 'フィドルスティックス')
	#l_value = (2, 4, 1, 1, 2, 1, 1, 1, 2, 2, 4, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1)

	g_list = list(set(counted_won_match_list + counted_lost_match_list))
	g_value =[0] * len(g_list)
	g2_value =[0] * len(g_list)
	
	for index,champ in enumerate(g_list):
		
		matched_champ = g_list[index]
		matched_champ_in_glist = g_list.index(matched_champ)
		
		if champ in counted_won_match_list:
			#print(counted_won_match_list[counted_won_match_list.index(matched_champ)])
			#print(won_match_value[counted_won_match_list.index(matched_champ)])
			g_value[matched_champ_in_glist] = won_match_value[counted_won_match_list.index(matched_champ)]
			
		if champ in counted_lost_match_list:
			g2_value[matched_champ_in_glist] = lost_match_value[counted_lost_match_list.index(matched_champ)]
		
	#この方法だとどのチャンプに勝ったのかを送れない
	"""
	count = 0
	
	print(won_match_value)
	#チャンプ配列の中から
	for a in g_list :
		#勝ったマッチアップにいたら
		if a in counted_won_match_list:
			#勝った数に
			g_value.append(won_match_value[count])
			print(a)
			print(g_value)
			print(count)
			count+=1
			#g_value.append(int(counted_won_match_list.index(a)))

		else:
			g_value.append(0)


			
	count = 0
	for a in g_list :
		if a in counted_lost_match_list:
			g2_value.append(lost_match_value[count])
			count+=1
		else:
			g2_value.append(0)	
	"""	
	
	
	fig, axes = plt.subplots(figsize=(80, 4))
	axes.bar(g_list, g_value)
	axes.bar(g_list, g2_value, bottom=g_value)
	plt.tick_params(labelsize=3)
	plt.show()
		

