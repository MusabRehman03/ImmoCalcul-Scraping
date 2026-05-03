## Image Compression (Lossless, VPS & Simple Mode)

This project uses **lossless image compression** for screenshots and exported images:

- **PNG:** [optipng](http://optipng.sourceforge.net/) (lossless, open source)
- **JPEG:** [jpegoptim](https://github.com/tjko/jpegoptim) (lossless, open source)

These tools are installed automatically in the Docker image. If you run outside Docker (simple mode), install them on your VPS for best results:

```bash
sudo apt-get install optipng jpegoptim
# or
brew install optipng jpegoptim
```

If these tools are not available, the script will fallback to Pillow for basic optimization (not always lossless).

Compression is applied automatically after screenshots are saved and before PDF creation. Logs will show before/after file sizes.
# Docker Setup for ImmoCalcul Scraper

This Docker setup allows you to test the scraper in a Linux environment with virtual display support, simulating a VPS deployment.

## Quick Start

### 1. Build the Docker Image

```bash
docker-compose build
```

### 2. Run the Scraper Inside Docker

**Option A: With Virtual Display (Recommended for testing anti-bot bypasses)**
```bash
docker-compose run scraper /app/docker-entrypoint.sh --lot 2607802 --virtual-display --record-video --trace
```

**Option B: Interactive Bash Shell (for debugging)**
```bash
docker-compose run scraper bash
```

Then inside the container:
```bash
# Test with virtual display
/app/docker-entrypoint.sh --lot 2607802 --virtual-display --record-video --trace

# Or run directly
python3 full_step_scraper.py --lot 2607802 --virtual-display --record-video --trace
```

### 3. Output Files

All output (videos, traces, screenshots, summary.json) will be saved to:
```
./run_steps/<run_id>/
```

These are shared between your Mac and the Docker container via volume mount.

## Environment Variables

The `docker-compose.yml` automatically passes your environment variables:
- `IMMOCALCUL_EMAIL`
- `IMMOCALCUL_PASSWORD`
- `PARENT_DRIVE_FOLDER_ID`

Make sure these are set in your `.env` file or shell before running Docker.

## Troubleshooting

### Display Issues
If you see "Cannot connect to display" errors, Xvfb may not have started. Check:
```bash
docker-compose run scraper bash
# Inside container
ps aux | grep Xvfb
```

### Permission Issues
If you get permission errors accessing `run_steps/`, run:
```bash
chmod -R 777 run_steps/
```

### Container Won't Start
Rebuild and check logs:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose run scraper bash
```

## Development Workflow

1. **Test on macOS first** (fast iteration):
   ```bash
   python3 full_step_scraper.py --lot 2607802 --record-video --trace
   ```

2. **Test in Docker** (simulate VPS):
   ```bash
   docker-compose run scraper /app/docker-entrypoint.sh --lot 2607802 --virtual-display --record-video --trace
   ```

3. **Deploy to VPS** (with `--virtual-display` flag if using Xvfb there too)

## Useful Commands

### View running containers
```bash
docker-compose ps
```

### Stop all containers
```bash
docker-compose down
```

### Remove all images and containers
```bash
docker-compose down --rmi all
```

### Run with custom arguments
```bash
docker-compose run scraper /app/docker-entrypoint.sh --lot 2607802 --headless --trace
```

### Access container shell
```bash
docker-compose run scraper bash
```
