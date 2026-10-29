"""Local-only reference inspection. Extract contact sheets, never bundle the clip."""
import sys
from pathlib import Path

import av
from PIL import Image, ImageDraw

source = Path(sys.argv[1])
out = Path(".reference")
out.mkdir(exist_ok=True)
times = [8, 20, 32, 40, 44, 49, 54, 60, 67, 75, 85, 99]
sheet = Image.new("RGB", (1200, 1200), "#202020")
for i, second in enumerate(times):
    with av.open(str(source)) as container:
        container.seek(int(second * av.time_base))
        for frame in container.decode(video=0):
            if frame.time is not None and frame.time >= second:
                im = frame.to_image()
                im.thumbnail((290, 350))
                x, y = (i % 4) * 300, (i // 4) * 400
                sheet.paste(im, (x + (300 - im.width) // 2, y + 25))
                ImageDraw.Draw(sheet).text((x + 10, y + 5), f"{second}s", fill="white")
                if second in [40, 49, 60, 75, 99]:
                    frame.to_image().save(out / f"frame-{second}.jpg")
                break
sheet.save(out / "contact.jpg")
print(out / "contact.jpg")
