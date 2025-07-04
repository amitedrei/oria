import asyncio
import json
from abc import ABC, abstractmethod
import os
import aiohttp
from crawler import LyricsHandler
from services.song_service import SongService
import json
import time

BACKEND_URL = os.getenv('BACKEND_URL') or 'http://localhost:8000'

class Crawler:
    __crawler_list = []
    __interval = 0
    __lyrics_handler = None

    @classmethod
    def initialize(cls):
        """Initialize shared resources"""
        if cls.__lyrics_handler is None:
            LyricsHandler.initialize()
            cls.__lyrics_handler = LyricsHandler()

    def __init__(self, source_name):
        Crawler.initialize()

        # Default to running once per day (24 hours) if not defined by user.
        if not self.__class__.__interval:
            self.__class__.__interval = 1 * 24 * 60 * 60

        self.__results = {}
        self.initialized = False
        self.session = None
        self.source_name = source_name

    async def __set_session(self):

        connector = aiohttp.TCPConnector(
                    
                )
        
        connector = aiohttp.TCPConnector(
                    limit=10,           # Total connection pool size
                    limit_per_host=2,   # Max connections per host
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
        
        session = aiohttp.ClientSession(headers={
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36'
            },
        timeout=aiohttp.ClientTimeout(total=300),
        connector=connector
        )

        return session

    @classmethod
    def set_interval(cls, interval):
        if type(interval) not in [float, int] or interval <= 0:
            return False

        cls.__interval = interval * 24 * 60 * 60
        return True

    async def start(self):
        if not self.initialized:
            if not self.session:
                self.session = await self.__set_session()
            Crawler.__crawler_list.append(self)
            self.initialized = True

    async def stop(self):
        if self.initialized:
            Crawler.__crawler_list.remove(self)
            self.initialized = False
            try:
                await self.session.close()
            except:
                pass

            self.session = None

    @staticmethod
    async def __crawl_once():
        results = {}
        tasks = []

        crawlers = [crawler for crawler in Crawler.__crawler_list if crawler.initialized]

        for crawler in crawlers:
            crawler.__results.clear()
            tasks.append(crawler._Crawler__crawl())

        await asyncio.gather(*tasks)
        tasks.clear()
        crawl_results = []
        for i in range(5):
            print(f'[Enumeration {i+1}]')
            print('[~] Tagging Songs')
            for index, crawler in enumerate(crawlers):
                if not i:
                    crawl_results.append(await SongService.tag_songs(crawler.get_source_name(), crawler.__get_results()))
                    new_songs = len(crawl_results[index]['new'])
                    total_songs = new_songs + len(crawl_results[index]['exists'])

                    if total_songs:
                        print(f'[~] `{crawler.get_source_name()}` Crawler Found {total_songs} Songs, Out Of them {new_songs} are new!')

                        if not await SongService.remove_old_songs(crawler.get_source_name(), crawl_results[index]):
                            print(f"[!] Couldn't Remove Old Songs For Source `{crawler.get_source_name()}`")

                        if not await SongService.update_existing_songs_playlists(crawler.get_source_name(), crawl_results[index]):
                            print(f"[!] Couldn't Update Existing Songs For Source `{crawler.get_source_name()}`")

                else:
                    crawl_results[index] = await SongService.tag_songs(crawler.get_source_name(), crawl_results[index]['new'])

                crawl_results[index]['new'] = dict(sorted(crawl_results[index]['new'].items(), key=lambda item: len(item[1]['name'])))
               
            print('[~] Getting Song Embeddings And Adding To DB')
            for index, crawler in enumerate(crawlers):
                print(f"[ Adding `{crawler.get_source_name()}` Crawler's Songs ]")
                await crawler.__crawlers_results_to_db(crawl_results[index]['new'])

            await asyncio.sleep(10)

    @classmethod
    async def crawl_all(cls):
        await cls.__crawl_once()


    @abstractmethod
    async def get_playlists(self):
        pass

    @abstractmethod
    async def __crawl(self):
        pass

    def get_source_name(self):
        return self.source_name
    
    async def __get_song_embedding(self, song_id, song, minimize_chorus=0, data=None):
        if 'lyrics' not in song:
            status = await Crawler.__lyrics_handler.find_song(song)
            if not status:
                return

        if not all(key in song for key in ['embedding_sname', 'chorus']):
            return 
        
        form_data = aiohttp.FormData()
        form_data.add_field('name', song['embedding_sname'])

        chorus = ''
        if minimize_chorus:
            chorus_list = song['chorus'].replace('\n', ' ').split(' ')
            for entry in chorus_list:
                if (len(chorus) + len(entry) + 1) > minimize_chorus:
                    break

                chorus += f'{entry} '

            chorus = chorus.strip()

        else:
            chorus = song['chorus']
            
        form_data.add_field('chorus', chorus)
        
        embeddings = []

        try:
            async with self.session.post(f"{BACKEND_URL}/data-transformers/song", data=form_data) as resp:
                if resp.status == aiohttp.http.HTTPStatus.OK:
                    embeddings = json.loads(await resp.text())
                
            if not embeddings and minimize_chorus != 400:
                minimize_chorus = minimize_chorus-50 if minimize_chorus else 450
                return await self.__get_song_embedding(song_id, song, minimize_chorus, data=data)

        except Exception as e:
            print(f"Failed To talk with oriapp backend. Recevied -> {e}")
            return

        finally:
            del form_data

        if embeddings:             
            song['name_embedding'] = embeddings[0]
            song['chorus_embedding'] = embeddings[1]
            return
                
            
    def _add_to_results(self, song_id, name, artists, url, thumbnail, playlists):
        song = {
            'source': self.source_name,
            'name': name,
            'artists': artists,
            'url': url,
            'thumbnail': thumbnail,
            'playlists': playlists,
        }

        if not all([song_id, song['name'], song['url'], song['artists'], song['thumbnail']]):
            return False
        if song_id in self.__results:
            self.__results[song_id]['playlists'].update(song['playlists'])
            return True

        self.__results[song_id] = song

    
    async def __crawlers_results_to_db(self, songs):
        songs_per_batch = 10
        tasks = []
        evaluated_songs = {}
        for index, (song_id, song) in enumerate(songs.items()):
            
            evaluated_songs[song_id] = song
            tasks.append(self.__get_song_embedding(song_id, song))
            if len(tasks) == songs_per_batch:
                await asyncio.gather(*tasks)

                evaluated_songs = {song_id: song for song_id, song in evaluated_songs.items() if 'name_embedding' in song and song['name_embedding']}
                await SongService.add_songs(evaluated_songs)
                tasks.clear()
                evaluated_songs.clear()
                await asyncio.sleep(0.3)

            if index and not (index+1) % 10:
                print(f'Checked {index+1} Songs out Of {len(songs)}')

        if tasks:
            await asyncio.gather(*tasks)
            evaluated_songs = {song_id: song for song_id, song in evaluated_songs.items() if 'embedding' in song and song['embedding']}
            await SongService.add_songs(evaluated_songs)

    def __get_results(self):
        return self.__results