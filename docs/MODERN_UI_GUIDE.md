# Modern UI Guide

## Overview
The Modern UI (`src/modern_ui.py`) provides a sleek, dark-mode friendly interface for the Video Clipping System using CustomTkinter.

## Features

### 1. **File Selection**
- Click "📁 Select Videos" button to choose video files
- Automatically copies selected files to `input/videos/` directory
- Supports: `.mp4`, `.mov`, `.avi`, `.mkv`

### 2. **Configuration Dashboard**

#### Metadata Settings
- **Default Description**: Set a default description for all clips (overrides AI generation)
- **Default Hashtags**: Set default hashtags (comma-separated) to use for all clips

#### Processing Parameters
- **Min Viral Score Threshold**: Slider to set minimum viral score (0-100)
  - Default: 70
  - Only segments with scores above this threshold will be extracted
  
- **Max Clips per Video**: Slider to set maximum number of clips per video (1-10)
  - Default: 5
  - Limits the number of clips extracted from each video

#### Platform Selection
- **📷 Instagram Reels**: Enable/disable Instagram upload
- **▶ YouTube Shorts**: Enable/disable YouTube upload
- **🎵 TikTok**: Enable/disable TikTok upload
- **🚀 Auto-schedule uploads**: Automatically schedule uploads after processing

### 3. **Real-time Logs**
- Console/Log Viewer with real-time progress updates
- Redirects all system logs to the UI
- Color-coded messages with emoji indicators:
  - ✓ Success messages
  - ⚠ Warnings
  - 🚀 Processing starts
  - 🎉 Completion messages

### 4. **Controls**
- **▶ Start Processing**: Begin processing videos with current configuration
- **⏹ Stop Processing**: Stop current processing (gracefully)
- **💾 Save Config**: Save configuration to `config/settings.yaml`
- **🗑 Clear Logs**: Clear the log viewer

### 5. **Appearance Mode**
- Switch between Dark, Light, and System themes
- Modern, dark-mode friendly design by default

## How to Use

### Starting the Modern UI

```bash
python src/modern_ui.py
```

### Workflow

1. **Select Videos**
   - Click "📁 Select Videos"
   - Choose one or more video files
   - Files are automatically copied to `input/videos/`

2. **Configure Settings**
   - Go to the "Configuration" tab
   - Set your preferred metadata (description, hashtags)
   - Adjust processing parameters (viral score, max clips)
   - Select target platforms

3. **Save Configuration** (Optional)
   - Click "💾 Save Config" to persist settings

4. **Start Processing**
   - Click "▶ Start Processing"
   - Switch to "Logs" tab to see real-time progress
   - The system will:
     - Analyze videos for viral-worthy segments
     - Extract clips meeting the viral score threshold
     - Optimize clips for selected platforms
     - Schedule uploads (if auto-upload is enabled)

5. **Monitor Progress**
   - View real-time logs in the "Logs" tab
   - Status bar shows current state and summary

6. **Stop if Needed**
   - Click "⏹ Stop Processing" to gracefully stop
   - System will complete the current video and stop

## Configuration Details

### Saved to `config/settings.yaml`
- Default description
- Default hashtags override

### UI Session Settings (not saved)
- Min viral score threshold
- Max clips per video
- Selected platforms
- Auto-upload preference

## Tips

1. **Testing**: Start with a low "Max Clips" value (1-2) to test quickly
2. **Quality vs Quantity**: Higher viral score threshold = fewer but higher quality clips
3. **Platform Selection**: Deselect platforms you don't want to upload to
4. **Logs**: Keep the Logs tab open during processing for detailed feedback
5. **Dark Mode**: Perfect for late-night content creation sessions!

## Troubleshooting

### No Videos Found
- Ensure videos are in `input/videos/` directory
- Use "📁 Select Videos" button to add videos

### Processing Errors
- Check the Logs tab for detailed error messages
- Ensure GitHub API token is configured (for AI analysis)
- Verify video files are not corrupted

### API Errors
- The system now includes robust error handling for API responses
- Check logs for detailed error messages including:
  - API status codes
  - Raw response text (for debugging)
  - JSON parsing errors with context

## Technical Details

- Built with **CustomTkinter 5.2.0+** for modern UI components
- Dark mode by default with theme switching support
- Thread-safe logging from background processing
- Graceful shutdown handling
- Integrates seamlessly with existing `main.py` functionality

## Comparison with Simple UI

| Feature | Simple UI | Modern UI |
|---------|-----------|-----------|
| Design | Basic tkinter | Modern, dark-mode |
| File Selection | Manual copy | Integrated file dialog |
| Parameters | Config file only | Interactive sliders |
| Platform Selection | Command-line only | Visual checkboxes |
| Logs | Basic text area | Styled, emoji-enhanced |
| Themes | None | Dark/Light/System |
| Controls | Start only | Start/Stop/Save |

## Requirements

- Python 3.8+
- customtkinter >= 5.2.0
- All other dependencies from `requirements.txt`
