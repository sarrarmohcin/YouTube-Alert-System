

import yt_dlp
from curl_cffi.requests import AsyncSession
from fake_useragent import UserAgent
import re
import xml.etree.ElementTree as ET
import random
import asyncio 
from langdetect import detect
import time

class youtubeVideoController:
    

    
    def __init__(self,video, logger):
        self.video = video
        self.logger = logger

    
    '''
    start function : get video infos, open the video url and extract data
    '''
    async def start(self):
        
        try:

            # start scraping
            video_info = await self.get_video()

            self.logger.info(f"Video: {self.video}, Message: Scraping video with success")
            
            return video_info

        except Exception as e:
            raise Exception(f"Failed to get video infos {str(e)}")
            return None
        
    '''
    get_video function : open the video url and extract data
    '''
    async def get_video(self, get_comments = False):
        # yt_dlp options
        ydl_opts = {
            'ignore_no_formats_error': True,
            'check_formats': False,
            'no_warnings': True,
            'quiet': True,
            'getcomments': get_comments,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['all'], 
            'extract_flat': False,
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                )
            },
            
        }
        
        # get video url
        video_id = self.video['video_id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        data = []
        # start extraction
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # extract video info
                info = ydl.extract_info(video_url, download=False)

                # get title
                title = info.get('title', None)
                if not title:
                    raise Exception(f"Video without title")
                
                # get thumbnail
                media = info.get('thumbnail', None)
                
                # get published_date         
                published_date = info.get('timestamp', None)
                
                # get interactions
                views = info.get('view_count', 0)
                likes = info.get('like_count', 0)
                comments = info.get('comment_count', 0)
                length = info.get('duration', 0)
                
                # get source name and url from video info if search bu keyword, or form the Database if search by source
                source_name = self.video['source_name'] if self.video['source_name'] is not None else info.get('uploader', None)
                source_url = self.video['source_url'] if self.video['source_url'] is not None else info.get('uploader_url', None)
                
                    
                # get transcript_url and language of the video
                language = None
                transcript_url = None
                
                transcript = self.get_transcript(info)
                if not transcript:
                    # detect language from title using langdetect
                    language = detect(info.get('title'))
                else:
                    language = transcript['language']
                    transcript_url = transcript['transcript_url']
                
                # download the transcript from url
                content = None
                if transcript_url:
                    content = await self.download_transcript(transcript_url)
                
                
                # create the article schema
                video_info = {
                    "source_id":self.video['source_id'],
                    "source_name":source_name,
                    "source_url":source_url,
                    "title": title,
                    "content": content,
                    "url": video_url,
                    "media": media,
                    "lang": language,
                    "published_date": published_date,
                    "extracted_date": int(time.time()),
                    "interactions": {
                        "views": views,
                        "likes": likes,
                        "comments": comments,
                        "length": length,
                    }
                }
                
                return video_info
                
                

            except Exception as e:
                raise Exception(f"Failed to get video info : {str(e)}")
    
    '''
    get_transcript function : Extract language and transcript url from automatic_captions
    Input: info of the video
    Output: None or dict(transcript_url,language)
    '''
    def get_transcript(self, info):
        
        try:
            # get automatic_captions
            automatic_captions = info.get('automatic_captions', None)
            if not automatic_captions:
                raise Exception(f"automatic captions not found")
            
            # search original language in automatic_captions
            language = next((k for k in automatic_captions if "-orig" in k), None)
            if not language:
                raise Exception(f"original language not found")
            
            # get transcript for automatic_captions
            transcript = automatic_captions.get(language, None)
            if not transcript:
                raise Exception(f"original language transcript not found")
            
            # get transcript url for automatic_captions
            transcript_url = transcript[0].get('url')
            if not transcript_url:
                raise Exception(f"original language transcript url not found")
            
            transcript_url = transcript_url.replace("&fmt=json3", "")
            language = language.replace("-orig", "")
            
            return {
                "transcript_url" : transcript_url,
                "language": language
            }
        
        except Exception as e:
            self.logger.error(f"Transcript URL video: {self.video}, Message: {str(e)}")
            return None

    '''
    download_transcript function : Download the transcript for url
    Input: transcript_url
    Output: transcript as String
    '''
    async def download_transcript(self, transcript_url):
        # define the retries and delay between retry
        retries = 3
        base_delay = 5
        
        # try block
        try:
            
            # custom header for xml content
            ua = UserAgent(platforms='mobile')
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'user-agent': ua.random,
            }

            # create curl session
            session = AsyncSession(
                impersonate="chrome120"
            )
            
            # add header to session
            session.headers.update(headers)

            proxies = {
                "http": "http://sscraperapi:c353f5398edc75d4e3ed264703fc4a5d@proxy-server.scraperapi.com:8001",
                "https": "http://sscraperapi:c353f5398edc75d4e3ed264703fc4a5d@proxy-server.scraperapi.com:8001"
            }
            
            
            # start retries
            for i in range(retries):
                self.logger.info(f"Download Transcript video: {self.video}, Message: retry {i+1}")
                try:
                    # if it is the third retry use the proxy, else use simple request
                    response = await session.get(transcript_url, timeout=30, proxies=proxies, verify=False)

                    # raise for erros
                    response.raise_for_status()

                    # parse the reponse as XML
                    full_text = self.clean_transcript(response.text)
                    
                    return full_text
                except Exception as e:
                    self.logger.warning(f"Download Transcript video: {self.video}, Message: retry {i+1} Failed {str(e)}")
                    # if number of retries reached return None
                    if i == retries - 1: 
                        raise Exception(f"Extracting Transcript failed {retries} times, {str(e)}")
                    
                    # if not, delay an exponential backoff time
                    wait_time = (base_delay * (i + 1)) + random.uniform(2, 7)
                    await asyncio.sleep(wait_time)
                    continue
        
        # if any error happen print the error in log and return None
        except Exception as e:
            self.logger.error(f"Transcript video: {self.video}, Message: {str(e)}")
            return None
        
        # close curl session
        finally:
            if 'session' in locals():
                await session.close()
            
    '''
    clean_transcript function : Parse the XML, clean ,and extract transcript
    Input: xml_response
    Output: cleaned transcript as String
    '''
    def clean_transcript(self, xml_response):
        try:

            # test if response is a valid string and xml
            if not xml_response:
                raise Exception(f"Transcript response is empty")
            
            
            # Parse the XML string
            try:
                root = ET.fromstring(xml_response)
            except Exception as e:
                raise Exception(f"Transcript response not a valid XML")
            
            
            # Extract all text from <text> tags and join them
            raw_text = " ".join([elem.text for elem in root.findall('text') if elem.text])
            
            # 1. Remove text between square brackets e.g., [موسيقى]
            # 2. Remove special characters like >>
            # 3. Clean up extra whitespace/newlines
            cleaned = re.sub(r'\[.*?\]', '', raw_text)
            cleaned = re.sub(r'[<>&>]', '', cleaned)
            cleaned = re.sub(r'gt;', '', cleaned)
            cleaned = " ".join(cleaned.split())
            
            return cleaned
        except Exception as e:
            raise Exception(f"Cleaning Transcript : {str(e)}")
        
