#!/usr/bin/env python3
"""
Test script for video analyzer with Whisper transcription
This tests the pipeline structure and error handling
"""
import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        from core.video_analyzer import VideoAnalyzer
        logger.info("✓ VideoAnalyzer imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import VideoAnalyzer: {e}")
        return False
    
    try:
        import whisper
        logger.info("✓ Whisper imported successfully")
    except ImportError as e:
        logger.warning(f"⚠ Whisper not installed: {e}")
        logger.warning("  Install with: pip install openai-whisper")
        return False
    
    return True

def test_video_analyzer_initialization():
    """Test VideoAnalyzer initialization"""
    logger.info("\nTesting VideoAnalyzer initialization...")
    
    try:
        from core.video_analyzer import VideoAnalyzer
        from utils.credential_manager import CredentialManager
        import yaml
        
        # Load config
        with open('config/settings.yaml', 'r') as f:
            settings = yaml.safe_load(f)
        
        with open('config/ai_prompts.yaml', 'r') as f:
            prompts = yaml.safe_load(f)
        
        # Create credential manager
        credential_manager = CredentialManager('config/platform_credentials.yaml')
        
        # Initialize analyzer
        ai_config = settings.get('ai', {})
        ai_config['cache_dir'] = settings['paths']['cache_ai']
        
        analyzer = VideoAnalyzer(ai_config, prompts, credential_manager)
        
        logger.info("✓ VideoAnalyzer initialized successfully")
        logger.info(f"  - Model: {analyzer.model}")
        logger.info(f"  - Whisper model size: {analyzer.whisper_model_size}")
        logger.info(f"  - Cache directory: {analyzer.cache_dir}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize VideoAnalyzer: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_methods_exist():
    """Test that all required methods exist"""
    logger.info("\nTesting method existence...")
    
    try:
        from core.video_analyzer import VideoAnalyzer
        
        required_methods = [
            '_check_ffmpeg',
            '_extract_audio',
            '_load_whisper_model',
            '_transcribe_audio',
            '_extract_frames',
            'analyze_video'
        ]
        
        for method in required_methods:
            if hasattr(VideoAnalyzer, method):
                logger.info(f"✓ Method {method} exists")
            else:
                logger.error(f"✗ Method {method} missing")
                return False
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to check methods: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid inputs"""
    logger.info("\nTesting error handling...")
    
    try:
        from core.video_analyzer import VideoAnalyzer
        from utils.credential_manager import CredentialManager
        import yaml
        
        # Load config
        with open('config/settings.yaml', 'r') as f:
            settings = yaml.safe_load(f)
        
        with open('config/ai_prompts.yaml', 'r') as f:
            prompts = yaml.safe_load(f)
        
        # Create credential manager
        credential_manager = CredentialManager('config/platform_credentials.yaml')
        
        # Initialize analyzer
        ai_config = settings.get('ai', {})
        ai_config['cache_dir'] = settings['paths']['cache_ai']
        
        analyzer = VideoAnalyzer(ai_config, prompts, credential_manager)
        
        # Test with non-existent file
        result = analyzer.analyze_video("/nonexistent/video.mp4")
        
        if 'error' in result:
            logger.info("✓ Error handling works for non-existent file")
            logger.info(f"  Error: {result.get('error')}")
            return True
        else:
            logger.error("✗ No error reported for non-existent file")
            return False
    except Exception as e:
        logger.error(f"✗ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Video Analyzer Pipeline Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("VideoAnalyzer Initialization", test_video_analyzer_initialization),
        ("Method Existence", test_methods_exist),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("\n🎉 All tests passed!")
        return 0
    else:
        logger.warning(f"\n⚠ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
