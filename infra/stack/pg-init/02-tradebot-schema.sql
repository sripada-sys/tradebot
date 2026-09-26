-- Tradebot Phase 1 schema (idempotent)
CREATE TABLE IF NOT EXISTS signals (
  id              BIGSERIAL PRIMARY KEY,
  source_group    TEXT NOT NULL,
  group_jid       TEXT NOT NULL,
  message_id      TEXT NOT NULL UNIQUE,
  sender_jid      TEXT,
  raw_text        TEXT NOT NULL,
  trade_type      TEXT,
  stock_name_raw  TEXT,
  nse_symbol      TEXT,
  entry_price     NUMERIC(12,2),
  stop_loss       NUMERIC(12,2),
  targets         NUMERIC(12,2)[],
  targets_mode    TEXT,
  extractor       TEXT NOT NULL DEFAULT 'regex',
  confidence      NUMERIC(3,2),
  posted_at       TIMESTAMPTZ NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_signals_posted ON signals(posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(nse_symbol);
CREATE INDEX IF NOT EXISTS idx_signals_group  ON signals(group_jid);

CREATE TABLE IF NOT EXISTS raw_messages (
  message_id   TEXT PRIMARY KEY,
  group_jid    TEXT NOT NULL,
  sender_jid   TEXT,
  body         TEXT,
  posted_at    TIMESTAMPTZ NOT NULL,
  received_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_raw_group ON raw_messages(group_jid, posted_at DESC);

CREATE TABLE IF NOT EXISTS symbols (
  stock_name_raw TEXT PRIMARY KEY,
  nse_symbol     TEXT NOT NULL,
  occurrences    INT DEFAULT 0,
  verified       BOOLEAN DEFAULT FALSE,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);
