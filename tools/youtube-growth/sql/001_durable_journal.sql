-- Run once on the reviewed database, with a backup, before enabling writes.
CREATE TABLE youtube_operations (
    id text PRIMARY KEY,
    kind text NOT NULL,
    payload jsonb NOT NULL,
    status text NOT NULL CHECK (status IN ('started', 'complete')),
    result jsonb,
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE youtube_poll_state (
    channel_id text PRIMARY KEY,
    payload jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
