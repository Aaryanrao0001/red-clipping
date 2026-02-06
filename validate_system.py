#!/usr/bin/env python3
"""
Validation script to test the system components
"""
import os
import sys
import yaml

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config_loading():
    """Test that configuration files load correctly"""
    print("Testing configuration loading...")
    
    try:
        with open('config/settings.yaml', 'r') as f:
            settings = yaml.safe_load(f)
        print("✓ settings.yaml loaded successfully")
        
        with open('config/ai_prompts.yaml', 'r') as f:
            prompts = yaml.safe_load(f)
        print("✓ ai_prompts.yaml loaded successfully")
        
        with open('config/platform_credentials.yaml', 'r') as f:
            credentials = yaml.safe_load(f)
        print("✓ platform_credentials.yaml loaded successfully")
        
        return True
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_imports():
    """Test that all modules can be imported"""
    print("\nTesting module imports...")
    
    modules = [
        'utils.credential_manager',
        'utils.state_manager',
        'utils.browser_manager',
        'core.video_analyzer',
        'core.clip_extractor',
        'core.format_optimizer',
        'core.metadata_generator',
        'upload.instagram_uploader',
        'upload.youtube_uploader',
        'upload.tiktok_uploader',
        'upload.upload_scheduler',
    ]
    
    success = True
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} imported successfully")
        except Exception as e:
            print(f"✗ {module} import failed: {e}")
            success = False
    
    return success

def test_credential_manager():
    """Test credential manager basic functionality"""
    print("\nTesting credential manager...")
    
    try:
        from utils.credential_manager import CredentialManager
        
        # Create temporary credential file
        cm = CredentialManager('config/platform_credentials.yaml')
        
        # Test encryption/decryption
        test_value = "test_password_123"
        cm.encrypt_credential('test_platform', 'test_field', test_value)
        decrypted = cm.decrypt_credential('test_platform', 'test_field')
        
        if decrypted == test_value:
            print("✓ Credential encryption/decryption works")
            return True
        else:
            print(f"✗ Decryption mismatch: expected '{test_value}', got '{decrypted}'")
            return False
    except Exception as e:
        print(f"✗ Credential manager test failed: {e}")
        return False

def test_state_manager():
    """Test state manager basic functionality"""
    print("\nTesting state manager...")
    
    try:
        from utils.state_manager import StateManager
        
        sm = StateManager('cache')
        
        # Test queue operations
        test_task = {
            'clip_path': 'test/clip.mp4',
            'platform': 'test_platform',
            'metadata': {'caption': 'test'}
        }
        
        sm.add_to_queue(test_task)
        queue = sm.get_queue()
        
        if len(queue) > 0 and queue[-1]['clip_path'] == test_task['clip_path']:
            print("✓ State manager queue operations work")
            
            # Test history operations
            sm.add_to_history({
                'clip_path': 'test/clip.mp4',
                'platform': 'test_platform',
                'status': 'success'
            })
            history = sm.get_history(limit=1)
            
            if len(history) > 0:
                print("✓ State manager history operations work")
                return True
        
        print("✗ State manager operations failed")
        return False
    except Exception as e:
        print(f"✗ State manager test failed: {e}")
        return False

def test_metadata_consistency():
    """Test that metadata generator supports consistent hashtags"""
    print("\nTesting metadata generator consistency...")
    
    try:
        from utils.credential_manager import CredentialManager
        from core.video_analyzer import VideoAnalyzer
        from core.metadata_generator import MetadataGenerator
        
        with open('config/settings.yaml', 'r') as f:
            settings = yaml.safe_load(f)
        
        with open('config/ai_prompts.yaml', 'r') as f:
            prompts = yaml.safe_load(f)
        
        cm = CredentialManager()
        
        # Create analyzer and metadata generator
        ai_config = settings['ai'].copy()
        ai_config['cache_dir'] = settings['paths']['cache_ai']
        
        analyzer = VideoAnalyzer(ai_config, prompts, cm)
        metadata_gen = MetadataGenerator(settings['metadata'], prompts, analyzer)
        
        # Check consistent hashtags setting
        if metadata_gen.consistent_hashtags:
            print("✓ Consistent hashtags feature is enabled by default")
        else:
            print("⚠ Consistent hashtags feature is disabled")
        
        # Test setting base hashtags
        test_hashtags = ['viral', 'trending', 'test']
        metadata_gen.set_base_hashtags(test_hashtags)
        
        if metadata_gen._base_hashtags == test_hashtags:
            print("✓ Base hashtags can be set for consistency")
            return True
        else:
            print("✗ Base hashtags setting failed")
            return False
    except Exception as e:
        print(f"✗ Metadata consistency test failed: {e}")
        return False

def test_directory_structure():
    """Test that all required directories exist"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        'config',
        'input/videos',
        'output/clips',
        'output/thumbnails',
        'output/logs',
        'cache/ai_responses',
        'cache/temp_processing',
        'src/core',
        'src/upload',
        'src/utils'
    ]
    
    success = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path} exists")
        else:
            print(f"✗ {dir_path} missing")
            success = False
    
    return success

def main():
    """Run all tests"""
    print("=" * 60)
    print("Red Clipping System Validation")
    print("=" * 60)
    
    results = []
    
    results.append(("Directory Structure", test_directory_structure()))
    results.append(("Configuration Loading", test_config_loading()))
    results.append(("Module Imports", test_imports()))
    results.append(("Credential Manager", test_credential_manager()))
    results.append(("State Manager", test_state_manager()))
    results.append(("Metadata Consistency", test_metadata_consistency()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All validation tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
