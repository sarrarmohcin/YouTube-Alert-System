
from curl_cffi.requests import AsyncSession
import feedparser


class youtubeChannelController:

    
    VIDEO_LIMIT = 10
    '''
        class constructor: 
        - get source object {'id', 'source_name', 'url'}
    '''
    def __init__(self, source, logger):
        self.source = source
        self.logger = logger

    # -----------------------------------------------------------------------------------------------------
    '''
        Function "start" : 
        - iterate over all types, 
        - run get_videos function to get video from channel
    '''
    async def start(self):
        
        try:
            
            
            # test if source has a valid url
            if self.source['url'] is None or self.source['url'] == '' or self.source['url'] == 'null':
                raise Exception(f"Source doesnt have url")
            
            # check rss pattern
            if "youtube.com/feeds/videos.xml?channel_id" not in self.source['url']:
                raise Exception(f"Source RSS url not valid")
                
            
            # get videos data from RSS url
            videos = await self.get_videos()
            
            # test if video not empty
            if not videos:
                raise Exception(f"videos not Found")
            
            # limit number of videos
            videos = videos[:self.VIDEO_LIMIT]
            
            self.logger.info(f"Source: {self.source}, Message: Extracting {len(videos)} videos")
            
            return videos
            
            
        except Exception as e:
            raise Exception(f"Failed to get videos from channel {str(e)}")
            return None
    
    # -----------------------------------------------------------------------------------------------------
    '''
    get videos from channel via RSS
    '''
    async def get_videos(self):
        try:
            channel_url = self.source['url']
            
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            }
            
            session = AsyncSession(
                    impersonate="chrome120",
                )
            session.headers.update(headers)
            
            response = await session.get(channel_url)
            response.raise_for_status()
            rss = feedparser.parse(response.text)
            
            results = rss['entries']
            # test if result is not None or empty
            if results is None or not isinstance(results, list) or len(results) == 0 :
                raise Exception(f"Empty results from RSS feed")
            
            videos = []
            # iterate over results and get data
            for result in results:
                
                # get the article url
                video_id = result.get("yt_videoid", None)
                if not video_id:
                    continue
                
                # add video info
                videos.append({
                        "source_id": self.source['id'],
                        "source_name": self.source['source_name'],
                        "source_url": self.source['url'],
                        "video_id" : video_id
                    })
                
            
            return videos
            
            
        except Exception as e:
            raise Exception(f"Failed to get videos from rss, {str(e)}")
            return None
        
    