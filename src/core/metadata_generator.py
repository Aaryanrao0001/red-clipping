"""
Metadata Generator - Generate captions and hashtags using AI
"""
import os
import json
import logging
import yaml

logger = logging.getLogger(__name__)


class MetadataGenerator:
    """Generate captions and hashtags for video clips"""
    
    def __init__(self, config, prompts_config, video_analyzer):
        """
        Initialize metadata generator
        
        Args:
            config: Metadata configuration dictionary
            prompts_config: AI prompts configuration
            video_analyzer: VideoAnalyzer instance for API access
        """
        self.config = config
        self.prompts = prompts_config
        self.video_analyzer = video_analyzer
        self.consistent_hashtags = config.get('consistent_hashtags', True)
        self.max_hashtags = {
            'instagram': config.get('max_hashtags_instagram', 30),
            'youtube': config.get('max_hashtags_youtube', 15),
            'tiktok': config.get('max_hashtags_tiktok', 30)
        }
        self.default_hashtags = config.get('default_hashtags', [])
        
        # Store generated hashtags for consistency
        self._base_hashtags = None
    
    def generate_caption(self, segment, platform, custom_context=None):
        """
        Generate caption for a video segment
        
        Args:
            segment: Segment dictionary with metadata
            platform: Target platform (instagram, youtube, tiktok)
            custom_context: Optional custom context for caption generation
            
        Returns:
            Generated caption string
        """
        # Get platform-specific guidelines
        guidelines = self.prompts.get('platform_caption_guidelines', {}).get(platform, {})
        
        # Get caption generation prompt
        prompt_template = self.prompts.get('caption_generation_prompt', '')
        
        # Extract segment information
        category = segment.get('category', 'entertainment')
        themes = segment.get('themes', [])
        description = segment.get('description', '')
        
        # Format prompt
        prompt = prompt_template.format(
            platform=platform,
            category=category,
            themes=', '.join(themes) if themes else 'general',
            description=description
        )
        
        # Add platform guidelines
        if guidelines:
            prompt += f"\n\nPlatform Guidelines:\n"
            prompt += f"- Maximum length: {guidelines.get('max_length', 2200)} characters\n"
            prompt += f"- Style: {guidelines.get('style', 'engaging')}\n"
        
        # Add custom context if provided
        if custom_context:
            prompt += f"\n\nAdditional Context: {custom_context}"
        
        logger.info(f"Generating caption for {platform}")
        
        try:
            # Call API via video analyzer
            caption = self.video_analyzer._call_api(prompt)
            
            # Clean up response
            caption = caption.strip()
            
            # Remove quotes if present
            if caption.startswith('"') and caption.endswith('"'):
                caption = caption[1:-1]
            if caption.startswith("'") and caption.endswith("'"):
                caption = caption[1:-1]
            
            # Enforce length limits
            max_length = guidelines.get('max_length', 2200)
            if len(caption) > max_length:
                caption = caption[:max_length-3] + "..."
            
            logger.info(f"Caption generated for {platform}: {len(caption)} characters")
            return caption
        
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            # Return a basic caption
            return f"Check out this {category} video! {' '.join(['#' + t for t in themes[:3]])}"
    
    def generate_hashtags(self, segment, platform, use_consistent=None):
        """
        Generate hashtags for a video segment
        
        Args:
            segment: Segment dictionary with metadata
            platform: Target platform (instagram, youtube, tiktok)
            use_consistent: Override for consistent hashtags setting
            
        Returns:
            List of hashtags (without # symbol)
        """
        if use_consistent is None:
            use_consistent = self.consistent_hashtags
        
        # If consistent hashtags are enabled and we have base hashtags, use them
        if use_consistent and self._base_hashtags:
            logger.info(f"Using consistent base hashtags for {platform}")
            platform_hashtags = self._base_hashtags.copy()
        else:
            # Generate new hashtags
            platform_hashtags = self._generate_new_hashtags(segment, platform)
            
            # Store as base hashtags if consistency is enabled
            if use_consistent and not self._base_hashtags:
                self._base_hashtags = platform_hashtags.copy()
                logger.info("Stored base hashtags for consistency across platforms")
        
        # Limit to platform maximum
        max_tags = self.max_hashtags.get(platform, 30)
        return platform_hashtags[:max_tags]
    
    def _generate_new_hashtags(self, segment, platform):
        """
        Generate new hashtags using AI
        
        Args:
            segment: Segment dictionary with metadata
            platform: Target platform
            
        Returns:
            List of hashtags
        """
        # Get hashtag generation prompt
        prompt_template = self.prompts.get('hashtag_generation_prompt', '')
        
        # Extract segment information
        category = segment.get('category', 'entertainment')
        themes = segment.get('themes', [])
        
        # Get platform max hashtags
        max_hashtags = self.max_hashtags.get(platform, 30)
        
        # Format prompt
        prompt = prompt_template.format(
            platform=platform,
            category=category,
            themes=', '.join(themes) if themes else 'general',
            max_hashtags=max_hashtags
        )
        
        logger.info(f"Generating hashtags for {platform}")
        
        try:
            # Call API
            response = self.video_analyzer._call_api(prompt)
            
            # Parse response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1])
            
            # Try to parse as JSON
            try:
                hashtags = json.loads(response)
                if isinstance(hashtags, list):
                    # Clean hashtags (remove # if present)
                    hashtags = [tag.lstrip('#') for tag in hashtags if tag]
                else:
                    raise ValueError("Response is not a list")
            except (json.JSONDecodeError, ValueError):
                # Try to extract hashtags from text
                hashtags = []
                for word in response.split():
                    if word.startswith('#'):
                        hashtags.append(word.lstrip('#'))
            
            # Add default hashtags
            all_hashtags = list(self.default_hashtags) + hashtags
            
            # Add category-specific hashtags
            category_tags = self.prompts.get('hashtag_strategy', {}).get('category_tags', {}).get(category, [])
            all_hashtags.extend(category_tags)
            
            # Add consistent core tags
            core_tags = self.prompts.get('hashtag_strategy', {}).get('consistent_core_tags', [])
            all_hashtags.extend(core_tags)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_hashtags = []
            for tag in all_hashtags:
                tag_lower = tag.lower()
                if tag_lower not in seen:
                    seen.add(tag_lower)
                    unique_hashtags.append(tag)
            
            logger.info(f"Generated {len(unique_hashtags)} hashtags for {platform}")
            return unique_hashtags
        
        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            # Return default hashtags
            return list(self.default_hashtags)
    
    def generate_metadata_for_clip(self, clip_info, platforms):
        """
        Generate complete metadata for a clip across multiple platforms
        
        Args:
            clip_info: Dictionary containing clip path and segment info
            platforms: List of platform names
            
        Returns:
            Dictionary mapping platforms to metadata
        """
        segment = clip_info.get('segment', {})
        metadata = {}
        
        for platform in platforms:
            caption = self.generate_caption(segment, platform)
            hashtags = self.generate_hashtags(segment, platform)
            
            metadata[platform] = {
                'caption': caption,
                'hashtags': hashtags,
                'category': segment.get('category', 'entertainment'),
                'viral_score': segment.get('viral_score', 0)
            }
        
        return metadata
    
    def reset_base_hashtags(self):
        """Reset base hashtags to force regeneration"""
        self._base_hashtags = None
        logger.info("Base hashtags reset")
    
    def set_base_hashtags(self, hashtags):
        """
        Manually set base hashtags for consistency
        
        Args:
            hashtags: List of hashtags to use
        """
        self._base_hashtags = hashtags.copy()
        logger.info(f"Set {len(hashtags)} base hashtags for consistency")
    
    def format_caption_with_hashtags(self, caption, hashtags, platform):
        """
        Format caption with hashtags according to platform conventions
        
        Args:
            caption: Caption text
            hashtags: List of hashtags
            platform: Platform name
            
        Returns:
            Formatted string
        """
        guidelines = self.prompts.get('platform_caption_guidelines', {}).get(platform, {})
        hashtag_placement = guidelines.get('hashtag_placement', 'end of caption')
        
        # Format hashtags
        hashtag_str = ' '.join(['#' + tag for tag in hashtags])
        
        if 'integrated' in hashtag_placement.lower():
            # For TikTok, hashtags are integrated in caption
            return f"{caption}\n\n{hashtag_str}"
        elif 'first comment' in hashtag_placement.lower():
            # For Instagram, hashtags can go in first comment
            # Return as dictionary
            return {
                'caption': caption,
                'first_comment': hashtag_str
            }
        else:
            # Default: end of caption
            return f"{caption}\n\n{hashtag_str}"
