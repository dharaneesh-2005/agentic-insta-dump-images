# Implementation Plan - AI Instagram Dump Generator

## Phase 1: Project Setup

### Step 1: Create Directory Structure
```bash
mkdir -p src prompts/male prompts/female workflows generated temp
```

### Step 2: Dependencies (requirements.txt)
- streamlit - Web UI framework
- requests - HTTP client for ComfyUI API
- pillow - Image processing
- python-dotenv - Environment configuration
- websocket-client - For ComfyUI real-time updates (optional)

## Phase 2: Core Modules

### Step 3: Configuration Module (config.py)
- ComfyUI connection settings
- Path configurations
- Generation parameters (batch size, timeouts)
- Theme and gender mappings

### Step 4: ComfyUI API Client (src/comfyui_client.py)
Key methods needed:
- `upload_image(image_path, name)` - Upload user photos
- `queue_workflow(workflow_json)` - Submit generation job
- `get_history(prompt_id)` - Check job status
- `download_image(filename)` - Retrieve output
- `get_image_data(node_id, prompt_id)` - Get generated image

ComfyUI API endpoints:
- POST `/upload/image` - Upload images
- POST `/prompt` - Queue workflow
- GET `/history/{prompt_id}` - Get execution history
- GET `/view?filename={name}` - Download images

### Step 5: Prompt Engine (src/prompt_engine.py)
Features:
- Load prompts from text files organized by gender/theme
- Random prompt selection from theme pool
- Support for prompt variables (optional)
- Fallback prompts if files missing

File structure:
```
prompts/
  male/
    cinematic.txt      (15 prompts)
    vintage.txt        (15 prompts)
    beach.txt          (15 prompts)
    streetwear.txt     (15 prompts)
    minimalist.txt     (15 prompts)
    dark_aesthetic.txt (15 prompts)
    nature.txt         (15 prompts)
    urban.txt          (15 prompts)
    luxury.txt         (15 prompts)
    casual.txt         (15 prompts)
  female/
    [same themes]
```

### Step 6: Batch Generator (src/batch_generator.py)
Logic:
- Accept: 2 image paths, gender, theme, count (10-20)
- For each image to generate:
  1. Select random prompt from theme pool
  2. Generate random seed
  3. Upload both user images to ComfyUI
  4. Submit workflow with prompt + seed
  5. Poll for completion
  6. Download result
  7. Store locally
- Return list of generated image paths
- Progress callback for UI updates

### Step 7: Image Utilities (src/image_utils.py)
- Image validation (format, size)
- Thumbnail generation for preview
- ZIP archive creation for download
- Cleanup temp files

## Phase 3: Frontend

### Step 8: Streamlit App (app.py)
Layout:
```
[Header: AI Instagram Dump Generator]

[Section 1: Upload]
- File uploader 1: "Upload Face Photo"
- File uploader 2: "Upload Full Body Photo"

[Section 2: Settings]
- Radio: Gender [Male | Female]
- Selectbox: Theme [dropdown of themes]
- Slider: Number of Images [10-20]

[Section 3: Generate]
- Button: "Generate Instagram Dump"
- Progress bar + status text

[Section 4: Results]
- Grid gallery of generated images
- Download buttons (individual + ZIP)
```

Features:
- Session state management
- Progress tracking
- Error display
- Image preview before generation

## Phase 4: Workflow Integration

### Step 9: Workflow File Setup
User needs to:
1. Open ComfyUI web interface
2. Build/create their workflow with:
   - 2 Load Image nodes
   - Prompt node
   - IPAdapter/InstantID for face transfer
   - KSampler
   - Save Image node
3. Click "Save (API Format)" to get workflow_api.json
4. Place file in workflows/workflow_api.json

Our code will:
- Load workflow_api.json
- Find and modify nodes for:
  - Image inputs (inject uploaded image paths)
  - Prompt text (inject selected prompt)
  - Seed (inject random seed)
- Submit modified workflow

## Phase 5: Prompt Content

### Step 10: Create Prompt Libraries
Each theme needs 15+ unique prompts.

Example themes and prompt styles:

**Cinematic:**
- Film grain, dramatic lighting, movie poster aesthetic
- 35mm lens, shallow depth of field, golden hour
- Anamorphic lens flare, color grading, moody atmosphere

**Vintage:**
- Retro film look, 90s aesthetic, faded colors
- Polaroid style, light leaks, grainy texture
- Old Hollywood glamour, sepia tones, classic portrait

**Beach:**
- Golden hour beach, ocean backdrop, natural lighting
- Sandy shores, tropical vibes, sunset colors
- Coastal aesthetic, relaxed pose, summer tones

**Streetwear:**
- Urban backdrop, graffiti walls, city streets
- Fashion editorial, bold colors, contemporary style
- Night city lights, neon reflections, modern aesthetic

## Phase 6: Testing & Polish

### Step 11: Error Handling
- ComfyUI connection errors
- Image upload failures
- Workflow execution errors
- Timeout handling
- User-friendly error messages

### Step 12: Progress Tracking
- Real-time progress updates
- Current image X of Y
- Estimated time remaining
- Cancel button (optional)

### Step 13: Final Integration Test
- End-to-end workflow test
- Verify all components work together
- Performance optimization

## Configuration Variables

```python
# config.py example values
COMFYUI_BASE_URL = "http://127.0.0.1:8000"
WORKFLOW_PATH = "workflows/workflow_api.json"
OUTPUT_FOLDER = "generated"
TEMP_FOLDER = "temp"
DEFAULT_BATCH_SIZE = 15
MIN_BATCH_SIZE = 10
MAX_BATCH_SIZE = 20
SUPPORTED_THEMES = [
    "cinematic", "vintage", "beach", "streetwear",
    "minimalist", "dark_aesthetic", "nature", 
    "urban", "luxury", "casual"
]
```

## Notes for Implementation

1. **ComfyUI Workflow Requirements:**
   - Must have exactly 2 image input nodes
   - Must have a text prompt node
   - Must save output to predictable location
   - API format must be exported from ComfyUI

2. **Image Upload Process:**
   - ComfyUI requires images to be uploaded before workflow execution
   - Uploaded images get assigned filenames
   - Workflow references these filenames

3. **Generation Strategy:**
   - Sequential generation is safer (avoid overwhelming ComfyUI)
   - Can add parallel generation later if needed
   - Each image gets unique prompt + seed combination

4. **UI Considerations:**
   - Keep UI responsive during generation (use callbacks)
   - Show preview of uploaded images
   - Gallery should be responsive grid
   - Download all as ZIP is essential
