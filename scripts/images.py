import os
import re
import shutil
import json

# --- Create combined images directory from attachments_dir and server_images_dir ---
attachments_dir = "/home/ollie/Documents/Obsidian Vaults/HiveMind/Attachments"
server_images_dir = "/home/ollie/Github/BeyondTheBenchServer/posts/images"
combined_images_dir = "/home/ollie/Github/BeyondTheBench/scripts/combined_images"

os.makedirs(combined_images_dir, exist_ok=True)

# List all image files in both directories (png, jpeg)
attachments_images = set(f for f in os.listdir(attachments_dir) if f.lower().endswith((".png", ".jpeg")))
server_images = set(f for f in os.listdir(server_images_dir) if f.lower().endswith((".png", ".jpeg")))

# Union of all images in both folders
all_images = attachments_images | server_images

# Remove any images from combined_images_dir that are not in the union
for f in os.listdir(combined_images_dir):
    if f.lower().endswith((".png", ".jpeg")) and f not in all_images:
        os.remove(os.path.join(combined_images_dir, f))

# Copy images from attachments_dir and server_images_dir to combined_images_dir
for image in all_images:
    src = None
    if image in server_images:
        src = os.path.join(server_images_dir, image)
    elif image in attachments_images:
        src = os.path.join(attachments_dir, image)
    dst = os.path.join(combined_images_dir, image)
    if src and not os.path.exists(dst):
        shutil.copy(src, dst)

# --- End combined images directory setup ---

# Paths
posts_dirs = [
    "/home/ollie/Github/BeyondTheBenchContent/Adventures/",
    "/home/ollie/Github/BeyondTheBenchContent/Projects/"
]
# Use combined_images_dir for processing
attachments_dir = combined_images_dir
gallery_data_file = "/home/ollie/Github/BeyondTheBench/data/gallery_images.json"

gallery_images = set()

# Step 1: Process each markdown file in the posts directory
for posts_dir in posts_dirs:
    for filename in os.listdir(posts_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(posts_dir, filename)

            with open(filepath, "r") as file:
                content = file.read()

            # Step 2: Find all image references
            all_images = re.findall(r'\!\[\[([^]]+\.(?:png|jpeg))\]\]', content)

            for image in all_images:
                # Check if the image is preceded by "X" (with or without space)
                image_pattern = rf'X!\[\[{re.escape(image)}\]\]'
                if re.search(image_pattern, content):
                    # Skip images marked with "X" in the content
                    print("Image marked, wont be added to the gallery")
                    content = content.replace(f"X![[{image}]]", f"![[{image}]]")
                else:
                    # Add to gallery images if not marked with 'X'
                    gallery_images.add(f"/images/{image}")
                    print(f"/images/{image}")

                # Replace original Obsidian-style link with Markdown image syntax
                markdown_image = f"![Image Description](/images/{image.replace(' ', '%20')})"
                content = content.replace(f"![[{image}]]", markdown_image)

            # Step 3: Write the updated content back to the markdown file
            with open(filepath, "w") as file:
                file.write(content)

# Step 4: Write gallery images to JSON
with open(gallery_data_file, "w") as json_file:
    json.dump(sorted(gallery_images), json_file, indent=2)

print("Markdown files processed and images copied successfully.")
