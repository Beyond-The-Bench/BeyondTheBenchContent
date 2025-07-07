import os
import re
import shutil
import json
from PIL import Image, ImageOps
import subprocess
import sys
import hashlib

def install_pillow():
    """Install Pillow if not already installed"""
    try:
        import PIL
    except ImportError:
        print("Installing Pillow...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        import PIL

def get_file_hash(file_path):
    """Generate SHA256 hash for a file"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"Error hashing file {file_path}: {e}")
        return None

def compress_and_convert_to_webp(input_path, output_path, max_width=600, quality=85):
    """
    Compress and convert image to WebP format while preserving orientation
    """
    try:
        with Image.open(input_path) as img:
            # Use ImageOps.exif_transpose() to handle EXIF orientation
            img = ImageOps.exif_transpose(img)
            
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to max_width while maintaining aspect ratio
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save as WebP
            img.save(output_path, 'WEBP', quality=quality, optimize=True)
            return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

def main():
    print("Starting image processing script...")
    
    # Install Pillow if needed
    install_pillow()
    
    # Configuration
    obsidian_dir = "/home/ollie/Documents/Obsidian Vaults/HiveMind/Attachments"
    server_dir = "/home/ollie/Github/BeyondTheBenchServer/posts/images"
    posts_dirs = [
        "/home/ollie/Github/BeyondTheBenchContent/Adventures/",
        "/home/ollie/Github/BeyondTheBenchContent/Projects/"
    ]
    temp_dir = "/home/ollie/Github/BeyondTheBenchContent/scripts/temp_images"
    final_images_dir = "/home/ollie/Github/BeyondTheBenchContent/images"
    gallery_data_file = "/home/ollie/Github/BeyondTheBenchContent/data/gallery_images.json"
    
    # Create directories
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(final_images_dir, exist_ok=True)
    os.makedirs(os.path.dirname(gallery_data_file), exist_ok=True)
    
    # Step 1: Collect and process all images
    print("\n=== Step 1: Processing images ===")
    image_mapping = {}  # original_name -> hashed_name.webp
    
    # Process Obsidian images
    if os.path.exists(obsidian_dir):
        obsidian_images = [f for f in os.listdir(obsidian_dir) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"Found {len(obsidian_images)} Obsidian images")
        
        for img in obsidian_images:
            src_path = os.path.join(obsidian_dir, img)
            file_hash = get_file_hash(src_path)
            if file_hash:
                hashed_name = f"{file_hash}.webp"
                temp_path = os.path.join(temp_dir, hashed_name)
                
                # Process and compress
                if compress_and_convert_to_webp(src_path, temp_path):
                    # Map all possible variations of the original name
                    variations = [
                        img,
                        img.replace(' ', '%20'),
                        img.replace('%20', ' ')
                    ]
                    for variation in variations:
                        image_mapping[variation] = hashed_name
                    # Also map the hashed name to itself for idempotency
                    image_mapping[hashed_name] = hashed_name
                    print(f"Processed: {img} -> {hashed_name}")
    
    # Process server images
    if os.path.exists(server_dir):
        server_images = [f for f in os.listdir(server_dir) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        print(f"Found {len(server_images)} server images")
        
        for img in server_images:
            src_path = os.path.join(server_dir, img)
            file_hash = get_file_hash(src_path)
            if file_hash:
                hashed_name = f"{file_hash}.webp"
                temp_path = os.path.join(temp_dir, hashed_name)
                
                # Process and compress
                if compress_and_convert_to_webp(src_path, temp_path):
                    image_mapping[img] = hashed_name
                    # Also map the hashed name to itself for idempotency
                    image_mapping[hashed_name] = hashed_name
                    print(f"Processed: {img} -> {hashed_name}")
    
    print(f"Total image mappings created: {len(image_mapping)}")
    
    # Step 2: Process markdown files and update references
    print("\n=== Step 2: Processing markdown files ===")
    used_images = set()
    gallery_images = set()
    
    for posts_dir in posts_dirs:
        if not os.path.exists(posts_dir):
            continue
            
        for filename in os.listdir(posts_dir):
            if not filename.endswith('.md'):
                continue
                
            filepath = os.path.join(posts_dir, filename)
            print(f"Processing: {filename}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all image references
            found_images = []
            marked_images = set()
            
            # Extract Obsidian images
            for match in re.finditer(r'(X\s*)?!\[\[([^]]+\.(?:png|jpg|jpeg|webp))\]\]', content):
                is_marked = match.group(1) is not None
                image_name = match.group(2).replace('%20', ' ')
                found_images.append((image_name, is_marked, match.group(0)))
                if is_marked:
                    marked_images.add(image_name)
            
            # Extract Markdown images
            for match in re.finditer(r'(X\s*)?!\[([^\]]*)\]\(([^)]+\.(?:png|jpg|jpeg|webp))\)', content):
                is_marked = match.group(1) is not None
                image_path = match.group(3)
                # Remove /images/ prefix if present
                image_name = image_path.replace('/images/', '').replace('%20', ' ')
                found_images.append((image_name, is_marked, match.group(0)))
                if is_marked:
                    marked_images.add(image_name)
            
            print(f"  Found {len(found_images)} image references")
            if marked_images:
                print(f"  Found {len(marked_images)} X-marked images")
            
            # Update content with new references
            for image_name, is_marked, original_text in found_images:
                # Find the hashed name
                hashed_name = None
                
                # Try different variations to find the mapping
                # Remove .webp extension if present and try with original extensions
                base_name = image_name
                if image_name.endswith('.webp'):
                    base_name = image_name[:-5]  # Remove .webp
                
                # Try different variations of the image name
                possible_names = [
                    image_name,  # Exact match (handles already hashed names)
                    base_name + '.jpeg',  # Try with .jpeg
                    base_name + '.jpg',   # Try with .jpg  
                    base_name + '.png',   # Try with .png
                    image_name.replace(' ', '%20'),  # URL encoded
                    image_name.replace('%20', ' '),  # URL decoded
                    base_name.replace(' ', '%20') + '.jpeg',  # URL encoded with .jpeg
                    base_name.replace('%20', ' ') + '.jpeg',  # URL decoded with .jpeg
                ]
                
                for possible_name in possible_names:
                    if possible_name in image_mapping:
                        hashed_name = image_mapping[possible_name]
                        print(f"    Found mapping: {possible_name} -> {hashed_name}")
                        break
                
                if hashed_name:
                    used_images.add(hashed_name)
                    
                    # Add to gallery if not marked with X
                    if not is_marked:
                        gallery_images.add(f"/images/{hashed_name}")
                    
                    # Replace in content
                    new_reference = f"![Image Description](/images/{hashed_name})"
                    content = content.replace(original_text, new_reference)
                    print(f"    Updated: {image_name} -> {hashed_name}")
                else:
                    print(f"    Warning: No mapping found for {image_name}")
            
            # Write updated content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    # Step 3: Move used images to final directory
    print("\n=== Step 3: Moving images to final directory ===")
    
    # Clean final directory
    if os.path.exists(final_images_dir):
        for f in os.listdir(final_images_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                os.remove(os.path.join(final_images_dir, f))
    
    # Copy used images
    moved_count = 0
    for image in used_images:
        src = os.path.join(temp_dir, image)
        dst = os.path.join(final_images_dir, image)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            moved_count += 1
            print(f"  Moved: {image}")
    
    print(f"Moved {moved_count} images to final directory")
    
    # Step 4: Create gallery JSON
    print("\n=== Step 4: Creating gallery JSON ===")
    
    # Verify gallery images exist
    verified_gallery = []
    for img_path in gallery_images:
        img_name = img_path.replace('/images/', '')
        if os.path.exists(os.path.join(final_images_dir, img_name)):
            verified_gallery.append(img_path)
    
    with open(gallery_data_file, 'w', encoding='utf-8') as f:
        json.dump(sorted(verified_gallery), f, indent=2)
    
    print(f"Gallery JSON created with {len(verified_gallery)} images")
    
    # Cleanup temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"Total images processed: {len(image_mapping)}")
    print(f"Images used in posts: {len(used_images)}")
    print(f"Images in gallery: {len(verified_gallery)}")
    print(f"Images excluded from gallery: {len(used_images) - len(verified_gallery)}")

if __name__ == "__main__":
    main()
