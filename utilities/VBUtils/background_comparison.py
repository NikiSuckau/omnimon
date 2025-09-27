#!/usr/bin/env python3
"""
Background Comparison Tool
Creates side-by-side comparisons of original vs upscaled backgrounds.
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_comparison_image(original_path, upscaled_path, output_path):
    """Create a side-by-side comparison image."""
    try:
        # Load images
        original = cv2.imread(str(original_path))
        upscaled = cv2.imread(str(upscaled_path))
        
        if original is None or upscaled is None:
            print(f"❌ Could not load images for {original_path.name}")
            return False
        
        # Get dimensions
        orig_h, orig_w = original.shape[:2]
        upsc_h, upsc_w = upscaled.shape[:2]
        
        print(f"📐 Original: {orig_w}x{orig_h}, Upscaled: {upsc_w}x{upsc_h}")
        
        # Create comparison canvas
        # We'll show: Original (scaled up) | Upscaled | Difference
        canvas_width = upsc_w * 3 + 40  # 3 images + spacing
        canvas_height = max(upsc_h, orig_h * 2) + 60  # Extra space for labels
        
        canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255  # White background
        
        # Scale up original for visual comparison (simple resize)
        original_scaled = cv2.resize(original, (upsc_w, upsc_h), interpolation=cv2.INTER_NEAREST)
        
        # Calculate difference
        diff = cv2.absdiff(original_scaled, upscaled)
        diff_enhanced = cv2.multiply(diff, 3)  # Enhance differences for visibility
        
        # Position images on canvas
        y_start = 50
        
        # Original (scaled)
        x1 = 10
        canvas[y_start:y_start+upsc_h, x1:x1+upsc_w] = original_scaled
        
        # Upscaled
        x2 = x1 + upsc_w + 10
        canvas[y_start:y_start+upsc_h, x2:x2+upsc_w] = upscaled
        
        # Difference
        x3 = x2 + upsc_w + 10
        canvas[y_start:y_start+upsc_h, x3:x3+upsc_w] = diff_enhanced
        
        # Convert to PIL for text rendering
        pil_canvas = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_canvas)
        
        # Try to load a font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Add labels
        draw.text((x1 + upsc_w//2 - 40, 10), "Original (80x160→160x160)", fill=(0,0,0), font=font)
        draw.text((x2 + upsc_w//2 - 30, 10), "AI Upscaled (160x160)", fill=(0,0,0), font=font)
        draw.text((x3 + upsc_w//2 - 30, 10), "Difference (Enhanced)", fill=(0,0,0), font=font)
        
        # Add filename
        draw.text((10, canvas_height - 30), f"File: {original_path.name}", fill=(0,0,0), font=font)
        
        # Convert back to OpenCV and save
        final_canvas = cv2.cvtColor(np.array(pil_canvas), cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(output_path), final_canvas)
        
        print(f"✅ Created comparison: {output_path.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating comparison for {original_path.name}: {e}")
        return False

def create_all_comparisons():
    """Create comparison images for all backgrounds."""
    original_dir = Path("backgrounds")
    upscaled_dir = Path("backgrounds_upscaled")
    comparison_dir = Path("backgrounds_comparison")
    
    # Create comparison directory
    comparison_dir.mkdir(exist_ok=True)
    
    # Find all original background files
    original_files = list(original_dir.glob("bg_*.png"))
    
    if not original_files:
        print("❌ No original background files found!")
        return
    
    print(f"🖼️  Creating comparisons for {len(original_files)} backgrounds...")
    
    success_count = 0
    
    for original_file in original_files:
        # Find corresponding upscaled file
        upscaled_file = upscaled_dir / f"upscaled_{original_file.name}"
        
        if not upscaled_file.exists():
            print(f"⚠️  Upscaled file not found: {upscaled_file.name}")
            continue
        
        # Create comparison output filename
        comparison_file = comparison_dir / f"comparison_{original_file.name}"
        
        if create_comparison_image(original_file, upscaled_file, comparison_file):
            success_count += 1
    
    print(f"\n🎉 Comparison creation complete!")
    print(f"   ✅ Successfully created: {success_count}/{len(original_files)} comparisons")
    print(f"   📁 Output directory: {comparison_dir.absolute()}")

def create_summary_grid():
    """Create a summary grid showing all upscaled backgrounds."""
    upscaled_dir = Path("backgrounds_upscaled")
    comparison_dir = Path("backgrounds_comparison")
    
    upscaled_files = sorted(list(upscaled_dir.glob("upscaled_*.png")))
    
    if not upscaled_files:
        print("❌ No upscaled files found!")
        return
    
    print(f"🎨 Creating summary grid with {len(upscaled_files)} backgrounds...")
    
    # Calculate grid size (try to make it roughly square)
    import math
    cols = math.ceil(math.sqrt(len(upscaled_files)))
    rows = math.ceil(len(upscaled_files) / cols)
    
    print(f"📊 Grid size: {cols} x {rows}")
    
    # Load first image to get dimensions
    first_img = cv2.imread(str(upscaled_files[0]))
    if first_img is None:
        print("❌ Could not load first image")
        return
    
    img_h, img_w = first_img.shape[:2]
    
    # Create grid canvas
    grid_width = cols * img_w + (cols + 1) * 10  # Images + spacing
    grid_height = rows * img_h + (rows + 1) * 10  # Images + spacing
    
    grid_canvas = np.ones((grid_height, grid_width, 3), dtype=np.uint8) * 240  # Light gray background
    
    # Place images on grid
    for i, img_file in enumerate(upscaled_files):
        img = cv2.imread(str(img_file))
        if img is None:
            continue
        
        row = i // cols
        col = i % cols
        
        x = col * (img_w + 10) + 10
        y = row * (img_h + 10) + 10
        
        grid_canvas[y:y+img_h, x:x+img_w] = img
        
        print(f"  📍 Placed {img_file.name} at position ({col}, {row})")
    
    # Save grid
    grid_output = comparison_dir / "summary_grid_all_backgrounds.png"
    cv2.imwrite(str(grid_output), grid_canvas)
    
    print(f"✅ Created summary grid: {grid_output.name}")
    print(f"   📐 Grid size: {grid_width}x{grid_height} pixels")

def main():
    """Main function."""
    print("📊 Background Comparison Tool")
    print("=" * 40)
    
    # Create individual comparisons
    create_all_comparisons()
    
    print("\n" + "=" * 40)
    
    # Create summary grid
    create_summary_grid()

if __name__ == "__main__":
    main()