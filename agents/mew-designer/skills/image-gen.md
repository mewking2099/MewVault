---
name: image-gen
triggers: [generate an image, create an image, make an image, image generation, generate a photo, ai image, flux, dalle, stability ai, generate artwork]
description: Generate images via AI APIs (FAL/Flux, Stability AI, DALL-E 3). Use when the user wants an AI-generated image as a design asset — concept art, mockup backgrounds, icons, textures. Handles prompt engineering, API call, and saving to assets/.
inject: on-trigger
claude_code_skills: []
source: mewvault/custom
---

# Image Generation Skill

Generate AI images via FAL/Flux (default), Stability AI, or DALL-E 3. Output saved to `design-studio/<project>/assets/`.

## Setup

Store API keys before first use:
```bash
mew secret set FAL_KEY          # fal.ai — Flux models (recommended)
mew secret set STABILITY_KEY    # Stability AI — SDXL / SD3
mew secret set OPENAI_KEY       # OpenAI — DALL-E 3
```

Check which keys are available:
```bash
mew secret get FAL_KEY && echo "FAL available" || echo "FAL not set"
```

## Step 1 — Build the prompt

Before calling any API, construct a strong prompt. Ask the user for:
1. **Subject** — what's in the image
2. **Style** — photo / illustration / concept art / logo / texture / abstract
3. **Mood/lighting** — cinematic, flat, dramatic, soft, neon
4. **Aspect ratio** — landscape (16:9), portrait (9:16), square (1:1)
5. **Negative prompt** — what to exclude (blurry, text, watermark, cartoon)

### Prompt formula
```
[subject], [style], [lighting], [composition], [quality modifiers]
```

Examples:
- `A minimal SaaS dashboard UI, flat design, soft gradient background, top-down view, clean, professional, 4K`
- `Abstract geometric logo mark for a fintech app, deep navy and gold, clean vectors, white background`
- `Atmospheric concept art of a forest at dusk, painterly, cinematic lighting, detailed, vibrant`

**Negative prompts to always include:** `blurry, low quality, watermark, text, signature, ugly, deformed`

## Step 2 — Choose the backend

| Backend | Best for | Model |
|---------|----------|-------|
| FAL/Flux Dev | General images, high quality | `fal-ai/flux/dev` |
| FAL/Flux Pro | Best quality, slower | `fal-ai/flux-pro` |
| FAL/Flux Schnell | Fast iteration | `fal-ai/flux/schnell` |
| Stability Ultra | Photorealistic | Stable Image Ultra |
| DALL-E 3 | Prompt adherence, text in image | `dall-e-3` |

Use FAL/Flux Dev as default. Fall back to Stability or DALL-E if FAL key not set.

## Step 3 — Generate

### FAL/Flux (recommended)
```python
import fal_client, os, requests
from pathlib import Path

# Load key
os.environ["FAL_KEY"] = subprocess.check_output(["mew", "secret", "get", "FAL_KEY"]).decode().strip()

handler = fal_client.submit(
    "fal-ai/flux/dev",
    arguments={
        "prompt": "YOUR PROMPT HERE",
        "negative_prompt": "blurry, low quality, watermark, text",
        "image_size": "landscape_4_3",   # or square_hd, portrait_4_3, landscape_16_9
        "num_inference_steps": 28,
        "guidance_scale": 3.5,
        "num_images": 1,
        "enable_safety_checker": True,
    },
)
result = fal_client.result("fal-ai/flux/dev", handler.request_id)
image_url = result["images"][0]["url"]

# Save to assets
output_path = Path("design-studio/<project>/assets/<filename>.png")
output_path.write_bytes(requests.get(image_url).content)
print(f"Saved: {output_path}")
```

Install if needed: `pip install fal-client`

### Stability AI
```python
import requests, os
from pathlib import Path

key = subprocess.check_output(["mew", "secret", "get", "STABILITY_KEY"]).decode().strip()
response = requests.post(
    "https://api.stability.ai/v2beta/stable-image/generate/ultra",
    headers={"authorization": f"Bearer {key}", "accept": "image/*"},
    files={"none": ""},
    data={
        "prompt": "YOUR PROMPT HERE",
        "negative_prompt": "blurry, low quality, watermark",
        "aspect_ratio": "16:9",   # 1:1, 16:9, 9:16, 4:3, 3:2
        "output_format": "png",
    },
)
Path("design-studio/<project>/assets/<filename>.png").write_bytes(response.content)
```

### DALL-E 3
```python
from openai import OpenAI
import subprocess, requests
from pathlib import Path

client = OpenAI(api_key=subprocess.check_output(["mew","secret","get","OPENAI_KEY"]).decode().strip())
response = client.images.generate(
    model="dall-e-3",
    prompt="YOUR PROMPT HERE",
    size="1792x1024",    # 1024x1024, 1024x1792, 1792x1024
    quality="hd",
    n=1,
)
url = response.data[0].url
Path("design-studio/<project>/assets/<filename>.png").write_bytes(requests.get(url).content)
```

## Step 4 — Iterate

If the first result misses the mark:
- **Wrong style** → add stronger style keywords, reference an art movement
- **Wrong composition** → add camera/perspective terms (`bird's eye view`, `close-up portrait`, `wide angle`)
- **Too busy** → add `minimalist, clean, simple, negative space` to prompt
- **Wrong colors** → name exact colors: `deep navy #1A3A5C`, `warm amber`

## MewVault context

- Assets → `design-studio/<project>/assets/<descriptive-name>.png`
- For idea-hub pitch decks → `idea-hub/ideas/<slug>/assets/`
- Log the generation in `wiki/<date>-image-gen.md`: prompt used, backend, seed if available
- If `greenlit: true` in Project_Status.md → align with locked design direction before generating
- Pair with `theme-factory` skill to match color palette to generated assets
