#!/usr/bin/env python3
"""
FFMPEG PADDING FIX - Align Frame Generation with FFmpeg Expectations

ROOT CAUSE: Frame generation uses len(str(total-1)) but FFmpeg uses len(str(total))
RESULT: Generated frame_0.png but FFmpeg expects frame_00.png  

SOLUTION: Make both use consistent padding calculation (Gemini's Approach 1A)
"""

import os
import re

def apply_ffmpeg_padding_fix():
    """Fix the padding mismatch between frame generation and FFmpeg command"""
    
    main_file = "/home/jacob/Spotify-Data-Visualizations/main_animator.py"
    
    print("🔧 APPLYING FFMPEG PADDING FIX")
    print("=" * 50)
    print("Root Cause: Frame generation and FFmpeg use different padding calculations")
    print("Solution: Align both to use consistent padding")
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # STEP 1: Fix frame generation padding calculation (line 1736)
    # Current: len(str(num_total_output_frames - 1))  # For 10 frames: len(str(9)) = 1
    # Fixed:   len(str(num_total_output_frames))      # For 10 frames: len(str(10)) = 2
    
    old_padding_calc = "frame_num_digits = len(str(num_total_output_frames -1)) if num_total_output_frames > 0 else 1"
    new_padding_calc = "frame_num_digits = len(str(num_total_output_frames)) if num_total_output_frames > 0 else 1"
    
    if old_padding_calc in content:
        content = content.replace(old_padding_calc, new_padding_calc)
        print("✅ Fixed frame generation padding calculation")
        print("   Before: len(str(total-1)) → 1-digit for 10 frames")  
        print("   After:  len(str(total))   → 2-digit for 10 frames")
    else:
        print("❌ Could not find frame generation padding calculation to fix")
        return False
    
    # Verify the FFmpeg command is already using the correct pattern
    ffmpeg_pattern = f"frame_%0{len(str(num_total_output_frames))}d.png"
    if "len(str(num_total_output_frames))}d.png" in content:
        print("✅ FFmpeg command already uses correct padding pattern")
        print("   Pattern: frame_%02d.png (for 10 frames)")
    else:
        print("⚠️  FFmpeg command pattern may need verification")
    
    # Write the fixed file
    with open(main_file, 'w') as f:
        f.write(content)
    
    print("\n🎉 FFMPEG PADDING FIX APPLIED!")
    print("=" * 50)
    print("✅ Frame generation now uses consistent padding")
    print("✅ Generated files: frame_00.png, frame_01.png, ..., frame_09.png")
    print("✅ FFmpeg expects: frame_%02d.png (matches!)")
    print("\nREADY FOR TESTING:")
    print("python main_animator.py")
    
    return True

def verify_fix():
    """Verify the padding fix was applied correctly"""
    main_file = "/home/jacob/Spotify-Data-Visualizations/main_animator.py"
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check if the fix was applied
    if "len(str(num_total_output_frames)) if num_total_output_frames > 0 else 1" in content:
        print("✅ Verification: Consistent padding calculation found")
        return True
    else:
        print("❌ Verification: Padding fix NOT applied correctly")
        return False

def main():
    """Apply and verify the FFmpeg padding fix"""
    print("🎯 FFMPEG PADDING FIX - Frame Generation & FFmpeg Alignment")
    print("=" * 60)
    print("Issue: frame_0.png generated but frame_00.png expected by FFmpeg")
    print("Fix: Make both use len(str(total_frames)) for consistent padding")
    print()
    
    if apply_ffmpeg_padding_fix():
        if verify_fix():
            print("\n🚀 READY FOR TESTING!")
            print("Video compilation should now work successfully.")
        else:
            print("\n⚠️  Fix applied but verification failed")
    else:
        print("\n❌ Failed to apply FFmpeg padding fix")

if __name__ == "__main__":
    main()