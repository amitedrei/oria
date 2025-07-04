import re
from typing import Optional, Set
from googletrans import Translator
from huggingface_hub import hf_hub_download
import fasttext
import json
import asyncio
from lyricsgenius import Genius
import os
import time
import copy

lang_model_path = hf_hub_download(repo_id="facebook/fasttext-language-identification", filename="model.bin")

class LyricsHandler:
    __lang_model = fasttext.load_model(lang_model_path)
    __translate_labels = {}
    __patterns = []
    __genius = None

    @classmethod
    def initialize(cls):
        if cls.__genius is None:
            cls.__genius = Genius(os.getenv("GENIUS_KEY"))
            cls.__genius.verbose = False
            cls.__genius.remove_section_headers = False
            cls.__genius.retries = 5

        data_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(data_dir, "data")

        if not cls.__translate_labels:
            with open(os.path.join(data_dir, 'fblabels_to_gtranslate.json'), 'r') as q:
                cls.__translate_labels = json.load(q)

        if not cls.__patterns:
            with open(os.path.join(data_dir, 'patterns.json'), 'r') as q:
                cls.__patterns = json.load(q)

    def __init__(self):
        self.__class__.initialize()
        self.__translator = Translator()


    async def __translate(self, text, src='', dst='en'):
        params = {'dest': dst}
        if src:
            params['src'] = src

        return await self.__translator.translate(text, **params)

    async def __determine_languages(self, text: str, splited: bool = False, google_format: bool = True):
        languages = list()

        if isinstance(text, list) or isinstance(text, set):
            tasks = [self.__determine_languages(entry, splited, google_format) for entry in text]
            return await asyncio.gather(*tasks)

        if not isinstance(text, str):
            return languages

        processed_entry = {text}
        if splited:
            processed_entry.update({i for i in text.split(' ') if i})

        for entry in processed_entry:
            try:
                label = await asyncio.to_thread(self.__class__.__lang_model.predict, entry)
                label = label[0][0].replace('__label__', '')
                label = self.__class__.__translate_labels[label] if google_format else label
                if label and label not in languages:
                    languages.append(label)

            except Exception as e:
                continue

        en_label = 'en' if google_format else 'eng_Latn'
        if en_label not in languages and re.match(r"^[a-zA-Z0-9\(\)\s]*$", text):
            languages.append(en_label)

        return languages

    async def __get_artists_variants(self, song_title, artists):
        title_languages = await self.__determine_languages(song_title, False, True)
        artists_languages = await self.__determine_languages(artists, True, True)

        results = []
        for index, artist in enumerate(artists):
            result = {artist}
            tasks = []

            for art_lang in artists_languages[index]:
                for title_lang in title_languages:
                    if art_lang == title_lang:
                        continue

                    tasks.append(self.__translate(artist, art_lang, title_lang))

            if tasks:
                translations = await asyncio.gather(*tasks, return_exceptions=True)
                for translation in translations:
                    if not isinstance(translation, Exception):
                        # Only add successful translations
                        result.add(translation.text)
                    else:
                        print(f"[Artists Variants Error] {str(translation)}")

            results.append(result)

        return results

    async def __sanitize_song_name(self, full_song_name, artists):
        clean_title = full_song_name
        clean_title = re.sub(r'[\u0000-\u001F\u007F-\u009F\u200B-\u200F\u2028-\u202F\u2060-\u206F]', '', clean_title)

        for pattern in self.__class__.__patterns:
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)

        wide_artists = await self.__get_artists_variants(clean_title, artists)
        for artist_wide in wide_artists:
            for name in artist_wide:
                clean_title = clean_title.replace(name, '')

        for c in ['-', '&', ',', '–', '|', '/', '\\']:
            clean_title = ' '.join([part for part in clean_title.split(' ') if part])
            clean_title = c.join([part for part in clean_title.split(c) if part])

        clean_title = ' '.join([part for part in clean_title.split(' ') if part])

        return {'name':clean_title, 'artists':wide_artists}

    async def __get_song_lyrics(self, song, try_count=0):
        try:    
            for artist_all in song['sartists']:
                for artist in artist_all:
                    data = self.__genius.search_song (
                        song['sname'],
                        artist,
                        get_full_info=True
                    )

                    if data:
                        lyrics = data.lyrics.splitlines()
                        if lyrics:
                            start = lyrics[0].find('[')
                            start = start if start != -1 else 0
                            lyrics[0] = lyrics[0][start:]

                        lyrics = [line.strip() for line in lyrics]
                        lyrics = '\n'.join(lyrics)
                        return lyrics

        except Exception as e:
            if '429' in str(e):
                print(e)
                print(f'Sleeping {(try_count +1) * 5} Minutes')
                time.sleep((try_count+1) * 5 * 60) # 5 Minutes
                return await self.__get_song_lyrics(song, try_count+1)

        return ""

    async def __get_chorus(self, eng_lyrics: str):
        sections = re.split(r'\n\s*\n+', eng_lyrics.strip())
        list_sections = [section.splitlines() for section in sections] 
        sanitzed_lyrics_list = []

        for i in range(len(sections)):
            res = sections[i]
            if sections[i].startswith('['):
                res = '\n'.join(sections[i].splitlines()[1:])

            sanitzed_lyrics_list.append(res)
            sanitized_lyrics = '\n'.join(sanitzed_lyrics_list)

        # Check by chorus
        for section in list_sections:
            if section:
                first_line = section[0].strip().lower()
                first_line = re.sub(r'(\[.*?)ditty(.*?\])', r'\1chorus\2', first_line, flags=re.IGNORECASE)
                first_line = re.sub(r'(\[.*?)choir(.*?\])', r'\1chorus\2', first_line, flags=re.IGNORECASE)
                first_line = re.sub(r'(\[.*?)refrain(.*?\])', r'\1chorus\2', first_line, flags=re.IGNORECASE)

                if re.search(r'\[.*chorus.*\]', first_line) and not re.search(r'\bpre[-\s]*chorus', first_line):
                    return sanitized_lyrics, '\n'.join(section[1:])
        
        if len(set(sanitzed_lyrics_list)) != len(sanitzed_lyrics_list):
            sections_sorted = sorted(sanitzed_lyrics_list)
            
            for index, entry in enumerate(sections_sorted):
                if not entry.strip():
                    continue

                if index >= (len(sections_sorted) - 1):
                    break

                if entry == sections_sorted[index + 1]:
                    return sanitized_lyrics, entry

        return sanitized_lyrics, sanitized_lyrics

    async def find_song(self, song) -> bool:
        result = await self.__sanitize_song_name(song['name'], song['artists'])
        song['sname'] = result['name']
        song['sartists'] = result['artists']

        try:
            song['embedding_sname'] = (await self.__translate(song['sname'])).text
        except Exception as e:
            song['embedding_sname'] = song['sname']

        
        src_lyrics = await self.__get_song_lyrics(song)
        if not src_lyrics:
            return False
        
        langs = await self.__determine_languages(' '.join(src_lyrics.splitlines()))
        parameters = {}
        if langs:
            parameters['src'] = langs[0]

        try:
            lyrics = (await self.__translate(text=src_lyrics, **parameters)).text
        except Exception as e:
            print(e)
            lyrics = src_lyrics

        try:
            lyrics, chorus =  await self.__get_chorus(lyrics)
            song['chorus'] = chorus

        except:
            song['chorus'] = lyrics

        song['lyrics'] = lyrics
        return True

    async def find_songs(self, songs):
        tasks = []
        for key, song in songs.items():
            tasks.append(self.find_song(song))

        results = await asyncio.gather(*tasks)