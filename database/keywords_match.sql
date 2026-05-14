CREATE OR REPLACE FUNCTION get_keyword_matches()
RETURNS TABLE (
  video_id BIGINT,
  video_title TEXT,
  video_url TEXT,
  matched_keyword TEXT,
  media TEXT,
  summary TEXT,
  source_name TEXT
)
AS $$
  WITH candidates AS (
    SELECT
      v.id AS video_id,
      v.title AS video_title,
      v.url AS video_url,
      k.keyword AS matched_keyword,
      v.media,
      v.summary,
      v.source_name
    FROM yt_videos v
    JOIN alert_keywords k
      ON k.is_active = TRUE
    WHERE v.published_date >= EXTRACT(EPOCH FROM NOW() - INTERVAL '6 hour')
      AND (
        v.title ILIKE '%' || k.keyword || '%'
        OR v.content ILIKE '%' || k.keyword || '%'
      )
  ),

  inserted AS (
    INSERT INTO video_keyword_alerts (video_id, keyword)
    SELECT
      c.video_id,
      c.matched_keyword
    FROM candidates c
    ON CONFLICT DO NOTHING
    RETURNING video_id, keyword
  )

  SELECT DISTINCT
    c.video_id,
    c.video_title,
    c.video_url,
    c.matched_keyword,
    c.media,
    c.summary,
    c.source_name
  FROM candidates c
  JOIN inserted i
    ON i.video_id = c.video_id
   AND i.keyword = c.matched_keyword
  ORDER BY c.video_id DESC;

$$ LANGUAGE sql;