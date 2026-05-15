from groq import Groq
from dotenv import load_dotenv
import os


class VideoAnalyzer:
    
    SYSTEM_PROMPT = """
        You are an expert summarization model. 
        Your task is to read a video transcript and produce a clear, concise, and accurate summary of its content.

        Rules:
        - Output ONLY the summary. No explanations, no titles, no preambles.
        - Do not repeat or quote large parts of the transcript.
        - Do not add opinions, commentary, or extra information not present in the transcript.
        - Keep the summary structured, coherent, and easy to understand.
        - Preserve important facts, key ideas, and main conclusions.
        - If the transcript is long, compress it into the most important points while maintaining meaning.
        - Write in a neutral, informative tone.
        - use arround 50 words

        Output format:

        Return a single block of text containing only the summary.
    """

    def __init__(self, logger):
        self.logger = logger
        self.client = None
        
        
        load_dotenv()
        grop_key = os.getenv("GROQ_KEY")

        # verify if credentials are available
        if not grop_key:
            self.logger.warning("GROQ API key not found. The generated summary may be unavailable or empty.")
            return None
        
        self.client = Groq(
            api_key=grop_key,
        )
    
    def inference(self, transcript_text):
        
        if not self.client:
            return ''
        
        try:
            USER_PROMPT = f"""
                Analyze this transcript:

                {transcript_text}
            """

            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": USER_PROMPT
                    }
                ]
            )

            content = response.choices[0].message.content

            return content
        except Exception as e:
            return ""


