# Angel Archiver

[![Docker Image CI](https://github.com/david-w-43/AngelArchiver/actions/workflows/docker-image.yml/badge.svg)](https://github.com/david-w-43/AngelArchiver/actions/workflows/docker-image.yml)

A wonderfully bodgy service to archive my favourite local radio station, [Angel Radio](https://www.angelradio.co.uk). It's great for finding new (old) music as they have a great variety of tune - and nothing after 1969!

## Get started

1. (Prerequisite) Install Docker with Docker Compose
2. Clone this repository
3. Edit the paths in `docker-compose.yml`
4. Start with `docker compose up -d`

## How does this work?

**`record.sh`** uses ffmpeg to continuously record 5-minute segments of live radio.

**`run.py`** is designed to run daily at *midnight*, and runs code from the following two files:

- **`Ingestor.py`** parses the website's schedule and uploads programme titles and start times to a database.

- **`Assemble.py`** reads this database and concatenates 5-minute segments into whole radio programmes.
