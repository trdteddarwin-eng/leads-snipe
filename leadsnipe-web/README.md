# LeadSnipe Web App

AI-Powered B2B Lead Generation Platform - Now as a Web Application!

## Quick Start

```bash
cd leadsnipe-web
npm install
npm run dev
```

Open http://localhost:3000

## Features Built

✅ Landing page with features
✅ Authentication (login, signup)
✅ Dashboard with stats
✅ 4-step campaign wizard
✅ Lead list & detail pages
✅ Ready for Python backend integration

## Project Structure

- `/` - Landing page
- `/login` - Sign in
- `/signup` - Create account
- `/dashboard` - Main dashboard
- `/campaigns/new` - Campaign wizard
- `/leads` - Lead list
- `/leads/[id]` - Lead details

## Next: Connect to Python Backend

See `directives/frontend_backend_mapping.md` for integration guide.

The Python pipeline scripts are in `../execution/`:
- `n8n_gmaps_scraper_ai.py` - Lead scraper (FREE)
- `anymailfinder_decision_maker.py` - Decision makers ($0.04/email)
- `find_linkedin_smart.py` - LinkedIn profiles (FREE)

## Deploy

Push to GitHub, then deploy on Vercel in one click!
