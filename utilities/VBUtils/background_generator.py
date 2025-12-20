from diffusers import StableDiffusionInpaintPipeline
import torch
from PIL import Image, ImageOps

# Load inpainting model (requires local weights)
pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-inpainting",
    torch_dtype=torch.float16
).to("cuda")

def expand_sprite(path, output_path, prompt="background continuation, pixel art style"):
    # Load original
    img = Image.open(path).convert("RGB")

    # Create 160x160 canvas and paste centered
    new_img = Image.new("RGB", (160, 160), (0, 0, 0))
    x_offset = (160 - img.width) // 2  # 40px left/right
    y_offset = (160 - img.height) // 2  # should be 0
    new_img.paste(img, (x_offset, y_offset))

    # Create mask (white = area to fill, black = keep)
    mask = Image.new("L", (160, 160), 0)
    draw = ImageOps.invert(new_img.convert("L"))  # rough mask
    mask.paste(255, (0, 0, 40, 160))   # left border
    mask.paste(255, (120, 0, 160, 160)) # right border

    # Inpaint missing parts
    result = pipe(prompt=prompt, image=new_img, mask_image=mask).images[0]
    result.save(output_path)

# Example
expand_sprite("backgrounds/bg_DC Villains.png", "expanded.png")