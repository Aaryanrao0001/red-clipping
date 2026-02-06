# Red Clipping - Autonomous Video Clipping & Publishing System

An intelligent, AI-powered system for automatically analyzing videos, extracting viral clips, and publishing them across multiple social media platforms (Instagram Reels, YouTube Shorts, TikTok).

## Features

- 🤖 **AI-Powered Analysis**: Uses GitHub Models API (GPT-4) to identify viral-worthy video segments
- ✂️ **Automated Clip Extraction**: FFmpeg-based video processing with quality optimization
- 📱 **Multi-Platform Publishing**: Automated uploads to Instagram, YouTube, and TikTok
- 🏷️ **Smart Metadata Generation**: AI-generated captions and hashtags optimized for each platform
- ⏰ **Intelligent Scheduling**: Staggered uploads with configurable delays between posts
- 🔒 **Secure Credential Management**: Encrypted storage of platform credentials
- 📊 **Upload Tracking**: Complete history and queue management for all uploads
- 🎨 **Format Optimization**: Automatic aspect ratio conversion (9:16 for vertical video)
- 🔄 **Retry Logic**: Automatic retry for failed uploads with exponential backoff
- 🎯 **Consistent Hashtags**: Option to maintain consistent hashtags across all platforms
- 🖥️ **Simple UI**: Tkinter-based graphical interface for easy system control and configuration

## System Architecture

```
├── config/                 # Configuration files
│   ├── settings.yaml       # General settings (paths, thresholds, etc.)
│   ├── platform_credentials.yaml  # Encrypted credentials
│   └── ai_prompts.yaml     # AI prompts for analysis and generation
├── input/videos/           # Input video files
├── output/
│   ├── clips/             # Extracted and optimized clips
│   ├── thumbnails/        # Generated thumbnails
│   └── logs/              # Application logs
├── cache/
│   ├── ai_responses/      # Cached AI analysis results
│   └── temp_processing/   # Temporary processing files
└── src/
    ├── core/              # Core processing modules
    │   ├── video_analyzer.py
    │   ├── clip_extractor.py
    │   ├── format_optimizer.py
    │   └── metadata_generator.py
    ├── upload/            # Platform uploaders
    │   ├── instagram_uploader.py
    │   ├── youtube_uploader.py
    │   ├── tiktok_uploader.py
    │   └── upload_scheduler.py
    ├── utils/             # Utility modules
    │   ├── browser_manager.py
    │   ├── credential_manager.py
    │   └── state_manager.py
    ├── main.py            # Main orchestrator
    └── simple_ui.py       # Simple graphical UI
```

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Aaryanrao0001/red-clipping.git
cd red-clipping
```

2. **Install FFmpeg** (required for video processing):
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

3. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
# Create .env file or set environment variables
export GITHUB_TOKEN="your_github_token"
export ENCRYPTION_KEY="your_encryption_key"  # Optional
```

## Configuration

### 1. General Settings (`config/settings.yaml`)

Configure paths, video processing settings, AI parameters, and platform-specific requirements.

Key settings:
- `min_clip_duration`: Minimum clip length (default: 15s)
- `max_clip_duration`: Maximum clip length (default: 60s)
- `target_aspect_ratio`: Video aspect ratio (default: 9:16)
- `min_upload_delay_minutes`: Delay between uploads (default: 60 min)
- `consistent_hashtags`: Use same hashtags across platforms (default: true)
- `default_description`: Default description for all clips (overrides AI generation when set)
- `default_hashtags_override`: Default hashtags for all clips (overrides AI generation when set)

### 2. Platform Credentials (`config/platform_credentials.yaml`)

Store encrypted credentials for each platform. Use the CLI to set credentials:

```bash
python src/main.py credentials --platform instagram --field username --value "your_username"
python src/main.py credentials --platform instagram --field password --value "your_password"
python src/main.py credentials --platform youtube --field email --value "your_email"
python src/main.py credentials --platform youtube --field password --value "your_password"
python src/main.py credentials --platform tiktok --field username --value "your_username"
python src/main.py credentials --platform tiktok --field password --value "your_password"
python src/main.py credentials --platform github_api --field token --value "your_github_token"
```

### 3. AI Prompts (`config/ai_prompts.yaml`)

Customize AI prompts for video analysis, caption generation, and hashtag generation.

## Usage

### Using the Simple UI

The system includes a graphical user interface for easy operation:

```bash
python src/simple_ui.py
```

**UI Features**:
- **Default Description**: Set a custom description that will be used for all clips instead of AI-generated captions
- **Default Hashtags**: Set custom hashtags (comma-separated) that will be used for all clips instead of AI-generated hashtags
- **Save Configuration**: Saves your default metadata settings to `config/settings.yaml`
- **Start Processing**: Begins processing all videos in the input directory with automatic upload scheduling
- **Logs**: Real-time log display showing processing progress and status

**Note**: The default metadata settings enforce consistent descriptions and hashtags across all uploads until you change them. This is useful when you want to maintain a specific message or branding across all your content.

### Using the Command Line

### Process Videos

**Process all videos in input directory**:
```bash
python src/main.py process
```

**Process specific video**:
```bash
python src/main.py process --video input/videos/sample.mp4
```

**Process with auto-upload**:
```bash
python src/main.py process --auto-upload --platforms instagram youtube tiktok
```

### Manage Credentials

**Set credentials**:
```bash
python src/main.py credentials --platform instagram --field username --value "myusername"
```

### View Upload Queue

**View all queued uploads**:
```bash
python src/main.py queue
```

**View queue for specific platform**:
```bash
python src/main.py queue --platform instagram
```

### View Upload History

**View recent uploads**:
```bash
python src/main.py history --limit 20
```

**View history for specific platform**:
```bash
python src/main.py history --platform youtube --limit 10
```

## Workflow

1. **Video Discovery**: System scans `input/videos/` for video files
2. **AI Analysis**: Videos are analyzed to identify viral-worthy segments (15-60s)
3. **Clip Extraction**: Selected segments are extracted using FFmpeg
4. **Format Optimization**: Clips are optimized for each platform (aspect ratio, quality, file size)
5. **Metadata Generation**: AI generates platform-specific captions and hashtags
6. **Upload Scheduling**: Uploads are scheduled with appropriate delays
7. **Execution**: Selenium-based automation uploads clips to each platform
8. **Tracking**: Upload status is tracked in history and queue

## Key Features Explained

### Consistent Hashtags

The system supports consistent hashtag usage across platforms. When enabled (default):
- First video clip generates hashtags based on content
- Same core hashtags are used for all subsequent uploads
- Platform-specific hashtags are added as needed
- Can be reset or manually configured

### Intelligent Scheduling

- Minimum 60-minute delay between uploads (configurable)
- Staggered uploads across platforms (5-minute delay)
- Automatic retry on failure (max 3 attempts)
- Respects platform rate limits

### Browser Automation

- Uses `undetected-chromedriver` to avoid detection
- Persistent browser profiles for each platform
- Automatic cookie consent handling
- Screenshot capture on errors

### Security

- Credentials encrypted using `cryptography` library
- Encryption key can be stored in environment variable
- API tokens never stored in plain text
- Browser profiles isolated per platform

## API Requirements

### GitHub Models API

You need a GitHub token with access to GitHub Models API:

1. Go to https://github.com/settings/tokens
2. Generate a new token with appropriate permissions
3. Set as environment variable: `export GITHUB_TOKEN="your_token"`

The system uses the GPT-4 model for:
- Video segment analysis
- Caption generation
- Hashtag generation

## Platform-Specific Notes

### Instagram Reels
- Max duration: 90 seconds
- Aspect ratio: 9:16
- Max file size: 100 MB
- Hashtags: Up to 30

### YouTube Shorts
- Max duration: 60 seconds
- Aspect ratio: 9:16
- Max file size: 100 MB
- Hashtags: Up to 15

### TikTok
- Max duration: 60 seconds
- Aspect ratio: 9:16
- Max file size: 100 MB
- Hashtags: Up to 30

## Troubleshooting

### FFmpeg not found
Install FFmpeg using your system's package manager.

### Browser automation fails
- Ensure you're not in headless mode for initial setup
- Check browser profiles in `cache/browser_profiles/`
- Verify credentials are correct
- Some platforms may require manual CAPTCHA solving

### AI analysis fails
- Check GitHub token is valid
- Verify API endpoint is accessible
- Check logs in `output/logs/app.log`

### Upload scheduling issues
- Ensure scheduler is running (`--auto-upload` flag)
- Check queue status with `python src/main.py queue`
- Review upload history for errors

## Development

### Adding New Platforms

1. Create uploader class in `src/upload/`
2. Implement `login()` and `upload()` methods
3. Add platform configuration to `config/settings.yaml`
4. Register uploader in `main.py`

### Customizing AI Prompts

Edit `config/ai_prompts.yaml` to customize:
- Video analysis criteria
- Caption generation style
- Hashtag strategy
- Platform-specific guidelines

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Disclaimer

This tool is for educational purposes. Ensure you comply with each platform's Terms of Service and automation policies. Use responsibly and respect platform rate limits.