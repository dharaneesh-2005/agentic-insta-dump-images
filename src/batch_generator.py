"""Batch generation logic for creating multiple images."""
import random
import time
from pathlib import Path
from typing import List, Callable, Optional, Tuple
from PIL import Image
import io

from src.comfyui_client import (
    ComfyUIClient, 
    load_workflow_template,
    inject_images_into_workflow,
    inject_prompt_into_workflow,
    inject_seed_into_workflow
)
from src.prompt_engine import PromptEngine
import config


class BatchGenerator:
    """Handles batch generation of images using ComfyUI."""
    
    def __init__(self, 
                 comfyui_client: ComfyUIClient = None,
                 prompt_engine: PromptEngine = None):
        self.client = comfyui_client or ComfyUIClient()
        self.prompt_engine = prompt_engine or PromptEngine()
        self.workflow_template = None
        
    def _load_workflow(self) -> dict:
        """Load the workflow template."""
        if self.workflow_template is None:
            self.workflow_template = load_workflow_template()
        return self.workflow_template.copy()
    
    def generate_single(
        self,
        image_paths: List[Path],
        prompt: str,
        seed: Optional[int] = None
    ) -> Image.Image:
        """Generate a single image.
        
        Args:
            image_paths: List of paths to uploaded images
            prompt: The prompt text
            seed: Random seed (generated if None)
            
        Returns:
            Generated PIL Image
        """
        if seed is None:
            seed = random.randint(1, 2**32 - 1)
        
        # Load and prepare workflow
        workflow = self._load_workflow()
        
        # Upload images to ComfyUI
        uploaded_names = []
        for img_path in image_paths:
            uploaded_name = self.client.upload_image(img_path)
            uploaded_names.append(uploaded_name)
        
        # Inject parameters into workflow
        workflow = inject_images_into_workflow(workflow, uploaded_names)
        workflow = inject_prompt_into_workflow(workflow, prompt)
        workflow = inject_seed_into_workflow(workflow, seed)
        
        # Execute workflow
        images_data = self.client.execute_workflow(workflow)
        
        if not images_data:
            raise ValueError("No images generated")
        
        # Convert first image to PIL Image
        image = Image.open(io.BytesIO(images_data[0]))
        return image
    
    def generate_batch(
        self,
        image_paths: List[Path],
        gender: str,
        theme: str,
        count: int = 15,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        save_dir: Path = None
    ) -> List[Tuple[Image.Image, str, int]]:
        """Generate a batch of images.
        
        Args:
            image_paths: List of paths to 2 uploaded images
            gender: "male" or "female"
            theme: Theme name
            count: Number of images to generate (10-20)
            progress_callback: Function(current, total, status) to call for progress updates
            save_dir: Directory to save generated images
            
        Returns:
            List of tuples (image, prompt_used, seed)
        """
        if save_dir is None:
            save_dir = config.OUTPUT_DIR
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Get prompts for this batch
        prompts = self.prompt_engine.get_prompts(gender, theme, count)
        
        results = []
        
        for i, prompt in enumerate(prompts):
            current_num = i + 1
            
            if progress_callback:
                progress_callback(current_num, count, f"Generating image {current_num}/{count}...")
            
            try:
                # Generate unique seed for each image
                seed = random.randint(1, 2**32 - 1)
                
                # Generate image
                image = self.generate_single(image_paths, prompt, seed)
                
                # Save image
                timestamp = int(time.time())
                filename = f"{gender}_{theme}_{timestamp}_{seed}.png"
                filepath = save_dir / filename
                image.save(filepath, "PNG")
                
                results.append((image, prompt, seed))
                
                if progress_callback:
                    progress_callback(current_num, count, f"Completed {current_num}/{count}")
                    
            except Exception as e:
                error_msg = f"Error generating image {current_num}: {str(e)}"
                if progress_callback:
                    progress_callback(current_num, count, error_msg)
                # Continue with next image instead of failing entire batch
                continue
        
        return results
    
    def validate_images(self, image_paths: List[Path]) -> Tuple[bool, str]:
        """Validate uploaded images.
        
        Args:
            image_paths: List of image paths to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(image_paths) != 2:
            return False, "Please upload exactly 2 images"
        
        for path in image_paths:
            if not path.exists():
                return False, f"Image not found: {path}"
            
            # Check file size
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > config.MAX_IMAGE_SIZE_MB:
                return False, f"Image {path.name} is too large ({size_mb:.1f}MB > {config.MAX_IMAGE_SIZE_MB}MB)"
            
            # Check format
            ext = path.suffix.lower().replace(".", "")
            if ext not in config.SUPPORTED_IMAGE_FORMATS:
                return False, f"Unsupported format: {path.suffix}. Use: {', '.join(config.SUPPORTED_IMAGE_FORMATS)}"
            
            # Try to open as image
            try:
                with Image.open(path) as img:
                    img.verify()
            except Exception as e:
                return False, f"Invalid image file {path.name}: {str(e)}"
        
        return True, ""


def create_zip_archive(
    images: List[Tuple[Image.Image, str, int]], 
    output_path: Path,
    gender: str,
    theme: str
) -> Path:
    """Create a ZIP archive of generated images.
    
    Args:
        images: List of (image, prompt, seed) tuples
        output_path: Path for the ZIP file
        gender: Gender used for generation
        theme: Theme used for generation
        
    Returns:
        Path to created ZIP file
    """
    import zipfile
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, (image, prompt, seed) in enumerate(images):
            # Save image to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            # Add to ZIP
            filename = f"{gender}_{theme}_image_{i+1:02d}.png"
            zf.writestr(filename, img_bytes)
        
        # Add metadata file
        metadata = f"Generation Details:\n"
        metadata += f"Gender: {gender}\n"
        metadata += f"Theme: {theme}\n"
        metadata += f"Total Images: {len(images)}\n\n"
        metadata += "Prompts used:\n"
        for i, (_, prompt, seed) in enumerate(images):
            metadata += f"\nImage {i+1}:\n"
            metadata += f"  Prompt: {prompt}\n"
            metadata += f"  Seed: {seed}\n"
        
        zf.writestr("metadata.txt", metadata)
    
    return output_path