-- LLM usage log for cost tracking (idempotent)
CREATE TABLE IF NOT EXISTS llm_usage (
  id            BIGSERIAL PRIMARY KEY,
  message_id    TEXT,
  model         TEXT NOT NULL,
  in_tokens     INT DEFAULT 0,
  out_tokens    INT DEFAULT 0,
  cost_usd      NUMERIC(10,6) DEFAULT 0,
  was_signal    BOOLEAN,
  error         TEXT,
  called_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_llm_called ON llm_usage(called_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_model  ON llm_usage(model);

-- Daily rollup view
CREATE OR REPLACE VIEW v_llm_daily_cost AS
SELECT
  DATE_TRUNC('day', called_at)::date AS day,
  model,
  COUNT(*)                AS calls,
  SUM(in_tokens)          AS in_tokens,
  SUM(out_tokens)         AS out_tokens,
  ROUND(SUM(cost_usd)::numeric, 6) AS cost_usd,
  COUNT(*) FILTER (WHERE was_signal) AS signals_extracted,
  COUNT(*) FILTER (WHERE error IS NOT NULL) AS errors
FROM llm_usage
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

-- Monthly total
CREATE OR REPLACE VIEW v_llm_monthly_cost AS
SELECT
  DATE_TRUNC('month', called_at)::date AS month,
  COUNT(*)   AS calls,
  ROUND(SUM(cost_usd)::numeric, 4) AS cost_usd
FROM llm_usage
GROUP BY 1
ORDER BY 1 DESC;
