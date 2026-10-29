"""Render deterministic musical-climax proof frames in the app's OpenGL pipeline."""
import os
from pathlib import Path
import sys
import time

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
    pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF)
    renderer = SculptureRenderer(size)
    renderer.instrument_visible = False
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

    for _ in range(90): frame()
    save('01-quiet.png')
    for i in range(100):
        if i % 12 == 0: renderer.climax.note(1); model.trigger(1)
        frame()
    assert renderer.climax.amount > .8
    save('02-high-phrase.png')
    for shape in (0,1,2,4):
        model.select_shape(shape)
        renderer.climax.sustain = 3.
        renderer.climax.excitation = 1.
        for _ in range(90): frame()
        save(f'03-form-{shape}.png')
    renderer.climax.reset()
    for _ in range(600): frame()
    assert renderer.climax.amount < .001
    save('04-return.png')
    print(f'CLIMAX OK: {frames} frames, {frames/(time.perf_counter()-started):.1f} FPS, '
          f'{renderer.ctx.info["GL_RENDERER"]}; proof: {output}')
    pygame.quit()


if __name__ == '__main__':
    main()
