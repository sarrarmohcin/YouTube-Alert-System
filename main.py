import logging
import asyncio

from app.youtubeChannelController import youtubeChannelController
from app.youtubeVideoController import youtubeVideoController
from database.supabaseClient import SupabaseClient
from app.analyzer import VideoAnalyzer

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("youtube_extractor.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("youtubeExtractor")
    
    # read sources
    supabase_client = SupabaseClient(logger)
    response = supabase_client.read_data('yt_sources')
    
    if not response:
        logger.error('Failed to read sources')
        exit(0)
        
        
    sources = response.data

    for source in sources:
        # get videos
        scraper = youtubeChannelController(source, logger)
        videos = asyncio.run(scraper.start())
        
        records = []
        # get videos info
        for video in videos[:5]:
            scraper = youtubeVideoController(video, logger)
            video_info = asyncio.run(scraper.start())
            records.append(video_info)
            
        # analyze videos
        analyzer = VideoAnalyzer()
        for rec in records:
            if rec['content']:
                summary = analyzer.inference(rec['content'])
                rec['summary'] = summary
            else:
                rec['summary'] = ""
            

        # store data
        supabase_client.store_data("yt_videos", records)
    