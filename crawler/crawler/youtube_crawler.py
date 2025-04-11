import os
from abc import ABC
from . import crawler
import re
import json
from yt_dlp import YoutubeDL
import asyncio
import time

output_dir = './data/'

class YoutubeCrawler(crawler.Crawler):
    def __init__(self):
        super().__init__("Youtube")
        self.playlists = set()
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'quiet': True,
            'no_warnings': True,
            'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
            'noplaylist': True,
        }

    async def add_playlist(self, id_param: str):
        new = []
        if isinstance(id_param, str):
            new = [id_param]

        elif isinstance(id_param, list) or isinstance(id_param, set):
           new = list(id_param.copy())

        else:
            raise Exception(f'Given Parameter {id_param} is not a str or list/set')

        for playlist_id in new:
            if playlist_id in self.playlists:
                continue

            songs = await self.__get_playlist(playlist_id)
            if not songs or not len(songs):
                print(f'Playlist ID `{playlist_id}` not found')
                continue

            self.playlists.add(playlist_id)

        return True

    async def _Crawler__download_song(self, song_id, song):
        if not song_id or 'url' not in song or not song['url']:
            return {}

        try:
            try:
                with YoutubeDL(self.ydl_opts) as ydl:
                    ydl.download([song['url']])
            except:
                time.sleep(5)
                return await self._Crawler__download_song(song_id, song)

            song_path = f"{output_dir}{song_id}.wav"
            with open(song_path, 'rb') as q:
                data = q.read()

            while os.path.exists(song_path):
                try:
                    os.remove(song_path)
                except:
                    continue

            return {'file_name':f"{song_id}.wav",'data':data}

        except Exception as e:
            raise e
            return {}


    @staticmethod
    def __get_artist_name(song_data):
        artists = []
        try:
            artists_data = song_data['flexColumns'][1]['musicResponsiveListItemFlexColumnRenderer']['text']['runs']
            for artist in artists_data[::2]:
                artists.append(artist['text'])
        except Exception as e:
            pass

        return artists

    @staticmethod
    def __get_song_name(song_data):
        try:
            return song_data['flexColumns'][0]['musicResponsiveListItemFlexColumnRenderer']['text']['runs'][0]['text']
        except Exception as e:
            return ""

    @staticmethod
    def __get_song_id(song_data):
        try:
            watch_data = song_data['flexColumns'][0]['musicResponsiveListItemFlexColumnRenderer']['text']['runs'][0]['navigationEndpoint']['watchEndpoint']
            return watch_data['videoId']
        except Exception as e:
            return ""

    @staticmethod
    def __get_song_url(song_id):
        if not song_id:
            return ""

        return f"https://music.youtube.com/watch?v={song_id}"

    @staticmethod
    def __get_song_thumbnail(song_data):
        try:
            return song_data['thumbnail']['musicThumbnailRenderer']['thumbnail']['thumbnails'][0]['url']
        except:
            return ""


    async def __get_playlist(self, playlist_id):
        async with self.session.get(f"https://music.youtube.com/playlist?list={playlist_id}") as resp:
            text = await resp.text()

        result = re.findall(r"'\\/browse',\s*params:\s*JSON.parse.*, data:\s*'(.*)'}", text)
        if not len(result):
            return {}

        try:
            bytes_data = result[0].encode('utf-8').decode('unicode-escape').encode('latin1')
            result = json.loads(bytes_data)
            songs = result['contents']['twoColumnBrowseResultsRenderer']['secondaryContents']['sectionListRenderer']['contents'][0]
            songs = songs['musicPlaylistShelfRenderer']['contents']
            return songs
        except Exception as e:
            return ""

    async def __parse_playlist(self, playlist_id):
        songs = await self.__get_playlist(playlist_id)
        if not songs or not len(songs):
            return False

        for song_data in songs:
            try:
                song_data = song_data['musicResponsiveListItemRenderer']
            except:
                continue

            # Results
            song_id = self.__get_song_id(song_data)
            song_name = self.__get_song_name(song_data)
            song_url = self.__get_song_url(song_id)
            artists = self.__get_artist_name(song_data)
            thumbnail = self.__get_song_thumbnail(song_data)

            self._add_to_results(song_id, song_name, artists, song_url, thumbnail, {playlist_id})

        return True

    async def get_playlists(self):
        return self.playlists.copy()

    async def _Crawler__crawl(self):  # This should be called by crawl_all
        tasks = []

        for playlist in self.playlists:
            tasks.append(self.__parse_playlist(playlist))

        await asyncio.gather(*tasks)
