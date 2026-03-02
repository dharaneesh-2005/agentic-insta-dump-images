"""AI Instagram Dump Generator - Streamlit Frontend."""
import streamlit as st
from pathlib import Path
import tempfile
import time
from PIL import Image
import io
import base64

from src.batch_generator import BatchGenerator, create_zip_archive
from src.prompt_engine import PromptEngine
import config

# Page configuration
st.set_page_config(
    page_title="AI Instagram Dump Generator",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
    }
    .stProgress > div > div > div > div {
        background-color: #4ECDC4;
    }
    .gallery-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 1rem;
    }
    .image-card {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = []
    if 'generation_complete' not in st.session_state:
        st.session_state.generation_complete = False
    if 'zip_path' not in st.session_state:
        st.session_state.zip_path = None


def save_uploaded_file(uploaded_file, temp_dir: Path) -> Path:
    """Save an uploaded file to temp directory."""
    file_path = temp_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    return file_path


def progress_callback(current: int, total: int, status: str):
    """Update progress in Streamlit."""
    progress = current / total
    st.session_state.progress_bar.progress(progress, text=status)


def main():
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">📸 AI Instagram Dump Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Upload 2 photos and generate 10-20 aesthetic Instagram dump images</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Gender selection
        gender = st.radio(
            "Select Gender:",
            options=list(config.GENDERS.keys()),
            format_func=lambda x: config.GENDERS[x],
            horizontal=True
        )
        
        # Theme selection
        theme = st.selectbox(
            "Select Theme:",
            options=list(config.THEMES.keys()),
            format_func=lambda x: config.THEMES[x]
        )
        
        # Number of images
        num_images = st.slider(
            "Number of Images:",
            min_value=config.MIN_BATCH_SIZE,
            max_value=config.MAX_BATCH_SIZE,
            value=config.DEFAULT_BATCH_SIZE
        )
        
        st.divider()
        
        # ComfyUI status
        st.subheader("🔌 ComfyUI Status")
        try:
            import requests
            response = requests.get(f"{config.COMFYUI_BASE_URL}/system_stats", timeout=5)
            if response.status_code == 200:
                st.success(f"✅ Connected to {config.COMFYUI_BASE_URL}")
            else:
                st.warning(f"⚠️ ComfyUI returned status {response.status_code}")
        except Exception as e:
            st.error(f"❌ Cannot connect to ComfyUI at {config.COMFYUI_BASE_URL}")
            st.info("Make sure ComfyUI is running with --listen flag")
    
    # Main content area
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 Upload Photos")
        
        # File uploaders
        uploaded_file_1 = st.file_uploader(
            "Upload Face Photo",
            type=config.SUPPORTED_IMAGE_FORMATS,
            key="face_photo"
        )
        
        uploaded_file_2 = st.file_uploader(
            "Upload Full Body Photo",
            type=config.SUPPORTED_IMAGE_FORMATS,
            key="body_photo"
        )
        
        # Preview uploaded images
        if uploaded_file_1:
            st.image(uploaded_file_1, caption="Face Photo Preview", width=None)
        
        if uploaded_file_2:
            st.image(uploaded_file_2, caption="Body Photo Preview", width=None)
    
    with col2:
        st.subheader("🎨 Selected Style")
        
        # Show selected theme info
        st.info(f"**Theme:** {config.THEMES[theme]}\n\n**Gender:** {config.GENDERS[gender]}\n\n**Images:** {num_images}")
        
        # Sample prompts preview
        prompt_engine = PromptEngine()
        sample_prompts = prompt_engine.get_prompts(gender, theme, min(3, num_images))
        
        with st.expander("👁️ Preview Sample Prompts"):
            for i, prompt in enumerate(sample_prompts, 1):
                st.text_area(f"Sample {i}", prompt, height=80, disabled=True)
    
    # Generation button
    st.divider()
    
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    
    with generate_col2:
        generate_button = st.button(
            "🚀 Generate Instagram Dump",
            type="primary",
            use_container_width=True,
            disabled=not (uploaded_file_1 and uploaded_file_2)
        )
    
    # Generation process
    if generate_button:
        if not uploaded_file_1 or not uploaded_file_2:
            st.error("Please upload both photos before generating!")
        else:
            # Create temp directory for uploads
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Save uploaded files
                image_paths = [
                    save_uploaded_file(uploaded_file_1, temp_path),
                    save_uploaded_file(uploaded_file_2, temp_path)
                ]
                
                # Initialize generator
                generator = BatchGenerator()
                
                # Validate images
                is_valid, error_msg = generator.validate_images(image_paths)
                if not is_valid:
                    st.error(error_msg)
                else:
                    # Create progress bar
                    st.session_state.progress_bar = st.progress(0, text="Starting generation...")
                    
                    try:
                        # Generate images
                        results = generator.generate_batch(
                            image_paths=image_paths,
                            gender=gender,
                            theme=theme,
                            count=num_images,
                            progress_callback=progress_callback
                        )
                        
                        st.session_state.generated_images = results
                        st.session_state.generation_complete = True
                        
                        # Create ZIP archive
                        if results:
                            timestamp = int(time.time())
                            zip_path = config.OUTPUT_DIR / f"{gender}_{theme}_{timestamp}.zip"
                            create_zip_archive(results, zip_path, gender, theme)
                            st.session_state.zip_path = zip_path
                        
                        st.success(f"✅ Successfully generated {len(results)} images!")
                        
                    except Exception as e:
                        st.error(f"Generation failed: {str(e)}")
                        st.info("Make sure ComfyUI is running and the workflow file is properly configured.")
    
    # Display results
    if st.session_state.generation_complete and st.session_state.generated_images:
        st.divider()
        st.subheader("🎉 Your Instagram Dump")
        
        # Download all button
        if st.session_state.zip_path and st.session_state.zip_path.exists():
            with open(st.session_state.zip_path, "rb") as f:
                st.download_button(
                    label="📥 Download All Images (ZIP)",
                    data=f,
                    file_name=st.session_state.zip_path.name,
                    mime="application/zip",
                    use_container_width=True
                )
        
        # Gallery grid
        st.markdown("<div class='gallery-grid'>", unsafe_allow_html=True)
        
        cols = st.columns(4)
        for idx, (image, prompt, seed) in enumerate(st.session_state.generated_images):
            with cols[idx % 4]:
                st.image(image, width=None)
                
                # Individual download
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG')
                img_bytes = img_buffer.getvalue()
                
                st.download_button(
                    label=f"⬇️ #{idx+1}",
                    data=img_bytes,
                    file_name=f"{gender}_{theme}_image_{idx+1:02d}.png",
                    mime="image/png",
                    key=f"download_{idx}"
                )
                
                with st.expander("📝 Prompt"):
                    st.text(prompt[:200] + "..." if len(prompt) > 200 else prompt)
                    st.caption(f"Seed: {seed}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Reset button
        st.divider()
        if st.button("🔄 Generate New Batch", use_container_width=True):
            st.session_state.generated_images = []
            st.session_state.generation_complete = False
            st.session_state.zip_path = None
            st.rerun()


if __name__ == "__main__":
    main()
