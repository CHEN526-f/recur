"""Read a supplied clip locally and save time-labelled inspection sheets."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/packages'))
import av
from PIL import Image, ImageDraw

source=Path(sys.argv[1])
out=ROOT/'.reference/structure-study'
out.mkdir(parents=True,exist_ok=True)
with av.open(str(source)) as container:
    duration=container.duration/av.time_base
times=[min(duration-.2,second) for second in range(0,113,8)]
if len(sys.argv)>2:
    times=[float(t) for t in sys.argv[2].split(',')]
columns=3;rows=(len(times)+columns-1)//columns
sheet=Image.new('RGB',(1440,rows*292),'#121517')
draw=ImageDraw.Draw(sheet)
for i,second in enumerate(times):
    with av.open(str(source)) as container:
        container.seek(int(second*av.time_base))
        for frame in container.decode(video=0):
            if frame.time is not None and frame.time>=second:
                im=frame.to_image()
                if im.height>im.width:im=im.rotate(90,expand=True)
                im.thumbnail((474,264))
                x=(i%columns)*480;y=(i//columns)*292
                sheet.paste(im,(x+(480-im.width)//2,y+24))
                draw.text((x+8,y+6),f'{second:05.1f}s',fill='#ece5c6')
                frame.to_image().save(out/f'frame-{second:g}.jpg')
                break
name='sequence.jpg' if len(sys.argv)>2 else 'contact.jpg'
sheet.save(out/name)
print(f'{duration:.2f}s; {out/name}')
