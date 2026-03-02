"""ComfyUI API Client for workflow execution and image generation."""
import json
import time
import uuid
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import config


class ComfyUIClient:
    """Client for interacting with ComfyUI API."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.COMFYUI_BASE_URL
        self.client_id = str(uuid.uuid4())
        
    def upload_image(self, image_path: Path, name: str = None) -> str:
        """Upload an image to ComfyUI server.
        
        Args:
            image_path: Path to the image file
            name: Optional name for the uploaded image
            
        Returns:
            Filename of the uploaded image on the server
        """
        url = f"{self.base_url}/upload/image"
        
        if name is None:
            name = image_path.name
            
        with open(image_path, "rb") as f:
            files = {"image": (name, f, "image/png")}
            data = {"type": "input", "overwrite": "true"}
            response = requests.post(url, files=files, data=data, timeout=30)
            
        response.raise_for_status()
        result = response.json()
        
        if "name" not in result:
            raise ValueError(f"Upload failed: {result}")
            
        return result["name"]
    
    def queue_workflow(self, workflow: Dict[str, Any]) -> str:
        """Queue a workflow for execution.
        
        Args:
            workflow: The workflow JSON with injected parameters
            
        Returns:
            Prompt ID for tracking the job
        """
        url = f"{self.base_url}/prompt"
        
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        
        response = requests.post(
            url, 
            json=payload, 
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if "prompt_id" not in result:
            raise ValueError(f"Failed to queue workflow: {result}")
            
        return result["prompt_id"]
    
    def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get execution history for a prompt.
        
        Args:
            prompt_id: The prompt ID to check
            
        Returns:
            History data if available, None otherwise
        """
        url = f"{self.base_url}/history/{prompt_id}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        history = response.json()
        
        if prompt_id in history:
            return history[prompt_id]
        return None
    
    def is_workflow_complete(self, prompt_id: str) -> Tuple[bool, Optional[List[str]]]:
        """Check if a workflow has completed.
        
        Args:
            prompt_id: The prompt ID to check
            
        Returns:
            Tuple of (is_complete, output_files)
        """
        history = self.get_history(prompt_id)
        
        if history is None:
            return False, None
            
        # Check for outputs
        outputs = history.get("outputs", {})
        
        if not outputs:
            return False, None
            
        # Extract output image filenames
        output_files = []
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for img in node_output["images"]:
                    output_files.append(img["filename"])
                    
        return True, output_files
    
    def download_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Download a generated image.
        
        Args:
            filename: Name of the file to download
            subfolder: Subfolder path
            folder_type: Type of folder (output, input, temp)
            
        Returns:
            Image data as bytes
        """
        url = f"{self.base_url}/view"
        params = {
            "filename": filename,
            "type": folder_type
        }
        if subfolder:
            params["subfolder"] = subfolder
            
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        return response.content
    
    def wait_for_completion(
        self, 
        prompt_id: str, 
        timeout: int = config.REQUEST_TIMEOUT,
        poll_interval: int = config.POLL_INTERVAL
    ) -> List[str]:
        """Wait for workflow completion and return output files.
        
        Args:
            prompt_id: The prompt ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Seconds between status checks
            
        Returns:
            List of output filenames
            
        Raises:
            TimeoutError: If workflow doesn't complete in time
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            is_complete, output_files = self.is_workflow_complete(prompt_id)
            
            if is_complete:
                if output_files:
                    return output_files
                else:
                    raise ValueError("Workflow completed but no outputs found")
                    
            time.sleep(poll_interval)
            
        raise TimeoutError(f"Workflow did not complete within {timeout} seconds")
    
    def execute_workflow(
        self, 
        workflow: Dict[str, Any],
        timeout: int = config.REQUEST_TIMEOUT
    ) -> List[bytes]:
        """Execute a workflow and return generated images.
        
        Args:
            workflow: The workflow JSON
            timeout: Maximum time to wait
            
        Returns:
            List of image data as bytes
        """
        # Queue the workflow
        prompt_id = self.queue_workflow(workflow)
        
        # Wait for completion
        output_files = self.wait_for_completion(prompt_id, timeout)
        
        # Download all outputs
        images = []
        for filename in output_files:
            image_data = self.download_image(filename)
            images.append(image_data)
            
        return images


def load_workflow_template(path: Path = None) -> Dict[str, Any]:
    """Load the workflow template from JSON file.
    
    Args:
        path: Path to workflow JSON file
        
    Returns:
        Workflow as dictionary
    """
    if path is None:
        path = config.WORKFLOW_PATH
        
    if not path.exists():
        raise FileNotFoundError(
            f"Workflow file not found: {path}\n"
            "Please export your ComfyUI workflow in API format and save it to this location."
        )
        
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_nodes_by_type(workflow: Dict[str, Any], node_type: str) -> List[str]:
    """Find all node IDs of a specific type in the workflow.
    
    Args:
        workflow: The workflow dictionary
        node_type: The class_type to search for
        
    Returns:
        List of node IDs
    """
    matching_nodes = []
    for node_id, node_data in workflow.items():
        if isinstance(node_data, dict) and node_data.get("class_type") == node_type:
            matching_nodes.append(node_id)
    return matching_nodes


def inject_images_into_workflow(
    workflow: Dict[str, Any],
    image_filenames: List[str],
    load_image_node_type: str = "LoadImage"
) -> Dict[str, Any]:
    """Inject uploaded image filenames into LoadImage nodes.
    
    Args:
        workflow: The workflow dictionary
        image_filenames: List of uploaded image filenames
        load_image_node_type: The node type for loading images
        
    Returns:
        Modified workflow
    """
    workflow = workflow.copy()
    
    # Find all LoadImage nodes and sort by node ID for consistent ordering
    load_image_nodes = find_nodes_by_type(workflow, load_image_node_type)
    
    if len(load_image_nodes) < len(image_filenames):
        raise ValueError(
            f"Workflow has {len(load_image_nodes)} LoadImage nodes "
            f"but {len(image_filenames)} images were provided"
        )
    
    # Sort nodes to ensure consistent ordering (e.g., 76 before 81)
    load_image_nodes.sort()
    
    # Inject images into nodes
    for i, filename in enumerate(image_filenames):
        if i < len(load_image_nodes):
            node_id = load_image_nodes[i]
            workflow[node_id]["inputs"]["image"] = filename
            
    return workflow


def inject_prompt_into_workflow(
    workflow: Dict[str, Any],
    prompt: str,
    prompt_node_types: List[str] = None
) -> Dict[str, Any]:
    """Inject prompt text into CLIPTextEncode or similar nodes.
    
    Args:
        workflow: The workflow dictionary
        prompt: The prompt text
        prompt_node_types: List of node types that accept text
        
    Returns:
        Modified workflow
    """
    if prompt_node_types is None:
        prompt_node_types = ["CLIPTextEncode", "CLIPTextEncodeFlux2", "PromptText", "TextInput"]
        
    workflow = workflow.copy()
    
    # Find prompt nodes - look for CLIPTextEncode with "Positive" in title
    prompt_node_id = None
    
    for node_id, node_data in workflow.items():
        if isinstance(node_data, dict):
            class_type = node_data.get("class_type", "")
            meta = node_data.get("_meta", {})
            title = meta.get("title", "").lower()
            
            if class_type in prompt_node_types:
                inputs = node_data.get("inputs", {})
                if "text" in inputs:
                    # Prefer "Positive Prompt" node if available
                    if "positive" in title:
                        prompt_node_id = node_id
                        break
                    # Otherwise use the first one found
                    elif prompt_node_id is None:
                        prompt_node_id = node_id
    
    # Inject the prompt
    if prompt_node_id:
        workflow[prompt_node_id]["inputs"]["text"] = prompt
    else:
        # Fallback: try to find any node with "text" input
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict):
                inputs = node_data.get("inputs", {})
                if "text" in inputs and isinstance(inputs["text"], str):
                    workflow[node_id]["inputs"]["text"] = prompt
                    break
                    
    return workflow


def inject_seed_into_workflow(
    workflow: Dict[str, Any],
    seed: int,
    seed_node_types: List[str] = None
) -> Dict[str, Any]:
    """Inject seed into KSampler, RandomNoise, or similar nodes.
    
    Args:
        workflow: The workflow dictionary
        seed: The random seed
        seed_node_types: List of node types that accept seed
        
    Returns:
        Modified workflow
    """
    if seed_node_types is None:
        seed_node_types = ["KSampler", "RandomNoise", "RandomSeed", "SeedInput"]
        
    workflow = workflow.copy()
    
    for node_id, node_data in workflow.items():
        if isinstance(node_data, dict):
            class_type = node_data.get("class_type", "")
            if class_type in seed_node_types:
                inputs = node_data.get("inputs", {})
                # Different nodes use different field names for seed
                if "seed" in inputs:
                    workflow[node_id]["inputs"]["seed"] = seed
                elif "noise_seed" in inputs:
                    workflow[node_id]["inputs"]["noise_seed"] = seed
                    
    return workflow
