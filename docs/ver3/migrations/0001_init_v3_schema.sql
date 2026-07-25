-- 0001_init_v3_schema.sql — Sprint V3.2
-- Hien thuc hoa V3_DATA_MODEL.md (Sprint V3.1) thanh migration THAT cho
-- SQLite (uu tien SQLite truoc theo dung V3_DATA_MODEL.md muc 8 "Migration
-- Strategy": khong can ha tang them, phu hop Render free tier). Duoc doc va
-- thuc thi boi v3/db.py qua conn.executescript() - day la NGUON SU THAT DUY
-- NHAT cua schema, khong dinh nghia lai o noi khac.
--
-- Khong dung AUTOINCREMENT - id la TEXT (uuid4 hex), dung nguyen pattern
-- job_id cua engine/jobs.py (Ver 2) de nhat quan toan he thong.
-- Cot dang JSON (media_urls, hashtags, rows, config...) luu duoi dang TEXT
-- (json.dumps) - SQLite khong co kieu JSON native, ung dung tu serialize/
-- deserialize o v3/repository.py.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS research_projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    objective       TEXT,
    date_range_days INTEGER NOT NULL DEFAULT 90,
    content_limit   INTEGER NOT NULL DEFAULT 30,
    notes           TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS brands (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    brand_type      TEXT NOT NULL CHECK (brand_type IN ('linkpower', 'competitor')),
    notes           TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_brands_project ON brands(project_id);

CREATE TABLE IF NOT EXISTS social_channels (
    id                   TEXT PRIMARY KEY,
    brand_id             TEXT NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    project_id           TEXT NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    platform             TEXT NOT NULL CHECK (platform IN ('facebook', 'linkedin', 'tiktok', 'youtube')),
    source_url           TEXT NOT NULL,
    normalized_url        TEXT NOT NULL,
    external_channel_id   TEXT,
    created_at             TEXT NOT NULL,
    -- URL trung trong CUNG 1 project (bat ke thuong hieu nao) bi chan -
    -- V3_PRODUCT_REQUIREMENTS.md FR3.
    UNIQUE (project_id, normalized_url)
);
CREATE INDEX IF NOT EXISTS idx_channels_brand ON social_channels(brand_id);
CREATE INDEX IF NOT EXISTS idx_channels_project_platform ON social_channels(project_id, platform);

CREATE TABLE IF NOT EXISTS collection_jobs (
    id               TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    channel_id       TEXT NOT NULL REFERENCES social_channels(id) ON DELETE CASCADE,
    status           TEXT NOT NULL DEFAULT 'pending' CHECK (
                         status IN (
                             'pending', 'validating', 'collecting', 'normalizing',
                             'analyzing', 'benchmarking', 'collected',
                             'partially_collected', 'failed',
                             'requires_manual_input', 'completed'
                         )
                     ),
    provider         TEXT,
    posts_requested  INTEGER,
    posts_collected  INTEGER,
    error_reason     TEXT,
    started_at       TEXT,
    finished_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_channel ON collection_jobs(channel_id);
CREATE INDEX IF NOT EXISTS idx_jobs_run ON collection_jobs(run_id);

CREATE TABLE IF NOT EXISTS raw_items (
    id                  TEXT PRIMARY KEY,
    collection_job_id   TEXT NOT NULL REFERENCES collection_jobs(id) ON DELETE CASCADE,
    item_type           TEXT NOT NULL CHECK (item_type IN ('profile', 'post')),
    raw_payload         TEXT NOT NULL,
    collected_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_raw_items_job ON raw_items(collection_job_id);

CREATE TABLE IF NOT EXISTS normalized_items (
    id                              TEXT PRIMARY KEY,
    raw_item_id                     TEXT REFERENCES raw_items(id) ON DELETE SET NULL,
    project_id                      TEXT NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    brand_id                        TEXT NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    channel_id                      TEXT NOT NULL REFERENCES social_channels(id) ON DELETE CASCADE,
    platform                        TEXT NOT NULL,
    provider                        TEXT NOT NULL,
    source_url                      TEXT NOT NULL,
    external_content_id             TEXT NOT NULL,
    content_type                    TEXT,
    published_at                    TEXT,
    collected_at                    TEXT NOT NULL,
    author_name                     TEXT,
    author_url                      TEXT,
    title                           TEXT,
    text_content                    TEXT,
    description                     TEXT,
    media_urls                      TEXT,
    thumbnail_url                   TEXT,
    video_duration                  INTEGER,
    hashtags                        TEXT,
    mentions                        TEXT,
    external_links                  TEXT,
    cta_text                        TEXT,
    language                        TEXT,
    view_count                      INTEGER,
    like_count                      INTEGER,
    reaction_count                  INTEGER,
    comment_count                   INTEGER,
    share_count                     INTEGER,
    save_count                      INTEGER,
    follower_count_at_collection    INTEGER,
    engagement_count                INTEGER,
    engagement_rate                 REAL,
    raw_payload_ref                 TEXT,
    data_quality_score              TEXT,
    collection_status               TEXT,
    created_at                      TEXT NOT NULL,
    updated_at                      TEXT NOT NULL,
    -- Idempotent theo (channel, external_content_id) - V3_DATA_MODEL.md muc 5.
    UNIQUE (channel_id, external_content_id)
);
CREATE INDEX IF NOT EXISTS idx_norm_items_channel_published ON normalized_items(channel_id, published_at);
CREATE INDEX IF NOT EXISTS idx_norm_items_project_platform ON normalized_items(project_id, platform);

CREATE TABLE IF NOT EXISTS content_classifications (
    id                        TEXT PRIMARY KEY,
    normalized_item_id        TEXT NOT NULL REFERENCES normalized_items(id) ON DELETE CASCADE,
    content_pillar            TEXT,
    funnel_stage               TEXT,
    content_intent              TEXT,
    format                       TEXT,
    primary_message              TEXT,
    target_audience               TEXT,
    pain_point                     TEXT,
    benefit                         TEXT,
    cta_type                         TEXT,
    tone_of_voice                     TEXT,
    product_mentioned                  TEXT,
    classified_by                       TEXT NOT NULL CHECK (classified_by IN ('ai', 'rule_fallback')),
    confidence                           REAL,
    created_at                            TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_classification_item ON content_classifications(normalized_item_id);

CREATE TABLE IF NOT EXISTS metric_results (
    id                TEXT PRIMARY KEY,
    project_id        TEXT NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    channel_id        TEXT NOT NULL REFERENCES social_channels(id) ON DELETE CASCADE,
    metric_key        TEXT NOT NULL,
    metric_value       REAL,
    unit                TEXT,
    time_window          TEXT,
    formula_version       TEXT NOT NULL DEFAULT '1.0.0',
    computed_at            TEXT NOT NULL,
    UNIQUE (channel_id, metric_key, time_window, formula_version)
);
CREATE INDEX IF NOT EXISTS idx_metrics_project ON metric_results(project_id);

CREATE TABLE IF NOT EXISTS benchmark_runs (
    id             TEXT PRIMARY KEY,
    project_id     TEXT NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    status         TEXT NOT NULL DEFAULT 'pending',
    config         TEXT,
    started_at     TEXT,
    completed_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_bench_runs_project ON benchmark_runs(project_id);

CREATE TABLE IF NOT EXISTS benchmark_results (
    id                       TEXT PRIMARY KEY,
    benchmark_run_id         TEXT NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,
    linkpower_channel_id     TEXT REFERENCES social_channels(id) ON DELETE CASCADE,
    competitor_channel_id    TEXT REFERENCES social_channels(id) ON DELETE CASCADE,
    comparison_scope         TEXT NOT NULL CHECK (comparison_scope IN ('one_vs_one', 'one_vs_group')),
    rows                     TEXT,
    overall_status           TEXT,
    confidence_score         TEXT,
    created_at               TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bench_results_run ON benchmark_results(benchmark_run_id);

CREATE TABLE IF NOT EXISTS ai_insights (
    id                  TEXT PRIMARY KEY,
    benchmark_run_id    TEXT NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,
    insight_type        TEXT NOT NULL,
    payload             TEXT,
    generated_by        TEXT NOT NULL CHECK (generated_by IN ('ai', 'rule_fallback')),
    created_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_insights_run ON ai_insights(benchmark_run_id);

CREATE TABLE IF NOT EXISTS reports (
    id                  TEXT PRIMARY KEY,
    benchmark_run_id    TEXT NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,
    project_id          TEXT NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    version             INTEGER NOT NULL DEFAULT 1,
    summary             TEXT,
    full_report         TEXT NOT NULL,
    generated_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reports_project ON reports(project_id, generated_at);

CREATE TABLE IF NOT EXISTS import_batches (
    id            TEXT PRIMARY KEY,
    channel_id    TEXT NOT NULL REFERENCES social_channels(id) ON DELETE CASCADE,
    platform      TEXT NOT NULL,
    filename      TEXT NOT NULL,
    file_format   TEXT NOT NULL CHECK (file_format IN ('csv', 'json')),
    row_count     INTEGER NOT NULL,
    imported_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_import_batches_channel ON import_batches(channel_id);
