import asyncio
import os
import time
import sys
from crawler import crawler, youtube_crawler
from utils import db
from dotenv import load_dotenv
import yaml
load_dotenv()

INTERVAL_SECONDS = 1

# Fixes asyncio error
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

crawlers = {}
config = None


async def set_youtube_crawler(conf):
    if not 'playlists' in conf:
        return None

    yc = youtube_crawler.YoutubeCrawler()
    await yc.start()
    await yc.add_playlist(conf['playlists'])
    print(f'Youtube Crawler is Startd with {len(yc.playlists)} playlists')
    return yc


async def set_crawlers():
    global crawlers
    if not 'crawlers' in config:
        raise Exception('crawlers not configured in config')

    if 'youtube' in config['crawlers']:
        crawlers['youtube'] = await set_youtube_crawler(config['crawlers']['youtube'])

async def main():
    global config
    with open('config.yaml', 'r') as q:
        config = yaml.safe_load(q)

    await db.init_database(os.getenv('MONGO_URL'), os.getenv('MONGO_DB'))
    
    await set_crawlers()

    print('Crawling!')
    await crawler.Crawler.crawl_all()
    return 0

if __name__ == '__main__':
    asyncio.run(main())
