from supabase import create_client, Client
from dotenv import load_dotenv
import os

class SupabaseClient:
    
    def __init__(self, logger):
        self.logger = logger
        
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        # verify if credentials are available
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    
    def store_data(self, table_name, records):
        if not records:
            return
        
        BATCH_SIZE = 100

        for i in range(0, len(records), BATCH_SIZE):

            batch = records[i:i + BATCH_SIZE]

            try:
                self.supabase.table(
                    table_name
                ).insert(batch).execute()

                self.logger.info(f"Inserted batch {i}-{i+len(batch)}")

            except Exception as e:
                self.logger.error(f"Insert error: {e}")
    
    def read_data(self, table_name):
        try:
            records = self.supabase.table(table_name).select("*").execute()
            return records
        except Exception as e:
                self.logger.error(f"Select error: {e}")
                return None