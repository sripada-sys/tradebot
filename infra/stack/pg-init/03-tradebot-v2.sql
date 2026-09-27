-- Tradebot Phase 1.5 additions (idempotent)
-- Adds: latency tracking, LLM extractor support, market context, edit history

-- 1. Extend signals table
ALTER TABLE signals ADD COLUMN IF NOT EXISTS received_at    TIMESTAMPTZ;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS processed_at   TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE signals ADD COLUMN IF NOT EXISTS llm_raw        JSONB;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS llm_model      TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS media_url      TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS is_edit        BOOLEAN DEFAULT FALSE;

-- 2. Extend raw_messages with received/processed timestamps and media info
ALTER TABLE raw_messages ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE raw_messages ADD COLUMN IF NOT EXISTS message_type TEXT DEFAULT 'text';
ALTER TABLE raw_messages ADD COLUMN IF NOT EXISTS media_url    TEXT;
ALTER TABLE raw_messages ADD COLUMN IF NOT EXISTS is_edit      BOOLEAN DEFAULT FALSE;

-- 3. Market context table (populated by Fyers integration later; nullable now)
CREATE TABLE IF NOT EXISTS signals_market_context (
  id                    BIGSERIAL PRIMARY KEY,
  signal_id             BIGINT REFERENCES signals(id) ON DELETE CASCADE,
  nse_symbol            TEXT,
  price_at_message      NUMERIC(12,2),
  price_at_capture      NUMERIC(12,2),
  advisor_entry         NUMERIC(12,2),
  slippage_pct          NUMERIC(6,3),
  latency_seconds       INT,
  captured_at           TIMESTAMPTZ DEFAULT NOW(),
  source                TEXT DEFAULT 'pending'  -- 'fyers', 'pending', 'unavailable'
);
CREATE INDEX IF NOT EXISTS idx_mkt_ctx_signal ON signals_market_context(signal_id);
CREATE INDEX IF NOT EXISTS idx_mkt_ctx_symbol ON signals_market_context(nse_symbol);

-- 4. Message edit history (for MESSAGES_UPDATE events)
CREATE TABLE IF NOT EXISTS message_edits (
  id           BIGSERIAL PRIMARY KEY,
  message_id   TEXT NOT NULL,
  group_jid    TEXT NOT NULL,
  old_body     TEXT,
  new_body     TEXT,
  edited_at    TIMESTAMPTZ NOT NULL,
  captured_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_edits_msg ON message_edits(message_id);

-- 5. Confidence scoring lookup (for reference / future tuning)
CREATE TABLE IF NOT EXISTS extractor_confidence (
  extractor   TEXT PRIMARY KEY,
  base_score  NUMERIC(3,2) NOT NULL,
  notes       TEXT
);
INSERT INTO extractor_confidence(extractor, base_score, notes) VALUES
  ('regex',  0.90, 'High confidence — strict pattern match'),
  ('llm',    0.70, 'Medium confidence — LLM inference, needs review'),
  ('manual', 1.00, 'Human verified')
ON CONFLICT (extractor) DO NOTHING;

-- 6. Convenience view: signals with latency + market context
CREATE OR REPLACE VIEW v_signals_enriched AS
SELECT
  s.id, s.source_group, s.nse_symbol, s.trade_type,
  s.entry_price, s.stop_loss, s.targets, s.extractor, s.confidence,
  s.posted_at, s.received_at, s.processed_at,
  EXTRACT(EPOCH FROM (s.received_at - s.posted_at))::INT AS delivery_lag_s,
  EXTRACT(EPOCH FROM (s.processed_at - s.received_at))::INT AS processing_lag_s,
  mc.price_at_message, mc.slippage_pct, mc.source AS market_source
FROM signals s
LEFT JOIN LATERAL (
  SELECT * FROM signals_market_context
  WHERE signal_id = s.id ORDER BY captured_at DESC LIMIT 1
) mc ON TRUE;
