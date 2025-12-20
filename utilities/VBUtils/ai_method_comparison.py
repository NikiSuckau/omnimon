#!/usr/bin/env python3
"""
AI Background Comparison Tool
Compare different AI upscaling approaches side by side.
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_method_comparison(original_file, output_dir):
    """Create comparison between different AI methods."""
    
    # Find all versions of the same background
    base_name = original_file.name
    versions = {}
    
    # Check for different method outputs
    method_dirs = [
        ('Original', 'backgrounds'),
        ('Lightweight AI', 'backgrounds_lightweight_ai'),
        ('Advanced Hybrid', 'backgrounds_upscaled_v2'),
        ('AI Fallback', 'backgrounds_ai_upscaled')
    ]
    
    for method_name, dir_name in method_dirs:
        dir_path = Path(dir_name)
        
        if method_name == 'Original':
            file_path = dir_path / base_name
        elif method_name == 'Lightweight AI':
            file_path = dir_path / f"lightweight_ai_{base_name}"
        elif method_name == 'Advanced Hybrid':
            file_path = dir_path / f"upscaled_{base_name}"
        else:  # AI Fallback
            file_path = dir_path / f"ai_upscaled_{base_name}"
        
        if file_path.exists():
            img = cv2.imread(str(file_path))
            if img is not None:
                versions[method_name] = img
                print(f"  📷 Found {method_name}: {img.shape[1]}x{img.shape[0]}")
    
    if len(versions) < 2:
        print(f"  ⚠️  Not enough versions found for {base_name}")
        return False
    
    # Create comparison grid
    print(f"  🎨 Creating comparison grid with {len(versions)} versions...")
    
    # Resize original to match others for fair comparison
    target_size = (160, 160)
    
    processed_versions = {}
    for name, img in versions.items():
        if name == 'Original':
            # Scale up original for visual comparison
            processed_img = cv2.resize(img, target_size, interpolation=cv2.INTER_NEAREST)
        else:
            processed_img = img
        processed_versions[name] = processed_img
    
    # Calculate grid dimensions
    num_versions = len(processed_versions)
    cols = min(4, num_versions)  # Max 4 columns
    rows = (num_versions + cols - 1) // cols
    
    # Create comparison canvas
    margin = 20
    label_height = 30
    cell_width = target_size[0]
    cell_height = target_size[1] + label_height
    
    canvas_width = cols * cell_width + (cols + 1) * margin
    canvas_height = rows * cell_height + (rows + 1) * margin + 50  # Extra for title
    
    canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 240  # Light gray
    
    # Place images
    for i, (name, img) in enumerate(processed_versions.items()):
        row = i // cols
        col = i % cols
        
        x = col * (cell_width + margin) + margin
        y = row * (cell_height + margin) + margin + 40  # Leave space for title
        
        # Place image
        canvas[y:y+target_size[1], x:x+target_size[0]] = img
        
        # Add label (convert to PIL for text)
        pil_canvas = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_canvas)
        
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Add method label
        text_x = x + cell_width // 2 - len(name) * 3
        text_y = y + target_size[1] + 5
        draw.text((text_x, text_y), name, fill=(0, 0, 0), font=font)
        
        # Convert back to OpenCV
        canvas = cv2.cvtColor(np.array(pil_canvas), cv2.COLOR_RGB2BGR)
    
    # Add title
    pil_canvas = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_canvas)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 16)
    except:
        title_font = ImageFont.load_default()
    
    title = f"AI Upscaling Methods Comparison: {base_name}"
    title_x = canvas_width // 2 - len(title) * 4
    draw.text((title_x, 10), title, fill=(0, 0, 0), font=title_font)
    
    # Convert back and save
    final_canvas = cv2.cvtColor(np.array(pil_canvas), cv2.COLOR_RGB2BGR)
    
    output_path = output_dir / f"method_comparison_{base_name}"
    cv2.imwrite(str(output_path), final_canvas)
    
    print(f"  ✅ Saved comparison: {output_path.name}")
    return True

def create_all_method_comparisons():
    """Create method comparisons for all backgrounds."""
    
    print("🔍 AI Method Comparison Generator")
    print("=" * 50)
    
    original_dir = Path("backgrounds")
    comparison_dir = Path("ai_method_comparisons")
    
    comparison_dir.mkdir(exist_ok=True)
    
    # Find all original files
    original_files = list(original_dir.glob("bg_*.png"))
    
    if not original_files:
        print("❌ No original files found!")
        return
    
    print(f"📊 Creating method comparisons for {len(original_files)} backgrounds...")
    
    success_count = 0
    
    for i, original_file in enumerate(original_files, 1):
        print(f"\n📋 Processing {i}/{len(original_files)}: {original_file.name}")
        
        if create_method_comparison(original_file, comparison_dir):
            success_count += 1
    
    print(f"\n🎉 Method comparison complete!")
    print(f"   ✅ Successfully created: {success_count}/{len(original_files)} comparisons")
    print(f"   📁 Output directory: {comparison_dir.absolute()}")
    
    # Create summary info
    print("\n📊 Summary of AI Methods:")
    print("   🔸 Original: 80x160 source images")
    print("   🔸 Lightweight AI: Intelligent edge extension + depth analysis")
    print("   🔸 Advanced Hybrid: Patch-based synthesis + multi-pass inpainting")
    print("   🔸 AI Fallback: Enhanced OpenCV with multiple algorithms")

def main():
    """Main function."""
    create_all_method_comparisons()

if __name__ == "__main__":
    main()