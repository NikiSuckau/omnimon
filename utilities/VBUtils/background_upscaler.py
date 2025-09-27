#!/usr/bin/env python3
"""
AI-Powered Background Upscaler for VB Utils
Upscales background images from 80x160 to 160x160 using AI inpainting.
"""

import os
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter
import argparse

def check_dependencies():
    """Check if required packages are installed."""
    try:
        import cv2
        print("✅ OpenCV available")
    except ImportError:
        print("❌ OpenCV not found. Install with: pip install opencv-python")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL available")
    except ImportError:
        print("❌ PIL not found. Install with: pip install pillow")
        return False
    
    return True

def load_image(image_path):
    """Load image and verify dimensions."""
    try:
        # Load with PIL first to check format
        pil_image = Image.open(image_path)
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        height, width = cv_image.shape[:2]
        print(f"📐 Loaded image: {width}x{height}")
        
        if width != 80 or height != 160:
            print(f"⚠️  Warning: Expected 80x160, got {width}x{height}")
        
        return cv_image, pil_image
    except Exception as e:
        print(f"❌ Error loading {image_path}: {e}")
        return None, None

def create_upscaled_canvas(original_image):
    """Create a 160x160 canvas with the original image centered."""
    height, width = original_image.shape[:2]
    
    # Create 160x160 canvas
    canvas = np.zeros((160, 160, 3), dtype=np.uint8)
    
    # Calculate position to center the original image
    # Original is 80x160, target is 160x160
    # We need to add 40 pixels on each side horizontally
    x_offset = (160 - width) // 2  # Should be 40
    y_offset = (160 - height) // 2  # Should be 0 (since 160-160=0)
    
    print(f"📍 Centering image at offset: ({x_offset}, {y_offset})")
    
    # Place original image on canvas
    canvas[y_offset:y_offset+height, x_offset:x_offset+width] = original_image
    
    return canvas, x_offset, y_offset

def create_inpainting_mask(width=160, height=160, center_width=80):
    """Create mask for inpainting - mark areas that need to be filled."""
    mask = np.zeros((height, width), dtype=np.uint8)
    
    # Calculate the areas that need inpainting (left and right sides)
    x_offset = (width - center_width) // 2
    
    # Mark left side for inpainting
    mask[:, :x_offset] = 255
    
    # Mark right side for inpainting  
    mask[:, x_offset + center_width:] = 255
    
    print(f"🎭 Created inpainting mask: filling {x_offset} pixels on each side")
    return mask

def apply_advanced_inpainting(image, mask):
    """Apply advanced multi-pass inpainting with edge preservation."""
    print("🤖 Applying advanced AI inpainting...")
    
    # Multi-scale inpainting approach
    results = []
    
    # Pass 1: Large radius for overall structure
    print("  🎯 Pass 1: Structural inpainting (large radius)...")
    result1 = cv2.inpaint(image, mask, 15, cv2.INPAINT_TELEA)
    results.append(('structural', result1))
    
    # Pass 2: Medium radius for texture details
    print("  🎨 Pass 2: Texture inpainting (medium radius)...")
    result2 = cv2.inpaint(image, mask, 8, cv2.INPAINT_NS)
    results.append(('texture', result2))
    
    # Pass 3: Small radius for fine details
    print("  ✨ Pass 3: Detail inpainting (small radius)...")
    result3 = cv2.inpaint(result1, mask, 3, cv2.INPAINT_TELEA)
    results.append(('detail', result3))
    
    # Blend all results with weighted average
    final = np.zeros_like(image, dtype=np.float32)
    weights = [0.4, 0.35, 0.25]  # Favor structural, then texture, then detail
    
    for (name, result), weight in zip(results, weights):
        final += result.astype(np.float32) * weight
    
    return final.astype(np.uint8), results

def apply_patch_based_inpainting(image, mask):
    """Apply patch-based texture synthesis for natural content generation."""
    print("🧩 Applying patch-based texture synthesis...")
    
    height, width = image.shape[:2]
    result = image.copy()
    
    # Find the boundary between known and unknown regions
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    boundary = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, kernel)
    
    # Get known region (original content area)
    known_region = (mask == 0)
    
    # Patch-based filling for left side
    print("  🎯 Filling left region with patch synthesis...")
    left_mask = mask.copy()
    left_mask[:, 80:] = 0  # Only fill left 80 pixels
    
    if np.any(left_mask > 0):
        # Sample patches from the right edge of known content
        source_start = 40  # Start of original content
        source_patches = []
        
        # Extract overlapping patches from the known region
        patch_size = 8
        for y in range(0, height - patch_size, 4):
            for x in range(source_start, source_start + 20, 2):  # Sample from left edge of content
                if x + patch_size < width:
                    patch = image[y:y+patch_size, x:x+patch_size]
                    source_patches.append((patch, x, y))
        
        # Fill left region with best matching patches
        for y in range(0, height, patch_size//2):
            for x in range(0, 40, patch_size//2):  # Fill left 40 pixels
                if left_mask[y, x] > 0 and y + patch_size < height and x + patch_size < width:
                    
                    # Find best matching patch based on edge similarity
                    best_patch = None
                    best_score = float('inf')
                    
                    # Context region for matching
                    context_region = result[max(0, y-2):y+patch_size+2, max(0, x-2):x+patch_size+2]
                    
                    for patch, orig_x, orig_y in source_patches[:50]:  # Limit for performance
                        # Calculate similarity score
                        if patch.shape == (patch_size, patch_size, 3):
                            # Simple color distance
                            score = np.mean(np.abs(patch.astype(float) - result[y:y+patch_size, source_start:source_start+patch_size].astype(float)))
                            
                            if score < best_score:
                                best_score = score
                                best_patch = patch
                    
                    if best_patch is not None:
                        # Blend the patch smoothly
                        alpha = 0.8
                        result[y:y+patch_size, x:x+patch_size] = (
                            alpha * best_patch + 
                            (1-alpha) * result[y:y+patch_size, x:x+patch_size]
                        ).astype(np.uint8)
    
    # Similar process for right side
    print("  🎯 Filling right region with patch synthesis...")
    right_mask = mask.copy()
    right_mask[:, :120] = 0  # Only fill right side
    
    if np.any(right_mask > 0):
        # Sample patches from the left edge of known content  
        source_end = 120  # End of original content
        
        for y in range(0, height, patch_size//2):
            for x in range(120, width, patch_size//2):  # Fill right side
                if right_mask[y, x] > 0 and y + patch_size < height and x + patch_size < width:
                    
                    # Use mirrored content from left side for consistency
                    mirror_x = source_end - (x - 120) - patch_size
                    if mirror_x >= 40 and mirror_x + patch_size <= source_end:
                        mirror_patch = image[y:y+patch_size, mirror_x:mirror_x+patch_size]
                        
                        # Add some variation to avoid perfect mirroring
                        variation = np.random.normal(0, 5, mirror_patch.shape).astype(np.int8)
                        varied_patch = np.clip(mirror_patch.astype(int) + variation, 0, 255).astype(np.uint8)
                        
                        # Blend smoothly
                        alpha = 0.7
                        result[y:y+patch_size, x:x+patch_size] = (
                            alpha * varied_patch + 
                            (1-alpha) * result[y:y+patch_size, x:x+patch_size]
                        ).astype(np.uint8)
    
    return result

def apply_seamless_inpainting(image, mask):
    """Apply seamless inpainting with gradient-based blending."""
    print("🎨 Applying seamless AI inpainting...")
    
    # Step 1: Use patch-based synthesis first
    patch_result = apply_patch_based_inpainting(image, mask)
    
    # Step 2: Refine with traditional inpainting
    print("  ✨ Refining with advanced inpainting...")
    
    # Create a refined mask for final inpainting (only edges)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    edge_mask = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, kernel)
    
    # Apply final inpainting pass to smooth transitions
    final_result = cv2.inpaint(patch_result, edge_mask, 5, cv2.INPAINT_TELEA)
    
    # Step 3: Color correction and blending
    print("  🎨 Final color harmonization...")
    
    # Ensure color consistency across the image
    # Apply slight gaussian blur to the filled regions for smoothness
    blur_mask = mask.astype(np.float32) / 255.0
    blur_mask = cv2.GaussianBlur(blur_mask, (5, 5), 2)
    blur_mask = np.stack([blur_mask, blur_mask, blur_mask], axis=-1)
    
    blurred_result = cv2.GaussianBlur(final_result, (3, 3), 1)
    
    # Blend blurred filled areas with sharp original areas
    result = (blur_mask * blurred_result + (1 - blur_mask) * final_result).astype(np.uint8)
    
    return result

def apply_symmetrical_extension(image, x_offset):
    """Apply symmetrical extension for more natural results."""
    print("🪞 Applying symmetrical extension...")
    
    height, width = image.shape[:2]
    
    # Create result image
    result = image.copy()
    
    # For left side, mirror the leftmost part of the original content
    left_source = image[:, x_offset:x_offset+20]  # Take 20 pixels from left edge
    left_flipped = cv2.flip(left_source, 1)  # Horizontal flip
    
    # Blend the mirrored content into the left area
    for i in range(x_offset):
        alpha = (x_offset - i) / x_offset  # Fade out as we go further from center
        blend_col = left_flipped[:, min(i, left_flipped.shape[1]-1)]
        original_col = result[:, i]
        result[:, i] = (alpha * blend_col + (1-alpha) * original_col).astype(np.uint8)
    
    # Same for right side
    right_source = image[:, x_offset+60:x_offset+80]  # Take 20 pixels from right edge
    right_flipped = cv2.flip(right_source, 1)
    
    for i in range(x_offset):
        pos = x_offset + 80 + i
        if pos < width:
            alpha = (i + 1) / x_offset
            blend_col = right_flipped[:, min(i, right_flipped.shape[1]-1)]
            original_col = result[:, pos]
            result[:, pos] = (alpha * blend_col + (1-alpha) * original_col).astype(np.uint8)
    
    return result

def upscale_background(input_path, output_dir, method='hybrid'):
    """Upscale a single background image."""
    print(f"\n🖼️  Processing: {input_path.name}")
    
    # Load original image
    cv_image, pil_image = load_image(input_path)
    if cv_image is None:
        return False
    
    # Create upscaled canvas with centered original
    canvas, x_offset, y_offset = create_upscaled_canvas(cv_image)
    
    # Create inpainting mask
    mask = create_inpainting_mask()
    
    if method == 'inpainting':
        # Use advanced multi-pass inpainting
        result, _ = apply_advanced_inpainting(canvas, mask)
    elif method == 'content_aware':
        # Use seamless inpainting
        result = apply_seamless_inpainting(canvas, mask)
    elif method == 'symmetrical':
        # Use symmetrical extension
        result = apply_symmetrical_extension(canvas, x_offset)
    else:  # hybrid method
        # Use the new seamless approach as default
        print("🔀 Using advanced seamless approach...")
        result = apply_seamless_inpainting(canvas, mask)
    
    # Save result
    output_path = output_dir / f"upscaled_{input_path.name}"
    cv2.imwrite(str(output_path), result)
    
    print(f"✅ Saved upscaled image: {output_path.name}")
    return True

def process_all_backgrounds(input_dir, output_dir, method='hybrid'):
    """Process all background images in the directory."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory
    output_path.mkdir(exist_ok=True)
    
    # Find all PNG files
    png_files = list(input_path.glob("bg_*.png"))
    
    if not png_files:
        print("❌ No background images found!")
        return
    
    print(f"📊 Found {len(png_files)} background images to process")
    print(f"🎯 Using method: {method}")
    
    success_count = 0
    
    for png_file in png_files:
        if upscale_background(png_file, output_path, method):
            success_count += 1
    
    print(f"\n🎉 Processing complete!")
    print(f"   ✅ Successfully processed: {success_count}/{len(png_files)} images")
    print(f"   📁 Output directory: {output_path.absolute()}")

def main():
    """Main function with command line arguments."""
    parser = argparse.ArgumentParser(description='AI-powered background upscaler')
    parser.add_argument('--input', '-i', default='backgrounds', 
                       help='Input directory with background images')
    parser.add_argument('--output', '-o', default='backgrounds_upscaled',
                       help='Output directory for upscaled images')
    parser.add_argument('--method', '-m', default='hybrid',
                       choices=['inpainting', 'content_aware', 'symmetrical', 'hybrid'],
                       help='Upscaling method to use')
    
    args = parser.parse_args()
    
    print("🤖 AI-Powered Background Upscaler")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Process backgrounds
    process_all_backgrounds(args.input, args.output, args.method)

if __name__ == "__main__":
    main()