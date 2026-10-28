-- Schéma initial du noyau serveur. Ne jamais modifier ce fichier une fois appliqué :
-- le démarrage échoue si son empreinte change. Toute évolution passe par une nouvelle migration.

create table users (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  display_name text not null check (length(display_name) between 1 and 120),
  password_hash text not null,
  disabled boolean not null default false,
  created_at timestamptz not null default now(),
  constraint users_email_lowercase check (email = lower(email)),
  constraint users_email_shape check (email ~ '^[^@\s]+@[^@\s]+$')
);
create unique index users_email_unique on users (email);

create table sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users (id) on delete cascade,
  token_hash text not null unique,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  revoked_at timestamptz
);
create index sessions_user on sessions (user_id);

create table login_failures (
  email text primary key,
  failures integer not null default 0,
  locked_until timestamptz
);

create table podcasts (
  id uuid primary key default gen_random_uuid(),
  name text not null check (length(name) between 1 and 200),
  created_by uuid not null references users (id),
  created_at timestamptz not null default now()
);

create table memberships (
  podcast_id uuid not null references podcasts (id) on delete cascade,
  user_id uuid not null references users (id) on delete cascade,
  role text not null check (role in ('ADMIN', 'PRODUCER', 'HOST', 'EDITOR', 'VIEWER')),
  created_at timestamptz not null default now(),
  primary key (podcast_id, user_id)
);
create index memberships_user on memberships (user_id);

-- Catalogues versionnés d'un podcast : on ajoute des versions, on n'en modifie jamais.
create table templates (
  podcast_id uuid not null references podcasts (id) on delete cascade,
  id text not null,
  version integer not null check (version >= 1),
  body jsonb not null,
  created_at timestamptz not null default now(),
  primary key (podcast_id, id, version)
);
create table assets (
  podcast_id uuid not null references podcasts (id) on delete cascade,
  id text not null,
  version integer not null check (version >= 1),
  meta jsonb not null default '{}',
  created_at timestamptz not null default now(),
  primary key (podcast_id, id, version)
);
create table themes (
  podcast_id uuid not null references podcasts (id) on delete cascade,
  id text not null,
  version integer not null check (version >= 1),
  meta jsonb not null default '{}',
  created_at timestamptz not null default now(),
  primary key (podcast_id, id, version)
);

create table episodes (
  id uuid primary key,
  podcast_id uuid not null references podcasts (id) on delete cascade,
  title text not null,
  episode_date date not null,
  workspace jsonb not null,
  revision integer not null check (revision >= 1),
  created_at timestamptz not null default now()
);
create index episodes_podcast on episodes (podcast_id, created_at);

create table episode_idempotency (
  podcast_id uuid not null references podcasts (id) on delete cascade,
  idempotency_key text not null,
  fingerprint text not null,
  episode_id uuid not null references episodes (id) on delete cascade,
  primary key (podcast_id, idempotency_key)
);

-- Régie : état courant, journal d'événements, résultats de commandes (idempotence).
create table studios (
  episode_id uuid primary key references episodes (id) on delete cascade,
  state jsonb not null,
  version integer not null
);
create table studio_events (
  episode_id uuid not null references episodes (id) on delete cascade,
  seq integer not null,
  event jsonb not null,
  primary key (episode_id, seq)
);
create table studio_commands (
  episode_id uuid not null references episodes (id) on delete cascade,
  command_id text not null,
  result jsonb not null,
  events jsonb not null,
  primary key (episode_id, command_id)
);

create table invitations (
  id uuid primary key default gen_random_uuid(),
  podcast_id uuid not null references podcasts (id) on delete cascade,
  episode_id uuid not null references episodes (id) on delete cascade,
  role text not null check (role in ('GUEST', 'HOST')),
  token_hash text not null unique,
  display_name text check (display_name is null or length(display_name) between 1 and 120),
  created_by uuid not null references users (id),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  used_at timestamptz,
  revoked_at timestamptz
);

-- Un participant : son identifiant est l'identité LiveKit, attribuée par le serveur.
create table participants (
  id uuid primary key default gen_random_uuid(),
  episode_id uuid not null references episodes (id) on delete cascade,
  user_id uuid references users (id),
  invitation_id uuid references invitations (id),
  display_name text not null check (length(display_name) between 1 and 120),
  role text not null check (role in ('ADMIN', 'PRODUCER', 'HOST', 'GUEST')),
  created_at timestamptz not null default now()
);
create index participants_episode on participants (episode_id);

-- Journal d'audit : ajout seul.
create table audit_log (
  id bigserial primary key,
  at timestamptz not null default now(),
  actor_user_id uuid,
  actor_kind text not null,
  podcast_id uuid,
  action text not null,
  target text not null,
  result text not null,
  correlation_id text not null,
  detail jsonb not null default '{}'
);
create index audit_podcast on audit_log (podcast_id, at);

create function audit_log_append_only() returns trigger language plpgsql as $$
begin
  raise exception 'audit_log est en ajout seul';
end;
$$;
create trigger audit_log_no_update before update or delete on audit_log
  for each row execute function audit_log_append_only();
create trigger audit_log_no_truncate before truncate on audit_log
  for each statement execute function audit_log_append_only();
