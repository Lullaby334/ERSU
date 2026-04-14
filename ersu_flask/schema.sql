-- ERSU schema for Supabase SQL Editor
-- Paste this whole file into SQL Editor and run it once.

create extension if not exists btree_gist;

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create table if not exists public.users (
  id bigserial primary key,
  full_name varchar(150) not null,
  email varchar(255) not null unique,
  password_hash varchar(255) not null,
  role varchar(30) not null default 'STUDENT'
    check (role in ('STUDENT', 'EMPLOYEE', 'LAB_STAFF', 'ADMIN')),
  is_active_account boolean not null default true,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now()
);

create table if not exists public.equipment (
  id bigserial primary key,
  name varchar(150) not null,
  category varchar(100) not null,
  laboratory varchar(120) not null,
  serial_number varchar(120) not null unique,
  description text,
  image_url varchar(500),
  status varchar(30) not null default 'AVAILABLE'
    check (status in ('AVAILABLE', 'RESERVED', 'LOANED', 'OUT_OF_SERVICE')),
  created_at timestamp not null default now(),
  updated_at timestamp not null default now()
);

create table if not exists public.reservations (
  id bigserial primary key,
  user_id bigint not null references public.users(id) on delete cascade,
  equipment_id bigint not null references public.equipment(id) on delete cascade,
  start_at timestamp not null,
  end_at timestamp not null,
  purpose varchar(255),
  status varchar(30) not null default 'PENDING'
    check (status in ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', 'EXPIRED')),
  decision_note varchar(255),
  approved_by_id bigint references public.users(id) on delete set null,
  created_at timestamp not null default now(),
  updated_at timestamp not null default now(),
  check (end_at > start_at)
);

create table if not exists public.loans (
  id bigserial primary key,
  reservation_id bigint not null unique references public.reservations(id) on delete cascade,
  equipment_id bigint not null references public.equipment(id) on delete cascade,
  checked_out_by_id bigint not null references public.users(id) on delete restrict,
  checked_in_by_id bigint references public.users(id) on delete set null,
  check_out_at timestamp not null default now(),
  check_in_at timestamp,
  due_at timestamp not null,
  condition_note text,
  created_at timestamp not null default now()
);

create table if not exists public.notifications (
  id bigserial primary key,
  user_id bigint not null references public.users(id) on delete cascade,
  title varchar(150) not null,
  message text not null,
  channel varchar(30) not null default 'IN_APP',
  is_read boolean not null default false,
  created_at timestamp not null default now()
);

create table if not exists public.audit_logs (
  id bigserial primary key,
  actor_id bigint references public.users(id) on delete set null,
  action varchar(100) not null,
  target_type varchar(50) not null,
  target_id bigint,
  details text,
  created_at timestamp not null default now()
);

create index if not exists idx_users_email on public.users(email);
create index if not exists idx_equipment_status on public.equipment(status);
create index if not exists idx_reservations_equipment on public.reservations(equipment_id);
create index if not exists idx_reservations_user on public.reservations(user_id);
create index if not exists idx_reservations_status on public.reservations(status);
create index if not exists idx_reservations_period on public.reservations(start_at, end_at);
create index if not exists idx_loans_equipment on public.loans(equipment_id);
create index if not exists idx_loans_due_at on public.loans(due_at);
create index if not exists idx_notifications_user on public.notifications(user_id, created_at desc);
create index if not exists idx_audit_logs_actor on public.audit_logs(actor_id, created_at desc);

-- Protect from overlapping active reservations for the same equipment.
do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'no_overlap_active_reservations'
  ) then
    alter table public.reservations
      add constraint no_overlap_active_reservations
      exclude using gist (
        equipment_id with =,
        tsrange(start_at, end_at, '[)') with &&
      )
      where (status in ('PENDING', 'APPROVED'));
  end if;
end $$;

-- Keep timestamps fresh.
drop trigger if exists trg_users_updated_at on public.users;
create trigger trg_users_updated_at
before update on public.users
for each row execute function set_updated_at();

drop trigger if exists trg_equipment_updated_at on public.equipment;
create trigger trg_equipment_updated_at
before update on public.equipment
for each row execute function set_updated_at();

drop trigger if exists trg_reservations_updated_at on public.reservations;
create trigger trg_reservations_updated_at
before update on public.reservations
for each row execute function set_updated_at();
