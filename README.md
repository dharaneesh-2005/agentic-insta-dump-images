# AI Instagram Dump Generator

Generate 10-20 aesthetic Instagram dump images from 2 uploaded photos using ComfyUI and AI.

## Features

- 📤 Upload 2 photos (face + body)
- 🎨 Choose from 12+ aesthetic themes (Cinematic, Vintage, Beach, Streetwear, etc.)
- 👤 Gender-specific prompt segmentation
- 🖼️ Generate 10-20 unique images in one batch
- 📥 Download individual images or full ZIP archive
- ⚡ Real-time progress tracking

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure ComfyUI

Make sure ComfyUI is running with the API enabled:

```bash
# In your ComfyUI directory
python main.py --listen --port 8000
```

### 3. Export Your Workflow

1. Open ComfyUI web interface
2. Build your workflow with:
   - 2 `LoadImage` nodes (for user uploads)
   - 1 `CLIPTextEncode` or prompt node
   - IPAdapter/InstantID for face transfer
   - KSampler for generation
   - SaveImage node
3. Click **"Save (API Format)"** in the menu
4. Save the JSON to `workflows/workflow_api.json`

### 4. Run the App

```bash
streamlit run app.py
```

## Project Structure

```
.
├── app.py                 # Streamlit frontend
├── config.py              # Configuration settings
├── requirements.txt         # Python dependencies
├── src/
│   ├── comfyui_client.py  # ComfyUI API connector
│   ├── prompt_engine.py   # Prompt template manager
│   └── batch_generator.py # Batch generation logic
├── prompts/
│   ├── male/              # Male-specific prompts by theme
│   └── female/            # Female-specific prompts by theme
├── workflows/
│   └── workflow_api.json  # Your ComfyUI workflow (export this)
└── generated/             # Output folder for images
```

## Available Themes

- 🎬 Cinematic
- 📷 Vintage
- 🏖️ Beach
- 👟 Streetwear
- ⚪ Minimalist
- 🌑 Dark Aesthetic
- 🌿 Nature
- 🏙️ Urban
- 💎 Luxury
- 😎 Casual
- 👔 Formal
- 🎨 Artistic

## Configuration

Edit `config.py` to customize:

```python
COMFYUI_HOST = "127.0.0.1"
COMFYUI_PORT = 8000
DEFAULT_BATCH_SIZE = 15
MIN_BATCH_SIZE = 10
MAX_BATCH_SIZE = 20
```

## Usage

1. Open the app in your browser (usually `http://localhost:8501`)
2. Upload 2 photos (face photo + body photo)
3. Select gender and theme
4. Choose number of images (10-20)
5. Click "Generate Instagram Dump"
6. Wait for generation to complete
7. Download individual images or the full ZIP

## Troubleshooting

### Cannot connect to ComfyUI
- Make sure ComfyUI is running with `--listen` flag
- Check the host/port in `config.py`
- Verify firewall settings

### Workflow not found
- Export your workflow from ComfyUI in API format
- Save it to `workflows/workflow_api.json`

### Generation fails
- Check ComfyUI console for errors
- Verify your workflow has the correct node types
- Ensure IPAdapter/InstantID is properly configured

## License

MIT License
