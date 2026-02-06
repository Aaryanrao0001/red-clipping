# Quick Start Guide

## Prerequisites

1. **Python 3.8+** installed
2. **FFmpeg** installed and in PATH
3. **GitHub Token** with access to GitHub Models API

## Installation

```bash
# Clone repository
git clone https://github.com/Aaryanrao0001/red-clipping.git
cd red-clipping

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export GITHUB_TOKEN="your_github_token_here"
```

## Initial Setup

### 1. Configure Credentials

Set credentials for each platform you want to use:

```bash
# Instagram
python src/main.py credentials --platform instagram --field username --value "your_username"
python src/main.py credentials --platform instagram --field password --value "your_password"

# YouTube
python src/main.py credentials --platform youtube --field email --value "your_email@gmail.com"
python src/main.py credentials --platform youtube --field password --value "your_password"

# TikTok
python src/main.py credentials --platform tiktok --field username --value "your_username"
python src/main.py credentials --platform tiktok --field password --value "your_password"

# GitHub API (if not using environment variable)
python src/main.py credentials --platform github_api --field token --value "your_github_token"
```

### 2. Add Videos

Place your video files in the `input/videos/` directory:

```bash
cp /path/to/your/video.mp4 input/videos/
```

## Basic Usage

### Process Videos (Without Upload)

Analyze and extract clips without uploading:

```bash
python src/main.py process
```

This will:
- Analyze all videos in `input/videos/`
- Extract viral-worthy clips
- Save clips to `output/clips/`
- Generate metadata (captions/hashtags)

### Process and Upload

Analyze, extract, and schedule uploads:

```bash
python src/main.py process --auto-upload
```

Keep the terminal open - the scheduler will upload clips with appropriate delays.

### Process Specific Video

Process just one video file:

```bash
python src/main.py process --video input/videos/myvideo.mp4 --auto-upload
```

### Upload to Specific Platforms

```bash
python src/main.py process --platforms instagram youtube --auto-upload
```

## Monitoring

### View Upload Queue

```bash
python src/main.py queue
```

### View Upload History

```bash
python src/main.py history --limit 20
```

### View Platform-Specific History

```bash
python src/main.py history --platform instagram --limit 10
```

## Configuration

### Adjust Settings

Edit `config/settings.yaml` to customize:

- Upload delays (default: 60 minutes between uploads)
- Video quality settings
- AI analysis parameters
- Platform-specific settings

### Customize AI Prompts

Edit `config/ai_prompts.yaml` to customize:

- Video analysis criteria
- Caption generation style
- Hashtag strategy

## Workflow Example

Here's a complete workflow:

```bash
# 1. Setup (one time)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"
python src/main.py credentials --platform instagram --field username --value "myaccount"
python src/main.py credentials --platform instagram --field password --value "mypassword"

# 2. Add videos
cp ~/Downloads/video1.mp4 input/videos/
cp ~/Downloads/video2.mp4 input/videos/

# 3. Process and upload to Instagram
python src/main.py process --platforms instagram --auto-upload

# 4. Monitor progress
# In another terminal:
python src/main.py queue
python src/main.py history

# 5. Keep terminal open until all uploads complete
# Press Ctrl+C when done
```

## Tips

1. **First Run**: Don't use `--auto-upload` on first run. Review extracted clips first.

2. **Headless Mode**: For production, enable headless mode in `config/settings.yaml`:
   ```yaml
   browser:
     headless: true
   ```

3. **Rate Limits**: The system respects platform rate limits with configurable delays.

4. **Consistent Hashtags**: By default, hashtags are consistent across all clips. See `docs/CONSISTENT_HASHTAGS.md` for details.

5. **Logs**: Check `output/logs/app.log` for detailed information.

## Troubleshooting

### No clips extracted
- Check video quality and length
- Lower `min_clip_duration` in settings
- Review `output/logs/app.log`

### Upload fails
- Verify credentials are correct
- Check internet connection
- Platform may require CAPTCHA (disable headless mode)
- Review browser screenshots in logs

### API errors
- Verify GitHub token is valid
- Check API quota/limits
- Review error messages in logs

## Next Steps

- Read `README.md` for detailed documentation
- See `docs/CONSISTENT_HASHTAGS.md` for hashtag feature details
- Customize prompts in `config/ai_prompts.yaml`
- Adjust settings in `config/settings.yaml`
