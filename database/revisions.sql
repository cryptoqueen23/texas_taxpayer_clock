CREATE TABLE IF NOT EXISTS source_versions (
 version_id VARCHAR PRIMARY KEY, source_id VARCHAR NOT NULL REFERENCES sources(source_id),
 sha256 VARCHAR NOT NULL, retrieved_at TIMESTAMP NOT NULL, reporting_period VARCHAR NOT NULL,
 UNIQUE(source_id,sha256,reporting_period)
);
CREATE TABLE IF NOT EXISTS observation_revisions (
 revision_id VARCHAR PRIMARY KEY, version_id VARCHAR NOT NULL REFERENCES source_versions(version_id),
 government_id VARCHAR NOT NULL REFERENCES governments(government_id), metric VARCHAR NOT NULL,
 period VARCHAR NOT NULL, amount DECIMAL(24,2), unit VARCHAR NOT NULL,
 status VARCHAR NOT NULL CHECK(status IN ('reported','provisional','unavailable')),
 CHECK((status='unavailable' AND amount IS NULL) OR (status<>'unavailable' AND amount IS NOT NULL)),
 UNIQUE(version_id,government_id,metric,period)
);
CREATE TABLE IF NOT EXISTS discrepancies (
 discrepancy_id VARCHAR PRIMARY KEY, metric VARCHAR NOT NULL, period VARCHAR NOT NULL,
 source_a VARCHAR, source_b VARCHAR, difference DECIMAL(24,2), description VARCHAR NOT NULL,
 status VARCHAR NOT NULL CHECK(status IN ('open','resolved','accepted_with_note'))
);
CREATE TABLE IF NOT EXISTS publication_reviews (
 review_id VARCHAR PRIMARY KEY, version_id VARCHAR NOT NULL REFERENCES source_versions(version_id),
 decision VARCHAR NOT NULL CHECK(decision IN ('pending','approved','blocked')),
 reviewed_at TIMESTAMP, rationale VARCHAR NOT NULL
);
