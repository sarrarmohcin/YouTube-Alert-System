/* enable extensions */
create extension if not exists "pg_net" with schema "extensions";
create extension if not exists "pg_cron" with schema "extensions";

/* add cron job */
select cron.schedule(
  'video_keyword_scan',
  '*/10 * * * *',
  $$
  select net.http_post(
    url := 'EDGE_FUNCTION_URL',
    headers := jsonb_build_object(
      'Content-Type', 'application/json'
    ),
    body := '{}'::jsonb
  );
  $$
);