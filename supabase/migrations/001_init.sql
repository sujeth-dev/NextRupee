-- NextRupee initial schema (Master Doc §3). profiles is append-only: never UPDATE.

create table if not exists profiles (
  id uuid primary key default gen_random_uuid(),
  session_id text not null,
  version int not null,
  monthly_income numeric not null,
  monthly_expenses numeric not null,
  cash_savings numeric not null,
  hi_debt_amount numeric not null default 0,
  hi_debt_apr numeric not null default 0,
  dependents boolean not null default false,
  term_insurance boolean not null default false,
  risk_tolerance text not null default 'medium',
  goals jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique (session_id, version)
);

create index if not exists idx_profiles_session on profiles (session_id, version desc);

create table if not exists nbca_log (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references profiles (id),
  rank int not null,
  nbca jsonb not null,
  model text not null,
  prompt_version text not null,
  engine_data_asof date,
  created_at timestamptz not null default now()
);

create index if not exists idx_nbca_log_profile on nbca_log (profile_id, created_at desc);

create table if not exists eval_runs (
  id uuid primary key default gen_random_uuid(),
  git_sha text not null,
  tier text not null,
  metrics jsonb not null,
  created_at timestamptz not null default now()
);

-- Enforce append-only profiles at the database level.
create or replace function forbid_profile_mutation() returns trigger as $$
begin
  raise exception 'profiles is append-only';
end;
$$ language plpgsql;

drop trigger if exists trg_profiles_no_update on profiles;
create trigger trg_profiles_no_update
  before update or delete on profiles
  for each row execute function forbid_profile_mutation();
