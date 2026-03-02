"""Batch generation logic for creating multiple images."""
import random
import time
import copy
from pathlib import Path
from typing import List, Callable, Optional, Tuple, Dict
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
        self._workflow_template = None
        
    def _load_workflow(self) -> dict:
        """Load the workflow template - creates a fresh deep copy each time."""
        if self._workflow_template is None:
            self._workflow_template = load_workflow_template()
        # Return a deep copy to ensure each workflow is independent
        return copy.deepcopy(self._workflow_template)
    
    def generate_batch_queued(
        self,
        image_paths: List[Path],
        gender: str,
        count: int = 15,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        save_dir: Path = None
    ) -> List[Tuple[Image.Image, str, int]]:
        """Generate a batch of images by queuing all at once to ComfyUI.
        
        This is much faster because ComfyUI keeps the model loaded
        and processes all queued workflows sequentially without reloading.
        
        Args:
            image_paths: List of paths to 2 uploaded images
            gender: "male" or "female"
            count: Number of images to generate (1-20)
            progress_callback: Function(current, total, status) to call for progress updates
            save_dir: Directory to save generated images
            
        Returns:
            List of tuples (image, prompt_used, seed)
        """
        if save_dir is None:
            save_dir = config.OUTPUT_DIR
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Get prompts for this batch (no theme, just gender-based prompts)
        prompts = self.prompt_engine.get_prompts(gender, "prompts", count)
        
        # Upload images once (reused for all generations)
        if progress_callback:
            progress_callback(0, count, "Uploading images to ComfyUI...")
        
        uploaded_names = []
        for img_path in image_paths:
            uploaded_name = self.client.upload_image(img_path)
            uploaded_names.append(uploaded_name)
        
        # Prepare all workflows with different prompts and seeds
        if progress_callback:
            progress_callback(0, count, f"Preparing {count} workflows...")
        
        workflows = []
        seeds = []
        for i, prompt in enumerate(prompts):
            workflow = self._load_workflow()
            workflow = inject_images_into_workflow(workflow, uploaded_names)
            workflow = inject_prompt_into_workflow(workflow, prompt)
            seed = random.randint(1, 2**32 - 1)
            seeds.append(seed)
            workflow = inject_seed_into_workflow(workflow, seed)
            workflows.append(workflow)
        
        # Queue all workflows at once
        if progress_callback:
            progress_callback(0, count, f"Queuing {count} images to ComfyUI...")
        
        prompt_ids = []
        for i, workflow in enumerate(workflows):
            prompt_id = self.client.queue_workflow(workflow)
            prompt_ids.append(prompt_id)
            if progress_callback:
                progress_callback(i + 1, count, f"Queued {i + 1}/{count} workflows...")
        
        # Wait for all completions and download results
        results = []
        completed_count = 0
        
        for i, (prompt_id, prompt, seed) in enumerate(zip(prompt_ids, prompts, seeds)):
            if progress_callback:
                progress_callback(completed_count, count, f"Waiting for image {i + 1}/{count}...")
            
            try:
                # Wait for this specific workflow
                output_files = self.client.wait_for_completion(prompt_id)
                
                # Download the generated image
                if output_files:
                    image_data = self.client.download_image(output_files[0])
                    image = Image.open(io.BytesIO(image_data))
                    
                    # Save image
                    timestamp = int(time.time())
                    filename = f"{gender}_{timestamp}_{i}_{seed}.png"
                    filepath = save_dir / filename
                    image.save(filepath, "PNG")
                    
                    results.append((image, prompt, seed))
                    completed_count += 1
                    
                    if progress_callback:
                        progress_callback(completed_count, count, f"Completed {completed_count}/{count}")
                
            except Exception as e:
                error_msg = f"Error on image {i + 1}: {str(e)}"
                if progress_callback:
                    progress_callback(completed_count, count, error_msg)
                continue
        
        return results
    
    def generate_batch(
        self,
        image_paths: List[Path],
        gender: str,
        count: int = 15,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        save_dir: Path = None
    ) -> List[Tuple[Image.Image, str, int]]:
        """Generate a batch of images (uses queued batch method for efficiency).
        
        Args:
            image_paths: List of paths to 2 uploaded images
            gender: "male" or "female"
            count: Number of images to generate (1-20)
            progress_callback: Function(current, total, status) to call for progress updates
            save_dir: Directory to save generated images
            
        Returns:
            List of tuples (image, prompt_used, seed)
        """
        # Use the new queued batch method for better performance
        return self.generate_batch_queued(
            image_paths=image_paths,
            gender=gender,
            count=count,
            progress_callback=progress_callback,
            save_dir=save_dir
        )
    
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
    prompt_set: str
) -> Path:
    """Create a ZIP archive of generated images.
    
    Args:
        images: List of (image, prompt, seed) tuples
        output_path: Path for the ZIP file
        gender: Gender used for generation
        prompt_set: Prompt set used for generation
        
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
            filename = f"{gender}_image_{i+1:02d}.png"
            zf.writestr(filename, img_bytes)
        
        # Add metadata file
        metadata = f"Generation Details:\n"
        metadata += f"Gender: {gender}\n"
        metadata += f"Prompt Set: {prompt_set}\n"
        metadata += f"Total Images: {len(images)}\n\n"
        metadata += "Prompts used:\n"
        for i, (_, prompt, seed) in enumerate(images):
            metadata += f"\nImage {i+1}:\n"
            metadata += f"  Prompt: {prompt}\n"
            metadata += f"  Seed: {seed}\n"
        
        zf.writestr("metadata.txt", metadata)
    
    return output_path