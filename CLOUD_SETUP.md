# Supabase Cloud Setup

The app uses Supabase Auth for password login and Row Level Security (RLS) to isolate each user's portfolio and watchlist. New cloud accounts use usernames; the app maps them to internal non-deliverable addresses because Supabase Auth requires an email identifier.

1. In the Supabase dashboard for this project, open **SQL Editor**.
2. Open `supabase_schema.sql` in this project, copy its contents into the SQL Editor, and run it.
3. In Supabase, open **Authentication → Sign In / Providers → Email** and turn off **Confirm email**. Username-only accounts use an internal `.invalid` address, so no confirmation email can be received.
4. Launch Leo Investing and create an account with a username and password. Existing email-based accounts can still sign in with their email.

Cloud requests use Python's standard-library HTTPS client; no Supabase SDK package is required.

The project URL and publishable key are in the ignored local `.env` file. Never put a `service_role` key in this desktop app. RLS is required because desktop client keys are public.

Legacy JSON and SQLite files remain on this device and are not automatically uploaded or deleted. The app's market-data cache, Python environment, and application files remain local; cloud storage holds portfolio/watchlist records written after sign-in.

## Browser App

Run `Run Leo Web.bat`, then open `http://127.0.0.1:8000`. The small local Python server serves the web interface and provides quote/search/history endpoints through the existing `yfinance` code. Supabase Auth and user stock records are accessed from the browser using the publishable key and RLS. Keep the server window open while using the app; press Ctrl+C there to stop it.

## Public URL

`render.yaml` prepares a free Render web service. To publish it, push this project to a GitHub repository you control, create a Render account, choose **New → Blueprint**, and connect that repository. Render will ask for `SUPABASE_PUBLISHABLE_KEY`; use the project's publishable key, never a `service_role` key. The service will receive a public `onrender.com` URL after its first deploy.

For your own domain, register a domain with a registrar, then in the Render service open **Settings → Custom Domains → Add Custom Domain**. Follow Render's displayed DNS records at your registrar and use **Verify** in Render; Render provisions HTTPS. Free Render services sleep after 15 minutes without traffic and can take about a minute to wake. Their filesystem is temporary, so the durable portfolio/watchlist remains in Supabase, not on Render.
