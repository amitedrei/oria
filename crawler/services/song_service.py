from models import Song
from typing import List, Dict, Any, Union, AsyncIterator

class SongService:
    async def sanitize_songs(songs: List[Song]) -> List[Song]:
        if not songs:
            return []
        
        snames = [song.sname for song in songs]
        
        existing_songs = await Song.find(
            {"sname": {"$in": snames}}
        ).to_list()
        
        existing_identifiers = set()
        for existing_song in existing_songs:
            artists_key = tuple(sorted([artist.lower() for artist in existing_song.artists]))
            existing_identifiers.add((existing_song.sname, artists_key))
            
            existing_identifiers.add((existing_song.sname, tuple(existing_song.chorus_embedding)))
        
        unique_songs = []
        for song in songs:
            song_artists_key = tuple(sorted([artist.lower() for artist in song.artists]))
            song_chorus_key = tuple(song.chorus_embedding)
            
            if ((song.sname, song_artists_key) not in existing_identifiers and 
                (song.sname, song_chorus_key) not in existing_identifiers):
                unique_songs.append(song)
        
        return unique_songs

    @classmethod
    async def add_songs(cls, songs_data: Dict[str, Dict[str, Any]]) -> bool:
        try:
            songs = [Song(**{'song_id': song_id, **song_data}) for song_id, song_data in songs_data.items()]
            songs = await cls.sanitize_songs(songs)
            if songs:
                await Song.insert_many(songs)
            return True
        except Exception as e:
            print(e)
            return False

    @staticmethod
    async def get_songs_by_source(source: str, as_list: bool = True) -> Union[List[Song], AsyncIterator[Song]]:
        query = Song.find({"source": {"$regex": source}})
        return await query.to_list() if as_list else query

    @staticmethod
    async def get_songs_not_in_sources(sources: List[str], as_list: bool = True) -> Union[
        List[Song], AsyncIterator[Song]]:
        query = {"$and": [{"source": {"$not": {"$regex": source}}} for source in sources]}
        find_query = Song.find(query)
        return await find_query.to_list() if as_list else find_query


    @staticmethod
    async def tag_songs(source: str, songs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        try:
            tagged_songs = {'exists': {}, 'new': {}}

            if not songs:
                return tagged_songs

            song_ids = list(songs.keys())

            existing_query = await Song.find(
                {"source": source, "song_id": {"$in": song_ids}}
            ).to_list()

            existing_ids = {song.song_id for song in existing_query}

            for song_id, song in songs.items():
                sub_key = 'exists' if song_id in existing_ids else 'new'
                tagged_songs[sub_key][song_id] = song

            return tagged_songs
        except Exception as e:
            print(f"Error in tag_songs: {e}")
            return {'exists': {}, 'new': {}}

    @staticmethod
    async def remove_old_songs(source: str, tagged_songs: Dict[str, Dict[str, Any]]) -> bool:
        try:
            good_songs = {**tagged_songs['new'], **tagged_songs['exists']}
            good_song_ids = set(good_songs.keys())

            await Song.find(
                {
                    "source": source,
                    "song_id": {"$nin": list(good_song_ids)}
                }
            ).delete_many()

            return True

        except Exception as e:
            return False

    @staticmethod
    async def update_existing_songs_playlists(source: str, tagged_songs: Dict[str, Dict[str, Dict[str, Any]]]) -> bool:
        try:
            if 'exists' not in tagged_songs or not tagged_songs['exists']:
                return True

            # Create a bulk write operation instead of individual updates
            bulk_operations = []
            for song_id, song_data in tagged_songs['exists'].items():
                if 'playlists' in song_data:
                    bulk_operations.append(
                        Song.UpdateOne(
                            {"source": source, "_id": song_id},
                            {"$set": {"playlists": song_data['playlists']}}
                        )
                    )
            
            # Execute bulk operation if there are updates to perform
            if bulk_operations:
                await Song.collection.bulk_write(bulk_operations)

            return True
        except Exception as e:
            print(f"Error updating playlists: {e}")
            return False