CREATE TABLE yt_sources (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE yt_videos (
    id BIGSERIAL PRIMARY KEY,

    source_id TEXT NOT NULL,
    source_name TEXT,
    source_url TEXT,

    title TEXT,
    content TEXT,
    url TEXT UNIQUE,
    media TEXT,
    lang TEXT,
    summary TEXT,

    published_date BIGINT,
    extracted_date BIGINT,

    interactions JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE alert_keywords (
    id BIGSERIAL PRIMARY KEY,
    keyword TEXT NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);