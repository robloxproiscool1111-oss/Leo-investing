-- Run this once in the Supabase SQL Editor for this project.
-- The publishable key is safe for client use only because these policies restrict every row.

create table if not exists public.portfolio (
    user_id uuid not null references auth.users(id) on delete cascade,
    ticker text not null check (ticker = upper(ticker) and length(ticker) between 1 and 16),
    shares double precision not null check (shares > 0),
    avg_price double precision not null check (avg_price > 0),
    primary key (user_id, ticker)
);

create table if not exists public.watchlist (
    user_id uuid not null references auth.users(id) on delete cascade,
    ticker text not null check (ticker = upper(ticker) and length(ticker) between 1 and 16),
    primary key (user_id, ticker)
);

alter table public.portfolio enable row level security;
alter table public.watchlist enable row level security;

revoke all on table public.portfolio, public.watchlist from anon, authenticated;
grant select, insert, update, delete on table public.portfolio, public.watchlist to authenticated;

drop policy if exists "portfolio_select_own" on public.portfolio;
drop policy if exists "portfolio_insert_own" on public.portfolio;
drop policy if exists "portfolio_update_own" on public.portfolio;
drop policy if exists "portfolio_delete_own" on public.portfolio;
drop policy if exists "watchlist_select_own" on public.watchlist;
drop policy if exists "watchlist_insert_own" on public.watchlist;
drop policy if exists "watchlist_update_own" on public.watchlist;
drop policy if exists "watchlist_delete_own" on public.watchlist;

create policy "portfolio_select_own" on public.portfolio
    for select to authenticated using ((select auth.uid()) = user_id);
create policy "portfolio_insert_own" on public.portfolio
    for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "portfolio_update_own" on public.portfolio
    for update to authenticated using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);
create policy "portfolio_delete_own" on public.portfolio
    for delete to authenticated using ((select auth.uid()) = user_id);

create policy "watchlist_select_own" on public.watchlist
    for select to authenticated using ((select auth.uid()) = user_id);
create policy "watchlist_insert_own" on public.watchlist
    for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "watchlist_update_own" on public.watchlist
    for update to authenticated using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);
create policy "watchlist_delete_own" on public.watchlist
    for delete to authenticated using ((select auth.uid()) = user_id);
