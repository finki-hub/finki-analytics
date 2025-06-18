# FINKI Analytics

This application for collecting and analyzing arbitrary events stored as JSON, intended to be used by the other applications in the ecosystem. Uses [MongoDB](https://github.com/mongodb/mongo) for storing events.

## Quick Setup (Production)

1. Download [`compose.prod.yaml`](./compose.prod.yaml)
2. Download [`.env.sample`](.env.sample), rename it to `.env` and change it to your liking
3. Run `docker compose -f compose.prod.yaml up -d`

## Quick Setup (Development)

Requires Python >= 3.13 and [`uv`](https://github.com/astral-sh/uv).

1. Clone the repository: `git clone https://github.com/finki-hub/finki-analytics.git`
2. Install dependencies: `cd api && uv sync`
3. Prepare env. variables by copying `env.sample` to `.env` - minimum setup requires the database configuration, it can be left as is
4. Run it: `docker compose up -d`

## License

This project is licensed under the terms of the MIT license.
