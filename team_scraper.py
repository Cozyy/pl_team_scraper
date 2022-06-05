import requests
from bs4 import BeautifulSoup,SoupStrainer
import bs4 
import json 


def upd_json_object(path,jsonObj):
    try: 
      with open(path,"w") as jsonFile:
         json.dump(jsonObj,jsonFile,indent = 2)
    except: 
      print(f"Could not store json-file to {path}")  
      

def parse_and_create(team_url,file_name="markdown.md"): 
    res_json = parse_team_page(team_url)
    md_string = create_formatted_discord_md_file(res_json,team_url,file_name=file_name)
    return md_string

def parse_team_page(team_url):
  page = requests.get(team_url)
  page.status_code

  soup = BeautifulSoup(page.content, 'html.parser')    
  res_json = {'players' : []}
  
  items = list(soup.children)
  level1 = items[2]
  items_lvl1 = list(level1.children)
  level2 = items_lvl1[3]
  items_lvl2 = list(level2.children)
  level3 = items_lvl2[3]
  items_lvl3 = list(level3.children)
  team_name = items_lvl3[3].get_text()
  level4 = items_lvl3[7]
  items_lvl4 = list(level4.children)
  level5 = items_lvl4[5]
  items_lvl5 = list(level5.children)
  level6 = items_lvl5[3] 
  items_lvl6 = list(level6.children)
  
  ####player infos ###
  for i,e in enumerate(items_lvl6):
      if type(e) == bs4.element.Tag:
        
        cur_player_info = list(filter(lambda e : e != "",e.get_text().split("\n")))
        player_info = {'pl_name':cur_player_info[0],'role':cur_player_info[1],'lol_name': cur_player_info[2], 'can_play' : cur_player_info[3]}
        res_json['players'].append(player_info)
        #print(player_info)
  ### team_name ###      
  team_name = items_lvl3[3].get_text()  
  team_name_split =  team_name.split("(")    
  res_json['team_name'] = team_name_split[0][:-1]
  res_json['tag'] = team_name_split[1][:-1]
  
  
  #### create multi gg ###
  multi_gg = "https://euw.op.gg/multisearch/euw?summoners="
  for player_info in res_json['players']:
    multi_gg = multi_gg + player_info['lol_name'].replace(" ","+") + "%2C+"
  res_json['multi_gg'] = multi_gg     
  ### get match links ###
  match_urls = []
  for a in soup.find_all('a', href=True):
      cur_url = a['href']
      prefix = 'https://www.primeleague.gg/leagues/matches/'
      
      if cur_url.startswith(prefix):
          if not cur_url in match_urls:
            match_urls.append(cur_url)
  
  #print(match_urls)
  matches = []  
  for m in match_urls:
    try:    
      matches.append({'match_url':m,'match':parse_match(m)}) 
    except:
      break      
  res_json['matches'] = matches
    
  ### calculations ###


  team_tag = res_json['tag']
  winrate = "100%"
  wins = 0 
  games = 0 
  champ_dict = {} 
  
  #init teamstats 
  teamstats = {"games":games,"wins":wins,"winrate":winrate} 
  player_stats = {p['lol_name'] : {'wins' : 0, 'games' : 0, 'champs_played' : {}} for p in res_json['players']}
  champ_stats = {}
  for m in res_json['matches']:
      cur_match = m['match']
      if cur_match['team1']['tag'] == team_tag:
          my_team = cur_match['team1']
          enemy_team = cur_match['team2']        
      else: 
          my_team = cur_match['team2']
          enemy_team = cur_match['team1']    
      games += 1 
      win_score = my_team['result']
      wins += win_score
      champions = my_team['champions']
      for champ in champions:
          champ_name = champ['champion']
          champ_player = champ['player']
          #update champion stats 
          if champ_name in champ_stats:
              champ_stats[champ_name]['wins']  += win_score
              champ_stats[champ_name]['games'] += 1 
          else:
              champ_stats[champ_name] = {'wins': win_score,'games' : 1}
          #update player stats     
          try:
            if champ_name in player_stats[champ_player]['champs_played']:
                player_stats[champ_player]['champs_played'][champ_name]['wins'] += win_score 
                player_stats[champ_player]['champs_played'][champ_name]['games'] += 1 
            else: 
               player_stats[champ_player]['champs_played'][champ_name] = {'wins': win_score,'games' : 1}  
            player_stats[champ_player]['games'] += 1
            player_stats[champ_player]['wins'] += win_score
          except:
              player_stats[champ_player] = {'wins' : win_score, 'games' : 1, 'champs_played' : {champ_name: {'wins': win_score,'games' : 1}}} 
              print(f"Player {champ_player} changed his name or is not part of the team anymore...")  
              
  teamstats['games'] = games  
  teamstats['wins'] = wins  
  teamstats['winrate'] = round(wins/games,2)     
              
                        
  res_json['teamstats'] = {'teamstats': teamstats, 'player_stats':player_stats, 'champ_stats' : champ_stats}              
    
  print("updating json file for:",res_json['tag'])
  upd_json_object(f"{res_json['tag']}.json",res_json)  
  return res_json 


def parse_match(match_url):
  print(f"parsing match:{match_url}")
  page = requests.get(match_url)
  page.status_code
  soup = BeautifulSoup(page.content, 'html.parser')  
  
  
  json_match = {'team1': {},'team2' : {}}
  #find team 1 vs team2 
  for div in soup.find_all("div", {"class": "a"}):
      
      cur_txt = div.get_text()
      if "vs." in cur_txt:
          splitted = cur_txt.replace("\n","").split(" ")
          team1 = splitted[1]
          team2 =splitted[3]
  
  json_match['team1']['tag'] = team1 
  json_match['team2']['tag'] = team2 
  
  
  #find bans 
  
  bans_soup = soup.find_all("div", {"class": "submatch-lol-bans"})
  bans_team1_soup = bans_soup[0]
  bans_team2_soup = bans_soup[1]
  bans_team1 = []
  bans_team2 = []
  for b in bans_team1_soup.children:
          if type(b) == bs4.element.Tag:
            bans_team1.append(b['title'])
  for b in bans_team2_soup.children:
          if type(b) == bs4.element.Tag:
            bans_team2.append(b['title'])
  json_match['team1']['bans'] = bans_team1
  json_match['team2']['bans'] = bans_team2 
                
  #find champions 
  champions_soup = soup.find_all("div", {"class": "submatch-lol-player-champion"})
  
  
  #find players of champions 
  players_soup = soup.find_all("div", {"class": "submatch-lol-player-name"})
  
  champs_team1 = []
  champs_team2 = []
  for i,champ in enumerate(champions_soup[:5]):
      champs_team1.append({'champion' :list(champ.children)[1]['title'],'player':players_soup[i].get_text()})
  for i,champ in enumerate(champions_soup[5:]):
      champs_team2.append({'champion' :list(champ.children)[1]['title'],'player':players_soup[i+5].get_text()})    
  champs_team2
  
  json_match['team1']['champions'] = champs_team1
  json_match['team2']['champions'] = champs_team2
  
  match_result = soup.find("span",{"class": "league-match-result"})
  results = match_result.get_text().split(":")
  team1_res = results[0]
  team2_res = results[1]
  json_match['team1']['result'] = int(team1_res)
  json_match['team2']['result'] = int(team2_res)
  #upd_json_object(f"match.json",json_match) 
  return json_match



def sort_by_other_list(list_to_sort,list_with_sort_values,descending=True):
  zipped_p = list(zip(list_to_sort,list_with_sort_values))
  zipped_p.sort(key=lambda x : x[1],reverse=descending)
  return list(map(lambda tpl : tpl[0],zipped_p)) 

def create_formatted_discord_md_file(res_json,team_url,file_name="markdown.md"):
  markdown_l = []
  
  team_name_md = f"__**Team: {res_json['team_name']} [{res_json['tag']}]**__  \n"
  team_url_md = f"**URL: {team_url}**  \n"
  multi_gg_md = f"**MultiGG: {res_json['multi_gg']}**  \n"
  performance_md = f"**Winrate: {res_json['teamstats']['teamstats']['winrate']*100} % ({res_json['teamstats']['teamstats']['games']} Games)**  \n"
  player_analysis_md = "__**Players**__  \n"
  players_md = []
  for player in res_json['teamstats']['player_stats']:
    cur_md = ""
    val =   res_json['teamstats']['player_stats'][player] 
    cur_games = res_json['teamstats']['player_stats'][player]['games'] 
    cur_champs_played = res_json['teamstats']['player_stats'][player]['champs_played'] 
    if cur_games == 0:
        cur_wr = 0
    else:
        cur_wr = round(res_json['teamstats']['player_stats'][player]['wins']/cur_games*100,2)
    #print(player) 
    underlining = "__                                                                                                 __ \n" 
    cur_md += underlining      
    cur_md += f"Name: {player}  \n"
    player_op_gg = f"https://euw.op.gg/summoners/euw/{player}".replace(" ","+")
    cur_md += f"op.gg : {player_op_gg}  \n"
    cur_md += f"Winrate: {cur_wr}% ({cur_games} Games)  \n"
    
    
    
    ### add champions played info to cur player md string 
    cur_md += "Champions played (sorted by total games played):  \n\n"
    champs_md = []
    for cur_champ in cur_champs_played:
        cur_champ_md = ""
        cur_games = cur_champs_played[cur_champ]['games']
        cur_wr = round(cur_champs_played[cur_champ]['wins']/cur_games * 100,2)
        cur_champ_md += f"{cur_champ} -> Winrate: {cur_wr}% ({cur_games} Games)  \n"
        champs_md.append(cur_champ_md)
    only_games_played_of_champs = [p['games']for p in cur_champs_played.values()] 
    champs_md = sort_by_other_list(champs_md,only_games_played_of_champs)
    
    #put rank before each champ 
    champs_md = [f"*{i+1}.* {ch_md}" for i,ch_md in enumerate(champs_md)]
    
    for ch in champs_md:
        cur_md += ch
    cur_md += "  \n" 
    players_md.append(cur_md) 
     
  
  #sort player descending by games_played 
  only_games_played = [p['games']for p in res_json['teamstats']['player_stats'].values()]
  #print(only_games_played)
  #zipped_p = list(zip(players_md,only_games_played))
  #zipped_p.sort(key=lambda x : x[1],reverse=True)
  #players_md = list(map(lambda tpl : tpl[0],zipped_p)) 
  players_md = sort_by_other_list(players_md,only_games_played)
  
  markdown_l.append(team_name_md)
  markdown_l.append(team_url_md)
  markdown_l.append(multi_gg_md)
  markdown_l.append(performance_md)
  markdown_l.append(player_analysis_md)
  markdown_l += players_md
  
  md_string = ""
  for m in markdown_l:
      md_string += m 
  md_string += underlining 
  md_string += "\n \n"    
  with open(file_name,"w") as f:
      f.write(md_string)
  return md_string        
      
  
  

    
        
