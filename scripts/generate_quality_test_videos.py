#!/usr/bin/env python3
"""
Quality test video generation script for Green-Code FX.

This script generates a comprehensive set of test videos for manual quality validation,
including various durations, parameters, and edge cases.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.video_generator import VideoGenerator
from src.config import config


def setup_environment():
    """Setup the testing environment."""
    # Ensure headless operation
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    
    # Ensure output directories exist
    config.ensure_directories()
    
    print(f"Quality test environment setup:")
    print(f"  SDL Video Driver: {os.environ.get('SDL_VIDEODRIVER', 'default')}")
    print(f"  Output Directory: {config.OUTPUT_DIR}")


def generate_typing_test_videos(video_generator):
    """Generate typing effect test videos for quality validation."""
    print("\n" + "="*60)
    print("GENERATING TYPING EFFECT TEST VIDEOS")
    print("="*60)
    
    test_cases = [
        {
            "name": "Short Duration Test",
            "job_id": "quality_typing_short",
            "duration": 30,
            "description": "30-second test for basic functionality"
        },
        {
            "name": "Standard Duration Test", 
            "job_id": "quality_typing_standard",
            "duration": 60,
            "description": "1-minute test for typical use case"
        },
        {
            "name": "Extended Duration Test",
            "job_id": "quality_typing_extended", 
            "duration": 90,
            "description": "90-second test for loop behavior"
        },
        {
            "name": "Minimum Duration Test",
            "job_id": "quality_typing_minimum",
            "duration": 10,
            "description": "Minimum duration edge case"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🎬 Generating: {test_case['name']}")
        print(f"   Duration: {test_case['duration']}s")
        print(f"   Description: {test_case['description']}")
        
        try:
            start_time = time.perf_counter()
            
            output_file = video_generator.generate_typing_effect(
                job_id=test_case["job_id"],
                duration=test_case["duration"],
                source_file="snake_code.txt",
                output_format="mp4"
            )
            
            generation_time = time.perf_counter() - start_time
            
            # Get file info
            file_path = config.OUTPUT_DIR / output_file
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            result = {
                "test_case": test_case["name"],
                "job_id": test_case["job_id"],
                "duration": test_case["duration"],
                "output_file": output_file,
                "file_size_mb": file_size / (1024 * 1024),
                "generation_time": generation_time,
                "performance_ratio": generation_time / test_case["duration"],
                "status": "SUCCESS"
            }
            
            print(f"   ✅ Generated: {output_file}")
            print(f"   📁 Size: {result['file_size_mb']:.1f} MB")
            print(f"   ⏱️  Time: {generation_time:.1f}s ({result['performance_ratio']:.1f}x realtime)")
            
        except Exception as e:
            result = {
                "test_case": test_case["name"],
                "job_id": test_case["job_id"],
                "duration": test_case["duration"],
                "error": str(e),
                "status": "FAILED"
            }
            print(f"   ❌ Failed: {e}")
        
        results.append(result)
    
    return results


def generate_matrix_test_videos(video_generator):
    """Generate Matrix effect test videos for quality validation."""
    print("\n" + "="*60)
    print("GENERATING MATRIX EFFECT TEST VIDEOS")
    print("="*60)
    
    test_cases = [
        {
            "name": "Standard Loop Test",
            "job_id": "quality_matrix_standard",
            "duration": 15,
            "loop_seamless": True,
            "description": "Standard 15-second seamless loop"
        },
        {
            "name": "Short Duration Test",
            "job_id": "quality_matrix_short",
            "duration": 5,
            "loop_seamless": True,
            "description": "Short 5-second test"
        },
        {
            "name": "Extended Duration Test",
            "job_id": "quality_matrix_extended",
            "duration": 30,
            "loop_seamless": True,
            "description": "Extended 30-second test"
        },
        {
            "name": "Non-Seamless Test",
            "job_id": "quality_matrix_non_seamless",
            "duration": 15,
            "loop_seamless": False,
            "description": "15-second non-seamless test"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🌧️  Generating: {test_case['name']}")
        print(f"   Duration: {test_case['duration']}s")
        print(f"   Seamless: {test_case['loop_seamless']}")
        print(f"   Description: {test_case['description']}")
        
        try:
            start_time = time.perf_counter()
            
            output_file = video_generator.generate_matrix_rain(
                job_id=test_case["job_id"],
                duration=test_case["duration"],
                loop_seamless=test_case["loop_seamless"],
                output_format="mp4"
            )
            
            generation_time = time.perf_counter() - start_time
            
            # Get file info
            file_path = config.OUTPUT_DIR / output_file
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            result = {
                "test_case": test_case["name"],
                "job_id": test_case["job_id"],
                "duration": test_case["duration"],
                "loop_seamless": test_case["loop_seamless"],
                "output_file": output_file,
                "file_size_mb": file_size / (1024 * 1024),
                "generation_time": generation_time,
                "performance_ratio": generation_time / test_case["duration"],
                "status": "SUCCESS"
            }
            
            print(f"   ✅ Generated: {output_file}")
            print(f"   📁 Size: {result['file_size_mb']:.1f} MB")
            print(f"   ⏱️  Time: {generation_time:.1f}s ({result['performance_ratio']:.1f}x realtime)")
            
        except Exception as e:
            result = {
                "test_case": test_case["name"],
                "job_id": test_case["job_id"],
                "duration": test_case["duration"],
                "loop_seamless": test_case["loop_seamless"],
                "error": str(e),
                "status": "FAILED"
            }
            print(f"   ❌ Failed: {e}")
        
        results.append(result)
    
    return results


def generate_test_report(typing_results, matrix_results):
    """Generate a comprehensive test report."""
    print("\n" + "="*60)
    print("QUALITY TEST VIDEO GENERATION REPORT")
    print("="*60)
    
    all_results = typing_results + matrix_results
    successful = [r for r in all_results if r["status"] == "SUCCESS"]
    failed = [r for r in all_results if r["status"] == "FAILED"]
    
    print(f"Total Test Cases: {len(all_results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        total_size = sum(r.get("file_size_mb", 0) for r in successful)
        avg_performance = sum(r.get("performance_ratio", 0) for r in successful) / len(successful)
        
        print(f"\nSUCCESSFUL GENERATIONS:")
        print(f"  Total File Size: {total_size:.1f} MB")
        print(f"  Average Performance: {avg_performance:.1f}x realtime")
        
        print(f"\n  Generated Files:")
        for result in successful:
            print(f"    {result['output_file']} ({result['file_size_mb']:.1f} MB)")
    
    if failed:
        print(f"\nFAILED GENERATIONS:")
        for result in failed:
            print(f"  {result['test_case']}: {result.get('error', 'Unknown error')}")
    
    # Save detailed report
    report_data = {
        "timestamp": time.time(),
        "summary": {
            "total_tests": len(all_results),
            "successful": len(successful),
            "failed": len(failed)
        },
        "typing_results": typing_results,
        "matrix_results": matrix_results
    }
    
    report_file = config.OUTPUT_DIR / "quality_test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📊 Detailed report saved: {report_file}")
    
    # Generate validation checklist
    checklist_file = config.OUTPUT_DIR / "quality_validation_checklist.md"
    with open(checklist_file, 'w') as f:
        f.write("# Quality Validation Checklist\n\n")
        f.write("Generated test videos for manual quality validation.\n\n")
        f.write("## Test Videos Generated\n\n")
        
        f.write("### Typing Effect Videos\n")
        for result in typing_results:
            if result["status"] == "SUCCESS":
                f.write(f"- [ ] **{result['test_case']}**: `{result['output_file']}` ({result['duration']}s, {result['file_size_mb']:.1f}MB)\n")
        
        f.write("\n### Matrix Effect Videos\n")
        for result in matrix_results:
            if result["status"] == "SUCCESS":
                f.write(f"- [ ] **{result['test_case']}**: `{result['output_file']}` ({result['duration']}s, {result['file_size_mb']:.1f}MB)\n")
        
        f.write("\n## Validation Steps\n\n")
        f.write("For each video above:\n")
        f.write("1. [ ] Visual quality check\n")
        f.write("2. [ ] Chroma key compatibility test\n")
        f.write("3. [ ] Cross-platform playback test\n")
        f.write("4. [ ] Technical specifications verification\n\n")
        f.write("See `docs/MANUAL_QUALITY_VALIDATION.md` for detailed validation procedures.\n")
    
    print(f"📋 Validation checklist saved: {checklist_file}")
    
    return len(failed) == 0


def main():
    """Main quality test video generation workflow."""
    print("Green-Code FX Quality Test Video Generator")
    print("=" * 60)
    
    try:
        # Setup environment
        setup_environment()
        
        # Create video generator
        video_generator = VideoGenerator()
        
        # Generate test videos
        typing_results = generate_typing_test_videos(video_generator)
        matrix_results = generate_matrix_test_videos(video_generator)
        
        # Generate report
        success = generate_test_report(typing_results, matrix_results)
        
        if success:
            print(f"\n🎉 All quality test videos generated successfully!")
            print(f"   Review generated files and follow manual validation procedures")
            print(f"   See: docs/MANUAL_QUALITY_VALIDATION.md")
            return 0
        else:
            print(f"\n⚠️  Some test video generation failed!")
            print(f"   Check the report for details")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Quality test generation interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Quality test generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
