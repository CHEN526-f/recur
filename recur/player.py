"""Pygame event routing for the two-deck instrument."""
import argparse
import math
from pathlib import Path
import time
import pygame
from .model import Instrument, FORM_COUNT, VOICE_FOR_FORM
from .audio import Synth
from .renderer import SculptureRenderer
from .ui import Interface
from .camera import MotionCamera
from .music import MusicTrack,DEMO_PATH
from .filepicker import pick_audio_file
from .composition import Performance


def run(save,restore):
    parser=argparse.ArgumentParser()
    parser.add_argument('--smoke-test',action='store_true')
    parser.add_argument('--interaction-test',action='store_true')
    parser.add_argument('--music-test',action='store_true')
    parser.add_argument('--rhythm-test',action='store_true',help='Run 12 seconds of real playback and verify audio/motion timing.')
    parser.add_argument('--mute',action='store_true')
    parser.add_argument('--music',help='Play and analyse a local WAV, MP3, OGG or FLAC track.')
    args=parser.parse_args()
    pygame.display.init();pygame.font.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION,3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION,3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,pygame.GL_CONTEXT_PROFILE_CORE)
    flags=pygame.OPENGL|pygame.DOUBLEBUF|pygame.RESIZABLE;size=(1280,820)
    if args.smoke_test or args.interaction_test or args.music_test or args.rhythm_test:flags|=pygame.HIDDEN
    try:
        pygame.display.set_mode(size,flags,vsync=1);renderer=SculptureRenderer(size)
    except Exception as exc:
        pygame.quit();print('OpenGL 3.3 could not start: '+str(exc));return 1
    pygame.display.set_caption('RECUR / 环生 — stage VJ')
    model=Instrument();synth=Synth();ui=Interface();camera=MotionCamera()
    synth.muted=args.mute or args.smoke_test or args.interaction_test or args.music_test or args.rhythm_test
    music=MusicTrack();music.muted=synth.muted;renderer.music=music
    performance=Performance();renderer.performance=performance
    clock=pygame.time.Clock();running=True;drag=None;jog_angle=0.;jog_last=0.;scratch_last=0.
    demo=False;backup=None;backup_music=False;backup_forms=None;toast='';toast_until=0.
    camera_gate=[False]*4;camera_last=[-10.]*4
    smoke_stage=-1;smoke_time=0.;proof=set();frames=0
    sync_errors=[];rhythm_forms=set();rhythm_controls=[];rhythm_joints=[];kick_frames=0;rhythm_started=None
    if not synth.enabled:toast='Audio unavailable. Visual controls still work.';toast_until=time.monotonic()+7

    def notify(text):
        nonlocal toast,toast_until
        toast=text;toast_until=time.monotonic()+3

    def hit(index,source='LIVE',deck=None,event=None):
        if model.paused:return
        if source=='LIVE':music.set_auto(False)
        if source=='LIVE' and demo:performance.set_auto(False)
        deck=model.selected_deck if deck is None else deck
        event=event or performance.live(index,performance.position/4 if demo else model.clock*model.bpm/60.)
        model.trigger(index,source,deck)
        synth.play(index,deck,model.deck_speeds[deck],note=event.note,velocity=event.velocity,chord=event.chord,variant=event.variant)
        gain=math.cos(model.crossfade*math.pi/2) if deck==0 else math.sin(model.crossfade*math.pi/2)
        renderer.climax.note(index,gain*event.velocity)
        renderer.motion.note(index,event.velocity,gain)

    def load_track(path):
        nonlocal demo
        if not synth.enabled:notify('Audio device unavailable');return False
        try:
            notify('正在分析音乐…')
            data=ui.render(size,model,synth,renderer,camera,clock.get_fps(),toast,demo)
            renderer.draw(model,data);pygame.display.flip();pygame.event.pump()
            if demo:action('score')
            music.load(path);renderer.motion.reset();renderer.evolution.reset()
            renderer.evolution.strength=1.
            synth.silence();model.playing=False;model.recording=False
            model.paused=False
            notify('自动跟随音乐 / V 暂停 / Y 切换自动与手动')
            return True
        except (OSError,ValueError,pygame.error) as exc:notify(str(exc));return False

    def import_track():
        was_playing=music.playing;music.pause(True)
        model.holding=False;model.jog[:]=[None,None]
        loaded=False
        try:
            path=pick_audio_file(pygame.display.get_wm_info().get('window'))
            if path:loaded=load_track(path)
        except (OSError,ImportError) as exc:notify(str(exc))
        if not loaded and was_playing and not model.paused:music.pause(False)

    def select_extra(index):
        if model.paused:return
        if music.path:music.set_auto(False)
        if demo:performance.set_auto(False)
        model.select_shape(index)
        hit(VOICE_FOR_FORM[index],'FORM')

    def action(name):
        nonlocal demo,backup,backup_music,backup_forms
        if name in ('help','close_help'):
            ui.show_help=not ui.show_help;model.holding=False;model.jog[:]=[None,None]
        elif name=='camera':ui.show_camera=not ui.show_camera
        elif name=='grid':ui.show_grid=not ui.show_grid
        elif name=='mute':synth.muted=not synth.muted;music.muted=synth.muted;synth.silence()
        elif name=='music':
            if demo:
                action('score')
                if not music.running:music.toggle()
                else:music.pause(False)
            else:music.toggle()
        elif name=='import_music':import_track()
        elif name=='auto_music':
            if demo:performance.set_auto(not performance.auto)
            else:music.set_auto(not music.auto)
        elif name.startswith('form_'):select_extra(int(name.split('_')[1]))
        elif name in ('play','grid_play'):
            desired=not model.playing
            if demo:action('score')
            if music.playing:music.pause(True)
            model.playing=desired
            if desired and music.auto:renderer.evolution.strength=1.
            if model.playing and not any(any(row) for row in model.loop+model.loop_b):
                ui.show_grid=True;notify('循环是空的：点亮格子即可试听并开始循环')
        elif name in ('deck_a','deck_b'):model.selected_deck=0 if name=='deck_a' else 1
        elif name=='record':
            if demo:notify('Stop LOCAL before recording');return
            model.recording=not model.recording
            if model.recording:model.playing=True
        elif name=='clear':
            if toast=='Clear this deck? Click again.' and time.monotonic()<toast_until:
                for row in model.active_loop:row[:]=[False]*16
                notify('Cleared')
            else:notify('Clear this deck? Click again.')
        elif name=='demo':
            if music.path==DEMO_PATH and music.running and not demo:music.toggle()
            elif load_track(DEMO_PATH):notify('DEMO / Technological Messup / CC0 / 自动卡点')
        elif name=='score':
            if not demo:
                backup_music=music.playing;music.pause(True)
                backup=([r.copy() for r in model.loop],[r.copy() for r in model.loop_b],model.playing,model.recording,model.crossfade_target)
                backup_forms=(model.target,model.target_b)
                model.playing=False;model.recording=False;model.crossfade_target=.45
                renderer.motion.reset();renderer.climax.reset();renderer.evolution.reset()
                renderer.evolution.strength=1.
                synth.silence();synth.prepare(performance.score);performance.start()
            elif backup:
                performance.stop();synth.silence()
                model.loop,model.loop_b,model.playing,model.recording,model.crossfade_target=backup
                for deck,form in enumerate(backup_forms):model.select_shape(form,deck)
                renderer.climax.reset()
                if backup_music:music.pause(False)
            demo=not demo
        elif name=='bpm_up':model.bpm=min(160,model.bpm+4)
        elif name=='bpm_down':model.bpm=max(60,model.bpm-4)
        elif name=='export':
            try:notify('Saved '+save(model,renderer))
            except (OSError,pygame.error):notify('Cannot save. Check folder permissions.')
        elif name=='load':
            if demo:notify('Stop LOCAL before restoring');return
            try:restore(model,renderer);notify('Restored')
            except (OSError,ValueError,TypeError,KeyError):notify('No valid saved session')
        elif name=='cam_device':
            if not camera.active:camera.index=(camera.index+1)%4
            else:notify('Stop camera before changing device')
        elif name=='cam_start':
            if camera.active:camera.stop()
            else:camera.start(camera.index)
        elif name=='sensitivity_up':camera.sensitivity=max(.015,camera.sensitivity-.015)
        elif name=='sensitivity_down':camera.sensitivity=min(.3,camera.sensitivity+.015)

    def move_control(pos):
        nonlocal jog_angle,jog_last,scratch_last
        if drag=='fader' and ui.fader:
            model.crossfade_target=max(0.,min(1.,(pos[0]-ui.fader.left)/ui.fader.w))
        elif drag=='fx' and ui.fx_rect:
            model.fx_target[:]=[max(0.,min(1.,(pos[0]-ui.fx_rect.x)/ui.fx_rect.w)),max(0.,min(1.,1-(pos[1]-ui.fx_rect.y)/ui.fx_rect.h))]
        elif type(drag) is int:
            center,_=ui.jogs[drag]
            angle=math.atan2(pos[1]-center[1],pos[0]-center[0])
            delta=(angle-jog_angle+math.pi)%(2*math.pi)-math.pi
            now=time.monotonic();elapsed=max(.012,now-jog_last)
            speed=max(-3.,min(3.,delta/elapsed*.32));model.jog[drag]=speed
            jog_angle=angle;jog_last=now
            if now-scratch_last>.055:
                synth.scratch(VOICE_FOR_FORM[model.target if drag==0 else model.target_b],drag,model.deck_phases[drag],speed)
                scratch_last=now

    try:
        if args.music:load_track(args.music)
        if args.rhythm_test:
            if not args.music:action('demo')
            assert music.playing and music.analysis,'No analysed demo/track loaded'
            rhythm_started=time.monotonic()
        while running:
            dt=clock.tick(60)/1000.;frames+=1
            for event in pygame.event.get():
                if event.type==pygame.QUIT:running=False
                elif event.type==pygame.DROPFILE:load_track(event.file)
                elif event.type==pygame.VIDEORESIZE:
                    size=(max(1024,event.w),max(720,event.h))
                    pygame.display.set_mode(size,flags);renderer.resize(size)
                elif event.type==pygame.WINDOWFOCUSLOST:
                    model.release();model.jog[:]=[None,None];drag=None;synth.silence()
                elif event.type==pygame.KEYDOWN:
                    k=event.key
                    if k==pygame.K_ESCAPE:
                        if ui.show_help:ui.show_help=False
                        else:running=False
                    elif k==pygame.K_SLASH:action('help')
                    elif ui.show_help:
                        if k==pygame.K_RETURN:ui.show_help=False
                    elif k in (pygame.K_a,pygame.K_s,pygame.K_d,pygame.K_j,pygame.K_k,pygame.K_l):
                        hit((pygame.K_a,pygame.K_s,pygame.K_d,pygame.K_j,pygame.K_k,pygame.K_l).index(k))
                    elif k==pygame.K_TAB:model.selected_deck=1-model.selected_deck
                    elif k==pygame.K_SPACE and not model.paused:model.holding=True
                    elif k==pygame.K_i:action('grid')
                    elif k==pygame.K_h:ui.hide=not ui.hide
                    elif k==pygame.K_m:action('mute')
                    elif k==pygame.K_v:action('music')
                    elif k==pygame.K_u:action('import_music')
                    elif k==pygame.K_y:action('auto_music')
                    elif k in (pygame.K_z,pygame.K_x):
                        performance.octave=max(-1,min(1,performance.octave+(-1 if k==pygame.K_z else 1)))
                        notify(f'Melody octave {performance.octave:+d}')
                    elif k in (pygame.K_4,pygame.K_5,pygame.K_6,pygame.K_7):select_extra(6+k-pygame.K_4)
                    elif k==pygame.K_r:action('record')
                    elif k==pygame.K_t:action('demo')
                    elif k==pygame.K_g:action('score')
                    elif k==pygame.K_e:action('export')
                    elif k==pygame.K_o:action('load')
                    elif k==pygame.K_c:action('camera')
                    elif k==pygame.K_q:model.accents[0]=0.;synth.play(1,model.selected_deck)
                    elif k==pygame.K_w:model.accents[1]=0.;synth.play(5,model.selected_deck)
                    elif k==pygame.K_p:
                        model.paused=not model.paused;model.release();model.jog[:]=[None,None];synth.silence()
                        music.pause(model.paused)
                    elif k==pygame.K_BACKSPACE:model.reset();renderer.climax.reset();renderer.motion.reset();renderer.evolution.reset()
                    elif k in (pygame.K_1,pygame.K_2,pygame.K_3):renderer.palette=k-pygame.K_1
                    elif k==pygame.K_b:renderer.light_background=not renderer.light_background
                    elif k in (pygame.K_MINUS,pygame.K_EQUALS):synth.volume=max(0.,min(.8,synth.volume+(.05 if k==pygame.K_EQUALS else -.05)))
                    elif k==pygame.K_f:
                        try:pygame.display.toggle_fullscreen();size=pygame.display.get_window_size();renderer.resize(size)
                        except pygame.error:notify('Fullscreen unavailable')
                elif event.type==pygame.KEYUP and event.key==pygame.K_SPACE:
                    if model.holding and not model.paused:
                        amount=model.release();synth.drop(amount);renderer.climax.drop(amount,model.weights)
                elif event.type==pygame.MOUSEWHEEL and not ui.show_help:
                    renderer.zoom_target=max(4.8,min(10.,renderer.zoom_target-event.y*.25))
                elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    pos=event.pos;used=False
                    for name,r in ui.buttons.items():
                        if r.collidepoint(pos):action(name);used=True;break
                    if not used and not ui.show_help:
                        for i,r in enumerate(ui.pad_rects):
                            if r.collidepoint(pos):hit(i);used=True;break
                        for r,row,col in ui.cells:
                            if r.collidepoint(pos):
                                if demo:action('score')
                                if music.playing:music.pause(True)
                                model.paused=False
                                model.toggle_cell(row,col)
                                if model.active_loop[row][col]:
                                    gain=math.cos(model.crossfade*math.pi/2) if model.selected_deck==0 else math.sin(model.crossfade*math.pi/2)
                                    if gain<.1:model.crossfade=model.crossfade_target=float(model.selected_deck)
                                    model.playing=True
                                    if music.auto:renderer.evolution.strength=1.
                                    hit(row,'GRID')
                                    notify('已加入并试听 / 循环播放中' if not synth.muted else '已加入 / 当前静音，按 M 开声音')
                                else:notify('已移除此音符')
                                used=True;break
                        if not used and ui.fader and ui.fader.inflate(8,14).collidepoint(pos):
                            drag='fader';move_control(pos);used=True
                        if not used and ui.fx_rect and ui.fx_rect.collidepoint(pos):
                            drag='fx';move_control(pos);used=True
                        if not used:
                            for deck,(center,radius) in enumerate(ui.jogs):
                                if math.hypot(pos[0]-center[0],pos[1]-center[1])<=radius:
                                    model.selected_deck=deck;model.jog[deck]=0.;drag=deck
                                    jog_angle=math.atan2(pos[1]-center[1],pos[0]-center[0]);jog_last=time.monotonic()
                                    used=True;break
                        if not used:drag='orbit'
                elif event.type==pygame.MOUSEBUTTONUP:drag=None;model.jog[:]=[None,None]
                elif event.type==pygame.MOUSEMOTION and drag is not None:
                    if drag=='orbit':
                        dx,dy=event.rel;renderer.orbit_target[0]+=dx*.003;renderer.orbit_target[1]+=dy*.003
                    else:move_control(event.pos)
            if type(drag) is int and time.monotonic()-jog_last>.08:model.jog[drag]=0.
            keys=pygame.key.get_pressed()
            if not ui.show_help:
                renderer.orbit_target[0]+=(keys[pygame.K_RIGHT]-keys[pygame.K_LEFT])*dt*.6
                renderer.orbit_target[1]+=(keys[pygame.K_DOWN]-keys[pygame.K_UP])*dt*.6
            if synth.enabled:
                measured=music.sample()
                renderer.motion.external=measured if music.playing else [0.,0.,0.]
                renderer.motion.detect_external=not (music.playing and music.analysis is not None)
                renderer.climax.music_level=sum(a*b for a,b in zip(measured,(.2,.35,.45))) if music.playing else 0.
                if music.playing and not model.paused:
                    for attack in music.take_attacks():
                        age=max(0.,music._position-attack.time)
                        if args.rhythm_test:
                            sync_errors.append(age)
                            if attack.voice==0:kick_frames+=1
                        strength=(.45+.55*attack.strength)*math.exp(-age*9.)
                        renderer.motion.note(attack.voice,strength)
                    for band in range(3):model.band_targets[band]=max(model.band_targets[band],measured[band])
                    model.energy_target=max(model.energy_target,sum(measured)/3)
                synth.duck=.28 if music.playing else 1.
            notes=model.advance(dt);synth.update(model)
            for index in notes:hit(index,'LOOP',0)
            for index in model.events_b:hit(index,'LOOP',1)
            if demo:
                for event in performance.advance(dt,model.bpm,model.paused,model.brake):
                    hit(event.voice,'DEMO',event.deck,event)
                if performance.done:action('score')
            if camera.active and not model.paused and not ui.show_help:
                for i,val in enumerate(camera.sample()):
                    if val>camera.sensitivity and not camera_gate[i] and model.clock-camera_last[i]>.7:
                        hit([1,2,3,4][i],'LOOP');camera_last[i]=model.clock;camera_gate[i]=True
                        model.fx_target[0]=.2 if i%2==0 else .8
                    if val<camera.sensitivity*.55:camera_gate[i]=False
            if args.smoke_test:
                smoke_time+=dt;stage=min(FORM_COUNT-1,int(smoke_time/2.8))
                if stage!=smoke_stage:model.select_shape(stage,0);smoke_stage=stage
                if smoke_time%2.8>2.4 and stage not in proof:
                    folder=Path('captures');folder.mkdir(exist_ok=True)
                    pygame.image.save(renderer.capture(),str(folder/f'proof-{stage+1}.png'));proof.add(stage)
                if smoke_time>FORM_COUNT*2.8:running=False
            if args.interaction_test:
                if frames==2:action('record')
                if frames==4:hit(2)
                if frames==6:
                    assert model.recording and any(model.loop[2]);action('record');action('grid')
                if frames==8:
                    r=next(r for r,row,col in ui.cells if row==1 and col==8)
                    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=r.center))
                if frames==10:
                    assert model.loop[1][8] and model.playing,'Grid did not start its loop'
                    action('export')
                if frames==12:model.loop[1][8]=False;action('load')
                if frames==14:assert model.loop[1][8];action('score')
                if frames==15:
                    assert performance.playing and performance.position>0 and not model.playing
                if frames==16:
                    action('score');assert model.loop[1][8] and not performance.playing
                if frames==17:
                    action('score');performance.position=32*16
                if frames==18:
                    assert not demo and model.loop[1][8],'Song completion lost the loop'
                    model.selected_deck=1;hit(4)
                if frames==20:select_extra(9);model.crossfade_target=.7;model.fx_target[:]=[.8,.7];model.jog[1]=-2.
                if frames==35:assert model.deck_speeds[1]<0. and model.target_b==9;model.jog[1]=None
                if frames==36:
                    action('export');model.select_shape(1,1);action('load');assert model.target_b==9
                if frames==38:action('help')
                if frames==40:assert ui.show_help;action('close_help')
                if frames==42:assert not ui.show_help;model.holding=True
                if frames==54:assert model.brake<1.;model.release();ui.hide=True
                if frames==56:pygame.event.post(pygame.event.Event(pygame.VIDEORESIZE,w=1152,h=768))
                if frames==60:assert renderer.size==(1152,768);running=False
            if args.music_test:
                if frames==2:
                    assert music.path and music.playing and music.auto,'Music import/auto failed'
                    assert 'import_music' in ui.buttons and 'auto_music' in ui.buttons,'Music controls missing'
                    from unittest.mock import patch
                    with patch('recur.player.pick_audio_file',return_value=None):action('import_music')
                    assert music.playing,'Cancelling import interrupted playback'
                    with patch('recur.player.pick_audio_file',return_value=str(music.path)):action('import_music')
                    assert music.playing and music.auto,'Import button path failed'
                if frames==4:hit(0);assert not music.auto,'Manual takeover failed'
                if frames==6:action('auto_music');assert music.auto,'Automatic follow failed'
                if frames==8:action('music');assert music.paused,'Music pause failed'
                if frames==10:action('music');assert music.playing,'Music resume failed'
                if frames==11:
                    action('score');assert music.paused and performance.playing,'Song did not pause imported audio'
                if frames==12:
                    action('score');assert music.playing and not performance.playing,'Song did not restore imported audio'
                if frames==14:
                    assert sum(model.bands)>0,'Measured audio did not reach geometry'
                    Path('captures').mkdir(exist_ok=True)
                    pygame.image.save(renderer.capture(),'captures/music-import-proof.png')
                    ui.show_grid=True
                if frames==15:
                    model.selected_deck=1
                    model.crossfade=model.crossfade_target=0.
                    r=next(r for r,row,col in ui.cells if row==0 and col==4)
                    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=r.center))
                if frames==17:
                    assert music.paused and model.playing,'Grid did not take over song playback'
                    assert model.loop_b[0][4] and model.crossfade>.8,'Muted deck did not become audible'
                    running=False
            if args.rhythm_test:
                rhythm_forms.add(model.target)
                rhythm_controls.append(renderer.evolution.vj.time)
                rhythm_joints.append(renderer.evolution.vj.edits)
                if time.monotonic()-rhythm_started>=12.:
                    assert len(sync_errors)>15 and kick_frames>5,'Drum motion missing'
                    assert len(rhythm_forms)==1,'Automatic playback cycled manual presets'
                    assert max(rhythm_controls)-min(rhythm_controls)>3.,'VJ spatial motion did not advance'
                    assert max(rhythm_joints)>=1,'No music-led compositional edit occurred'
                    assert max(sync_errors)<.10,(f'Playback/visual delay max {max(sync_errors)*1000:.1f} ms; '
                                                 f'mean {sum(sync_errors)/len(sync_errors)*1000:.1f} ms; '
                                                 f'{frames/(time.monotonic()-rhythm_started):.1f} FPS')
                    assert renderer.motion.activity>.05,'Geometry motion stayed inactive'
                    running=False
            renderer.instrument_visible=not ui.hide
            data=ui.render(size,model,synth,renderer,camera,clock.get_fps(),toast if time.monotonic()<toast_until else '',demo)
            renderer.draw(model,data)
            if args.interaction_test and frames==15:
                pygame.image.save(renderer.capture(),'captures/qa/song-interface.png')
            if args.music_test and frames==17:
                pygame.image.save(renderer.capture(),'captures/qa/grid-interface.png')
            if args.rhythm_test and not running:
                Path('captures').mkdir(exist_ok=True)
                pygame.image.save(renderer.capture(),f'captures/rhythm-{music.path.stem}.png')
            pygame.display.flip()
        if args.smoke_test:
            if len(proof)!=FORM_COUNT:
                print(f'SMOKE INCOMPLETE: {len(proof)}/{FORM_COUNT} forms');return 1
            print(f'SMOKE OK: {frames} frames; {len(proof)} forms; {renderer.ctx.info["GL_RENDERER"]}')
        if args.interaction_test:print('INTERACTION OK: two decks, loop, edit, restore, demo, reverse, FX, brake, help, resize')
        if args.music_test:print('MUSIC OK: import, VJ/manual takeover, loop auto-start, silent-deck recovery, pause/resume, UI')
        if args.rhythm_test:
            print(f'RHYTHM OK: {music.path.name}; {len(sync_errors)} attacks; {kick_frames} kick attacks; '
                  f'{len(rhythm_forms)} fixed manual base; {max(rhythm_joints)} VJ edits; mean/max scheduling delay {sum(sync_errors)/len(sync_errors)*1000:.1f}/{max(sync_errors)*1000:.1f} ms; '
                  f'{frames/(time.monotonic()-rhythm_started):.1f} FPS')
    finally:
        camera.stop();music.close();synth.silence();pygame.quit()
    return 0
