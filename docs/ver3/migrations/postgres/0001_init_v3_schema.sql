-- 0001_init_v3_schema.sql (PostgreSQL) — Sprint V3.3.1
-- Ban PostgreSQL cua docs/ver3/migrations/0001_init_v3_schema.sql (SQLite,
-- Sprint V3.2) - CUNG 13 bang, CUNG ten cot, CUNG rang buoc logic nghiep vu
-- (UNIQUE, CHECK, FOREIGN KEY ON DELETE CASCADE/SET NULL) de v3/repository.py
-- va v3/services/* hoat dong KHONG SUA DOI khi doi backend (xem
-- docs/ver3/V3_DATABASE_MIGRATION_GUIDE.md muc "Khac biet dialect").
--
-- Duoc doc va thuc thi boi v3/db.py (executescript qua psycopg2, xem
-- _PGConnection.executescript) khi DATABASE_URL duoc dat - day la NGUON SU
-- THAT DUY NHAT cua schema PostgreSQL, khong dinh nghia lai o noi khac.
--
-- Khac biet co chu dich so voi ban SQLite (xem giai thich chi tiet trong
-- V3_DATABASE_MIGRATION_GUIDE.md):
--   1. Khong co "PRAGMA foreign_keys = ON" - PostgreSQL luon thuc thi FK,
--      khong co pragma tuong duong va cung khong can thiet.
--   2. REAL (SQLite = 8-byte double precision theo dac ta) -> DOUBLE PRECISION
--      (PostgreSQL REAL chi la 4-byte single precision) - tranh mat do chinh
--      xac khi tinh confidence/engagement_rate/metric_value.
--   3. Khong dung AUTOINCREMENT/SERIAL - id van la TEXT (uuid4 hex, sinh o
--      Python qua v3/repository.py:new_id()) - giu nguyen id lien tuc duoc
--      giua 2 backend (vd id sinh tu SQLite dev van hop le neu import sang
--      Postgres).
--   4. Cot JSON (media_urls, hashtags, rows, config, summary, full_report...)
--      VAN la TEXT (khong doi sang JSONB) - repository.py tu json.dumps/
--      json.loads o tang ung dung cho ca 2 backend, tranh phai viet 2 duong
--      serialize khac nhau (xem V3_DATABASE_MIGRATION_GUIDE.md ly do khong
--      dung JSONB o Sprint nay).
--   5. Khong co cot BOOLEAN nao trong schema hien tai (status dang TEXT enum
--      qua CHECK) nen khong phat sinh khac biet kieu boolean SQLite (0/1)
--      vs PostgreSQL (true/false) o Sprint nay.
--   6. Timestamp VAN la TEXT dang ISO-8601 ("%Y-%m-%dT%H:%M:%S", sinh boi
--      v3/repository.py:now_iso()) thay vi TIMESTAMP/TIMESTAMPTZ native -
--      giu dinh dang giong het SQLite de repository.py khong can nhanh
--      rieng cho tung backend.

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
    engagement_rate                 DOUBLE PRECISION,
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
    confidence                           DOUBLE PRECISION,
    created_at                            TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_classification_item ON content_classifications(normalized_item_id);

CREATE TABLE IF NOT EXISTS metric_results (
    id                TEXT PRIMARY KEY,
    project_id        TEXT NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    channel_id        TEXT NOT NULL REFERENCES social_channels(id) ON DELETE CASCADE,
    metric_key        TEXT NOT NULL,
    metric_value       DOUBLE PRECISION,
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
