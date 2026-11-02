"""Render deterministic musical-climax proof frames in the app's OpenGL pipeline."""
import os
from pathlib import Path
import sys
import time
import numpy as np

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from recur.model import Instrument
from recur.renderer import SculptureRenderer


def main():
    pygame.display.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    size = (1280, 820)
    pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.HIDDEN)
    renderer = SculptureRenderer(size)
    renderer.instrument_visible = True
    model = Instrument()
    output = Path(__file__).resolve().parents[1] / 'captures' / 'crescendo'
    output.mkdir(parents=True, exist_ok=True)
    overlay = bytes(size[0] * size[1] * 4)
    started = time.perf_counter(); frames = 0

    def frame():
        nonlocal frames
        pygame.event.pump()
        model.advance(1/60)
        renderer.draw(model, overlay)
        pygame.display.flip()
        frames += 1

    def save(name):
        pygame.image.save(renderer.capture(), str(output / name))

    def coverage():
        rgb=np.frombuffer(renderer.ctx.screen.read(components=3,alignment=1),dtype=np.uint8).reshape(size[1],size[0],3)
        lit=rgb.max(axis=2)>32
        edges=np.r_[lit[:20].ravel(),lit[-20:].ravel(),lit[:,:20].ravel(),lit[:,-20:].ravel()]
        return float(edges.mean()),float((rgb.min(axis=2)>248).mean())

    for _ in range(90): frame()
    save('01-quiet.png')
    quiet_edges,_=coverage()
    renderer.climax.drop(1.)
    for _ in range(100):frame()
    assert renderer.climax.amount > .8
    save('02-high-phrase.png')
    peak_edges,white=coverage()
    assert peak_edges>max(.06,quiet_edges+.05),f'Climax did not reach the edges: {quiet_edges:.3f}/{peak_edges:.3f}'
    assert white<.03,f'Too much clipped white: {white:.3f}'
    for shape in (0,1,2,6):
        renderer.stage.set_base(shape)
        renderer.climax.sustain = 3.
        renderer.climax.excitation = 1.
        for _ in range(90): frame()
        save(f'03-form-{shape}.png')
    renderer.climax.reset()
    for _ in range(600): frame()
    assert renderer.climax.amount < .001
    save('04-return.png')
    print(f'CLIMAX OK: {frames} frames, {frames/(time.perf_counter()-started):.1f} FPS, '
          f'{renderer.ctx.info["GL_RENDERER"]}; quiet/peak edge coverage {quiet_edges:.1%}/{peak_edges:.1%}; '
          f'clipped white {white:.2%}; proof: {output}')
    pygame.quit()


if __name__ == '__main__':
    main()
