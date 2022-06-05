# bot.py
import os

import discord
from dotenv import load_dotenv
from team_scraper import parse_team_page,create_formatted_discord_md_file,parse_and_create





load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'{client.user} is connected to the following guilds:\n')
    for guild in client.guilds:
       print( f'{guild.name}(id: {guild.id})')
       
@client.event
async def on_message(message):
    if message.author == client.user:
        return



    if message.content.startswith("!pl_team_check"):
        url_try = message.content.replace("!pl_team_check","").replace(" ","").replace("\n","")
        pl_pre = "https://www.primeleague.gg/leagues/teams/"
        
        if url_try.startswith(pl_pre):
          #try:    
          md_string = parse_and_create(team_url=url_try,file_name="nms.md") 
          start_bound = 0
          end_bound = 1900
          while end_bound < len(md_string):
            await message.channel.send(f"{md_string[start_bound:end_bound]}")
            start_bound = end_bound 
            end_bound += 1900
          await message.channel.send(f"{md_string[start_bound:]}")  
          ##except:
          ##  await message.channel.send(f"Something went wrong :*( \nTeamlink could not be analysed...")     
        else: 
          await message.channel.send(f"Wrong URL-Format! \nGiven url '{url_try}' needs to begin with {pl_pre}")         
        
    
    return   
  
client.run(TOKEN)

