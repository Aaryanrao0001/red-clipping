# Consistent Hashtags Feature

## Overview

The Red Clipping system supports **consistent hashtag usage across all platforms** to maintain brand identity and improve content discoverability. This feature ensures that core hashtags remain the same across Instagram, YouTube, and TikTok while allowing platform-specific hashtags to be added.

## How It Works

### 1. Default Behavior (Consistent Hashtags Enabled)

When `consistent_hashtags: true` in `config/settings.yaml` (default):

1. **First Clip**: AI generates hashtags based on video content
2. **Subsequent Clips**: Core hashtags from the first clip are reused
3. **Platform-Specific**: Additional platform-specific tags are added
4. **Persistence**: Base hashtags persist across all clips in a processing session

### 2. Configuration

In `config/settings.yaml`:

```yaml
metadata:
  # Enable consistent hashtags across platforms
  consistent_hashtags: true
  
  # Default hashtags always included
  default_hashtags:
    - "viral"
    - "trending"
    - "shorts"
```

### 3. Hashtag Strategy

The system uses a multi-tiered hashtag strategy defined in `config/ai_prompts.yaml`:

#### Core Tags (Consistent Across Platforms)
```yaml
consistent_core_tags:
  - "viral"
  - "trending"
  - "fyp"
  - "foryou"
```

#### Category-Based Tags
```yaml
category_tags:
  humor:
    - "funny"
    - "comedy"
    - "laugh"
  education:
    - "learn"
    - "educational"
    - "tutorial"
```

## Usage Examples

### Example 1: Processing Multiple Videos

```python
from src.main import VideoClippingSystem

system = VideoClippingSystem()

# Process first video - generates base hashtags
result1 = system.process_video('video1.mp4', auto_upload=True)
# Hashtags: #viral #trending #funny #comedy #shorts

# Process second video - uses same core hashtags
result2 = system.process_video('video2.mp4', auto_upload=True)
# Hashtags: #viral #trending #funny #comedy #shorts (same core set)
```

### Example 2: Programmatic Control

```python
from src.core.metadata_generator import MetadataGenerator

# Create metadata generator
metadata_gen = MetadataGenerator(config, prompts, video_analyzer)

# Manually set base hashtags
custom_hashtags = ['mybrand', 'viral', 'trending']
metadata_gen.set_base_hashtags(custom_hashtags)

# Generate hashtags - will use custom base
hashtags = metadata_gen.generate_hashtags(segment, 'instagram')
# Result includes: #mybrand #viral #trending + platform-specific tags

# Reset to allow new hashtags
metadata_gen.reset_base_hashtags()
```

### Example 3: Disable Consistent Hashtags

To disable and generate new hashtags for each clip:

```python
# In code:
hashtags = metadata_gen.generate_hashtags(
    segment, 
    platform='instagram',
    use_consistent=False  # Override setting
)
```

Or update `config/settings.yaml`:
```yaml
metadata:
  consistent_hashtags: false
```

## Platform-Specific Limits

The system respects platform hashtag limits:

| Platform | Max Hashtags |
|----------|--------------|
| Instagram | 30 |
| YouTube | 15 |
| TikTok | 30 |

For YouTube (15 hashtag limit), the system prioritizes:
1. Default/core hashtags
2. Category-specific hashtags
3. AI-generated relevant hashtags (up to limit)

## Best Practices

### 1. Brand Consistency
Set custom base hashtags for your brand:
```python
system.metadata_generator.set_base_hashtags([
    'yourbrand',
    'yourniche',
    'viral',
    'trending'
])
```

### 2. Campaign Tracking
Use consistent hashtags for campaigns:
```yaml
default_hashtags:
  - "2024campaign"
  - "yourbrand"
  - "viral"
```

### 3. A/B Testing
Temporarily disable consistency to test different hashtag sets:
```python
# Variant A
metadata_gen.set_base_hashtags(['viral', 'trending', 'shorts'])

# Process some videos...

# Variant B
metadata_gen.reset_base_hashtags()
metadata_gen.set_base_hashtags(['fyp', 'foryou', 'explore'])
```

## Configuration Reference

### settings.yaml
```yaml
metadata:
  consistent_hashtags: true  # Enable/disable feature
  max_hashtags_instagram: 30
  max_hashtags_youtube: 15
  max_hashtags_tiktok: 30
  default_hashtags:  # Always included
    - "viral"
    - "trending"
```

### ai_prompts.yaml
```yaml
hashtag_strategy:
  consistent_core_tags:  # Core tags for all platforms
    - "viral"
    - "trending"
  
  category_tags:  # Category-specific tags
    humor:
      - "funny"
      - "comedy"
```
