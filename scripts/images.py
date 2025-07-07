import os
import re
import shutil
import json
from PIL import Image
import subprocess
import sys

from PIL import Image
import subprocess
import sys

def install_pillow():
    """Install Pillow if not already installed"""
    try:
        import PIL
    except ImportError:
        print("Installing Pillow...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        import PIL

def compress_and_convert_to_webp(input_path, output_path, max_width=600, quality=85):
    """
    Compress and convert image to WebP format while preserving orientation
    """
    try:
        with Image.open(input_path) as img:
            # Use ImageOps.exif_transpose() which is the most reliable method
            # for handling EXIF orientation data
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception:
                # If exif_transpose fails, try manual EXIF orientation handling
                try:
                    exif = img._getexif()
                    if exif is not None:
                        # EXIF orientation tag is 274
                        orientation = exif.get(274)
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
                except (AttributeError, KeyError, TypeError):
                    # If no EXIF data, continue without rotation
                    pass
            
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
            
            # Determine which dimension to use for max_width constraint
            # For portrait images, we want to limit the width
            # For landscape images, we want to limit the width as well
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

def get_webp_filename(original_filename):
    """Convert original filename to WebP extension"""
    name, ext = os.path.splitext(original_filename)
    return f"{name}.webp"

print("Starting image processing script...")

# Install Pillow if needed
install_pillow()

# --- Create combined images directory from attachments_dir and server_images_dir ---
attachments_dir = "/home/ollie/Documents/Obsidian Vaults/HiveMind/Attachments"
server_images_dir = "/home/ollie/Github/BeyondTheBenchServer/posts/images"
combined_images_dir = "/home/ollie/Github/BeyondTheBenchContent/scripts/combined_images"

os.makedirs(combined_images_dir, exist_ok=True)

# List all image files in both directories (png, jpeg, webp)
try:
    attachments_images = set(f for f in os.listdir(attachments_dir) if f.lower().endswith((".png", ".jpeg", ".jpg")))
    print(f"Found {len(attachments_images)} attachment images")
except FileNotFoundError:
    print(f"Attachments directory not found: {attachments_dir}")
    attachments_images = set()

try:
    server_images = set(f for f in os.listdir(server_images_dir) if f.lower().endswith((".png", ".jpeg", ".jpg", ".webp")))
    print(f"Found {len(server_images)} server images: {list(server_images)[:5]}...")  # Show first 5
except FileNotFoundError:
    print(f"Server images directory not found: {server_images_dir}")
    server_images = set()

# Convert attachment image names to their WebP equivalents for comparison
attachments_images_webp = {get_webp_filename(img) for img in attachments_images}

# Union of all images (server images as-is, attachments as WebP)
all_images = server_images | attachments_images_webp

# Remove any images from combined_images_dir that are not in the union
for f in os.listdir(combined_images_dir):
    if f.lower().endswith((".png", ".jpeg", ".jpg", ".webp")) and f not in all_images:
        os.remove(os.path.join(combined_images_dir, f))
        print(f"Removed unused image: {f}")

# Process and copy images
for image in all_images:
    dst = os.path.join(combined_images_dir, image)
    
    if image in server_images:
        # Copy server images as-is (already processed)
        src = os.path.join(server_images_dir, image)
        if not os.path.exists(dst):
            shutil.copy(src, dst)
            print(f"Copied server image: {image}")
    else:
        # This is a WebP version of an attachment image
        # Find the original attachment image
        original_name = None
        for att_img in attachments_images:
            if get_webp_filename(att_img) == image:
                original_name = att_img
                break
        
        if original_name and not os.path.exists(dst):
            src = os.path.join(attachments_dir, original_name)
            if compress_and_convert_to_webp(src, dst):
                print(f"Compressed and converted: {original_name} -> {image}")
            else:
                print(f"Failed to process: {original_name}")

# --- End combined images directory setup ---

# Paths
posts_dirs = [
    "/home/ollie/Github/BeyondTheBenchContent/Adventures/",
    "/home/ollie/Github/BeyondTheBenchContent/Projects/"
]
# Use combined_images_dir for processing
attachments_dir = combined_images_dir
final_images_dir = "/home/ollie/Github/BeyondTheBenchContent/images"
gallery_data_file = "/home/ollie/Github/BeyondTheBenchContent/data/gallery_images.json"

# Ensure final images directory exists
os.makedirs(final_images_dir, exist_ok=True)

gallery_images = set()
used_images = set()  # Track which images are actually used

# Step 1: Process each markdown file in the posts directory
for posts_dir in posts_dirs:
    print(f"Processing directory: {posts_dir}")
    for filename in os.listdir(posts_dir):
        if filename.endswith(".md"):
            print(f"Processing file: {filename}")
            filepath = os.path.join(posts_dir, filename)

            with open(filepath, "r") as file:
                content = file.read()

            # Step 2: Find all image references (both Obsidian and Markdown formats)
            obsidian_images = re.findall(r'\!\[\[([^]]+\.(?:png|jpeg|jpg|webp))\]\]', content)
            markdown_images = re.findall(r'!\[.*?\]\(/images/([^)]+\.(?:png|jpeg|jpg|webp))\)', content)
            # Also find images with direct references (no /images/ prefix)
            direct_images = re.findall(r'!\[.*?\]\(([^)]+\.(?:png|jpeg|jpg|webp))\)', content)
            
            # Combine all formats and decode URL encoding
            all_images = obsidian_images + [img.replace('%20', ' ') for img in markdown_images] + [img.replace('%20', ' ') for img in direct_images]
            
            print(f"Found {len(all_images)} images in {filename}: {all_images}")

            for image in all_images:
                # Handle different image reference formats
                if image.startswith('/images/'):
                    # Already has /images/ prefix, extract filename
                    image_name = image[8:]  # Remove '/images/' prefix
                else:
                    image_name = image
                
                # Convert image to WebP format name if it's not already WebP
                if not image_name.lower().endswith('.webp'):
                    webp_image = get_webp_filename(image_name)
                else:
                    webp_image = image_name
                
                # Track that this image is used
                used_images.add(webp_image)
                
                # Check if the image is preceded by "X" (with or without space) in Obsidian format
                image_pattern = rf'X!\[\[{re.escape(image)}\]\]'
                if re.search(image_pattern, content):
                    # Skip images marked with "X" in the content
                    print("Image marked, wont be added to the gallery")
                    content = content.replace(f"X![[{image}]]", f"![[{webp_image}]]")
                else:
                    # Add to gallery images if not marked with 'X'
                    gallery_images.add(f"/images/{webp_image}")
                    print(f"Added to gallery: /images/{webp_image}")

                # Replace Obsidian-style links with Markdown image syntax
                if f"![[{image}]]" in content:
                    markdown_image = f"![Image Description](/images/{webp_image.replace(' ', '%20')})"
                    content = content.replace(f"![[{image}]]", markdown_image)
                
                # Update existing markdown links to use WebP format and /images/ prefix
                # Handle direct image references (no /images/ prefix)
                direct_pattern = rf'!\[([^\]]*)\]\({re.escape(image_name.replace(" ", "%20"))}\)'
                if re.search(direct_pattern, content):
                    content = re.sub(direct_pattern, rf'![\1](/images/{webp_image.replace(" ", "%20")})', content)
                
                # Handle /images/ prefixed references
                old_markdown = f"![Image Description](/images/{image_name.replace(' ', '%20')})"
                new_markdown = f"![Image Description](/images/{webp_image.replace(' ', '%20')})"
                if old_markdown in content and old_markdown != new_markdown:
                    content = content.replace(old_markdown, new_markdown)
                
                # Handle other markdown image formats (different alt text)
                markdown_pattern = rf'!\[([^\]]*)\]\(/images/{re.escape(image_name.replace(" ", "%20"))}\)'
                if re.search(markdown_pattern, content):
                    content = re.sub(markdown_pattern, rf'![\1](/images/{webp_image.replace(" ", "%20")})', content)

            # Step 3: Write the updated content back to the markdown file
            with open(filepath, "w") as file:
                file.write(content)

# Step 4: Remove unused images from combined_images_dir
for f in os.listdir(combined_images_dir):
    if f.lower().endswith((".png", ".jpeg", ".jpg", ".webp")) and f not in used_images:
        os.remove(os.path.join(combined_images_dir, f))
        print(f"Removed unused image from combined dir: {f}")

# Step 5: Copy used WebP images to final images directory and remove unused ones
# First, remove all old images from final directory
for f in os.listdir(final_images_dir):
    if f.lower().endswith((".png", ".jpeg", ".jpg", ".webp")):
        os.remove(os.path.join(final_images_dir, f))

# Copy only the used images
for image in used_images:
    src = os.path.join(combined_images_dir, image)
    dst = os.path.join(final_images_dir, image)
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"Copied to final images: {image}")

# Step 6: Write gallery images to JSON
with open(gallery_data_file, "w") as json_file:
    json.dump(sorted(gallery_images), json_file, indent=2)

print("Markdown files processed and images compressed/converted successfully.")
print(f"Total images used: {len(used_images)}")
print(f"Images in gallery: {len(gallery_images)}")
