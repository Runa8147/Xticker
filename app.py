import streamlit as st
import streamlit_cropper as st_cropper
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
from rembg import remove

# -------------------------
# CONFIGURATION
# -------------------------
st.set_page_config(page_title="Xtickr Sticker Maker", layout="wide")
st.title("🖼️ Xtickr Sticker Maker for WhatsApp")


# -------------------------
# HELPER FUNCTIONS
# -------------------------
def opacity_to_255(opacity_percent):
    """Convert opacity percentage to 0-255 alpha value."""
    return int(255 * (opacity_percent / 100))


def get_font(size):
    """Load a font, fallback to default if not available."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except:
            return ImageFont.load_default()


# -------------------------
# STEP 1: UPLOAD IMAGE
# -------------------------
def upload_image():
    """Handle image upload."""
    uploaded_file = st.sidebar.file_uploader("1. Upload an Image", type=["png", "jpg", "jpeg"])
    if not uploaded_file:
        st.info("Please upload an image to begin.")
        st.stop()
    return Image.open(uploaded_file)


# -------------------------
# STEP 2: CROP IMAGE
# -------------------------
def crop_image(image):
    """Allow user to crop the image using interactive cropper."""
    st.sidebar.subheader("2. Crop Image")
    realtime_update = st.sidebar.checkbox("Update in Real Time", value=True)
    box_color = st.sidebar.color_picker("Box Color", value='#00FF00')
    aspect_choice = st.sidebar.radio(
        "Aspect Ratio",
        options=["1:1", "16:9", "4:3", "2:3", "Free"],
        format_func=lambda x: x
    )
    aspect_dict = {
        "1:1": (1, 1),
        "16:9": (16, 9),
        "4:3": (4, 3),
        "2:3": (2, 3),
        "Free": None
    }
    aspect_ratio = aspect_dict[aspect_choice]

    st.info("Drag to select crop area and double-click to confirm.")
    cropped_img = st_cropper(
        image,
        realtime_update=realtime_update,
        box_color=box_color,
        aspect_ratio=aspect_ratio,
        key='cropper'
    )

    if cropped_img is None:
        st.warning("Please complete the cropping step.")
        st.stop()
    return cropped_img


# -------------------------
# STEP 3: REMOVE BACKGROUND
# -------------------------
def remove_background(image):
    """Remove background using rembg library."""
    st.sidebar.subheader("3. Remove Background")
    remove_bg = st.sidebar.checkbox("Remove Background", value=True)

    if not remove_bg:
        return image.convert("RGBA")

    try:
        # Ensure input is a PIL Image
        if not isinstance(image, Image.Image):
            st.error("Invalid image format after cropping.")
            st.stop()

        # Remove background (directly accepts PIL image)
        output = remove(image)
        st.sidebar.success("✅ Background removed!")
        return output

    except Exception as e:
        st.sidebar.error(f"❌ Failed to remove background: {str(e)}")

# -------------------------
# STEP 4: ADD TEXT
# -------------------------
def add_text_to_image(image):
    """Add customizable text to the image."""
    st.sidebar.subheader("4. Add Text")
    text_input = st.sidebar.text_input("Text to Add", value="")
    text_size = st.sidebar.slider("Text Size", min_value=10, max_value=100, value=40)
    text_color = st.sidebar.color_picker("Text Color", value="#FFFFFF")
    text_opacity = st.sidebar.slider("Text Opacity", min_value=0, max_value=100, value=100)
    positioning_mode = st.sidebar.radio(
        "Text Position",
        ["Bottom", "Top", "Center", "Custom"]
    )

    # Parse color and opacity
    r = int(text_color[1:3], 16)
    g = int(text_color[3:5], 16)
    b = int(text_color[5:7], 16)
    a = opacity_to_255(text_opacity)
    fill_color = (r, g, b, a)

    # Copy image for editing
    result_img = image.copy()
    if text_input.strip():
        draw = ImageDraw.Draw(result_img)
        font = get_font(text_size)

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text_input, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        img_w, img_h = result_img.size

        # Position logic
        if positioning_mode == "Bottom":
            position = ((img_w - text_width) // 2, img_h - text_height - 10)
        elif positioning_mode == "Top":
            position = ((img_w - text_width) // 2, 10)
        elif positioning_mode == "Center":
            position = ((img_w - text_width) // 2, (img_h - text_height) // 2)
        else:  # Custom: simulate placement
            st.warning("Custom text placement: adjust using preview below.")
            # Placeholder to help visualize
            temp_img = result_img.copy()
            draw_temp = ImageDraw.Draw(temp_img)
            draw_temp.text(((img_w - text_width)//2, (img_h - text_height)//2),
                           text_input, font=font, fill=fill_color)
            st_cropper(temp_img, box_color="#FF0000", aspect_ratio=None,
                       realtime_update=True, key="text_placement")
            position = ((img_w - text_width) // 2, (img_h - text_height) // 2)

        # Draw final text
        draw.text(position, text_input, font=font, fill=fill_color)

    return result_img


# -------------------------
# STEP 5: GENERATE STICKER
# -------------------------
def make_whatsapp_sticker(img, name_prefix="xtickr_sticker"):
    """Resize to 512x512 and save as optimized WEBP under 100KB."""
    img = img.convert("RGBA").resize((512, 512), Image.LANCZOS)
    
    unique_id = uuid.uuid4().hex[:8]
    file_name = f"{name_prefix}_{unique_id}.webp"
    
    quality = 90
    while quality >= 20:
        img.save(file_name, "WEBP", quality=quality, method=6)
        if os.path.getsize(file_name) <= 100 * 1024:  # ≤ 100KB
            break
        quality -= 10

    return file_name


# -------------------------
# MAIN APP FLOW
# -------------------------
def main():
    # Step 1: Upload
    image = upload_image()

    # Step 2: Crop
    cropped_img = crop_image(image)

    # Step 3: Background removal
    bg_removed_img = remove_background(cropped_img)

    # Show preview after bg removal
    st.sidebar.image(bg_removed_img, caption="After Crop & BG Removal", use_column_width=True)

    # Step 4: Add text
    final_img = add_text_to_image(bg_removed_img)

    # Show final preview before export
    st.subheader("🎨 Final Sticker Preview")
    st.image(final_img, caption="Preview (before resizing to 512×512)", use_column_width=True)

    # Step 5: Export
    if st.sidebar.button("✅ Create Sticker"):
        output_file = make_whatsapp_sticker(final_img)
        st.success(f"🎉 Sticker created successfully: `{output_file}`")
        st.image(output_file, caption="✅ Your WhatsApp Sticker", use_column_width=True)

        # Download button
        with open(output_file, "rb") as f:
            st.download_button(
                label="💾 Download Sticker",
                data=f.read(),
                file_name=output_file,
                mime="image/webp"
            )


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":

    main()
