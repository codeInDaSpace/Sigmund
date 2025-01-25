#all libraries being imported
import discord
import asyncio
import os
import random
from queue import Queue
from discord.ext import commands
from discord import FFmpegPCMAudio
from pytubefix import YouTube
from pytubefix.cli import on_progress
import scrapetube
import spotipy
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials

#imported file with apiKeys
from apiKeys import *

#creates the an object with all intents enabled, new bot is initialized with prefix $
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)


#allows to log in and access data from spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=spotifySecret))


#bot event, to have the bot ready to be in use
@bot.event
async def on_ready():
    print("Sigmund is now Ready for User")
    print("-----------------------------")



#bot command, hello, replies with message
@bot.command()
async def hello(ctx):
    await ctx.send("Hello, I am Sigmund the Penguin")


@bot.command()
async def back(ctx):
    await ctx.send("we're so back")

@bot.command()
async def Intro(ctx):
    await ctx.send("Hello, I am Sigmund the Penguin. I am a discord bot written in python. I am currently undergoing development and only run periodically, however during these times I would appreciate feedback on my performance, or any general request, you can send it in the botFeedback channel. Since I am running from a wireless connection my service may not be as good, but I will soon be connected directly to the internet.")



#bot event, when member joins server, prints on terminal, and sends message in discord chat
@bot.event
async def on_member_join(member):
    print(f"{member} has joined the server")
    channel = bot.get_channel(phiRhoId) 
    await channel.send("Welcome " f"{member} To the Phi Rho Server :)")



#bot event, when member leaves, prints on terminal, and sends message in discord chat
@bot.event
async def on_member_remove(member):
    print(f"{member} has left the server")
    channel = bot.get_channel(phiRhoId)
    await channel.send("Goodbye " f"{member} :(")

#NEED TO MAKE COMMAND DOES NOT EXIST FUNCTION


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel and (not after.channel or before.channel != after.channel):
        channel = before.channel
        if channel:  # Ensure the channel is not None
            members = channel.members
            print("member moved/left")
            print(f"Members remaining in channel: {len(members)}")
            for m in members:
                print(m)

            if len(members) == 1 and channel.members[0].name == 'Sigmund':
                voice = discord.utils.get(bot.voice_clients, guild=channel.guild)
                print(f"Voice client: {voice}")
                if voice:
                    print(f"Voice connected: {voice.is_connected()}")
                    if voice.is_connected():
                        await voice.disconnect()
                        print("Bot disconnected from the voice channel")
                    else:
                        print("Voice client is not connected")
                else:
                    print("No voice client found")
    




@bot.command(pass_context=True)
async def image(ctx):
    
    GenFile = random.choice(os.listdir("phiRhoPhotos")) 
    NewFile = 'phiRhoPhotos/' + GenFile
    print("received image request")
    await ctx.send(file=discord.File(NewFile))



    
q = asyncio.Queue()  #QUEUE FOR MUSIC


@bot.command(pass_context=True)
async def play(ctx, *, url):
    user = ctx.message.author
    if not user.voice:
        await ctx.send("You must be in a voice channel to use this command.")
        return

    vc = user.voice.channel
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    print("reached this point")

    if voice:
        print(f"Existing voice client found: {voice.is_connected()}")

    if voice and voice.is_connected():
        if voice.is_playing():
            await ctx.send("Added to queue")
            print("added to the queue")
            await AddToQueue(url)  # Ensure AddToQueue is implemented correctly
        else:
            try:
                await playAudio(url, ctx, voice)
            except Exception as e:
                await ctx.send(f"An error occurred while playing audio: {e}")
    else:
        try:
            print("Connected to voice channel.")
            voice = await vc.connect()
            await playAudio(url, ctx, voice)
        except Exception as e:
            await ctx.send(f"An error occurred while connecting to the voice channel: {e}")
            print(e)


listForContents = []

async def AddToQueue(name):
    await q.put(name)  # Adding to the queue
    listForContents.append(name)  # Adding to the list

           
async def PlayQueue(ctx, voice):
    if not q.empty():
        song = await q.get()
        listForContents.pop(0)
        print({song}, " is playing")
        await playAudio(song, ctx, voice)


@bot.command(pass_context=True)
async def showQueue(ctx):
    if len(listForContents) == 0:
        await ctx.send("Queue is empty")
    else:
        endstring = '\n'.join(str(item) for item in listForContents)
        await ctx.send(endstring)
    

    
async def playAudio(url, ctx, voice):
    print("Processing audio")
    
    if url[:5] == 'https':
        try:
            yt = YouTube(url)
            if yt.streams.filter(only_audio=True):
                stream = yt.streams.get_audio_only()
                newAudio = stream.download()
                print(f"Downloaded audio from YouTube: {newAudio}")
            else:
                await ctx.send("No audio stream available.")
                return
        except Exception as e:
            await ctx.send(f"Error downloading from YouTube: {e}")
            print(f"Error downloading from YouTube: {e}")
            return
    else:
        try:
            searchResults = sp.search(q=url, type="track")
            if searchResults and searchResults.get('tracks') and searchResults['tracks']['items']:
                track = searchResults['tracks']['items'][0]
                trackName = track['name']
                artistNames = "".join(artist['name'] for artist in track['artists'])
                search = list(scrapetube.get_search(trackName + artistNames, limit=1))
                
                if search:
                    video = search[0]
                    new_url = 'https://www.youtube.com/watch?v=' + video['videoId']
                    yt = YouTube(new_url)
                    if yt.streams.filter(only_audio=True):
                        stream = yt.streams.get_audio_only()
                        newAudio = stream.download()
                        print(f"Downloaded audio from Scrapetube result: {newAudio}")
                        await ctx.send(trackName + " by " + artistNames)
                    else:
                        await ctx.send("No audio stream available.")
                        return
                else:
                    await ctx.send("No search results found.")
                    return
            else:
                await ctx.send("No tracks found.")
                return
        except Exception as e:
            await ctx.send(f"Error searching for track: {e}")
            print(f"Error searching for track: {e}")
            return

    try:
        ffmpeg_options = {'options': '-vn -f s16le -ar 48000 -ac 2'}
        audio_source = discord.FFmpegPCMAudio(newAudio, **ffmpeg_options)
        volume_source = discord.PCMVolumeTransformer(audio_source, volume=0.5)
        voice.play(volume_source)
    except Exception as e:
        await ctx.send(f"Error initializing audio: {str(e)}")
        print(f"Error initializing audio: {str(e)}")
        return

    while voice.is_playing() or voice.is_paused():
        await asyncio.sleep(1)

    os.remove(newAudio)
    print("Playback finished")
    
    await PlayQueue(ctx, voice)



@bot.command(pass_context=True)
async def pause(ctx):
    user = ctx.message.author
     
    vc = user.voice.channel
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)


#checks if bot is already connected
    if voice and voice.is_playing():
            voice.pause()
            await ctx.send("Music is Paused")
    else:
        await ctx.send("Music is already paused")

@bot.command(pass_context=True)
async def resume(ctx):
    user = ctx.message.author
     
    vc = user.voice.channel
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)


#checks if bot is already connected
    if voice and voice.is_paused():
            voice.resume()
            await ctx.send("Resuming Music")
    else:
        await ctx.send("Music is already playing")


@bot.command(pass_context=True)
async def skip(ctx):
    user = ctx.message.author
    vc = user.voice.channel
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected() and voice.is_playing():
        # Stop the current playback
        voice.stop()

        # Check if there are more tracks in the queue and play the next one
        if not q.empty():
            await ctx.send("Song is Skipped")
            await PlayQueue(ctx, voice)
        else:
            await ctx.send("No more tracks in the queue.")
    else:
        await ctx.send("Nothing is playing that I could skip for you.")

#runs bot
bot.run(BOTtoken)
    

    