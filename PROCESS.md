# RECUR — development record

This record was drafted with Codex from the author's directions and development
checks. The human-trial account below was supplied directly by the author on
29 October 2026; it is not inferred from automated tests.

## Starting intention

I wanted a visually ambitious, interactive artwork rather than an unchanged
tutorial or a passive animation. I selected the later transformations in
Lengfeng Guojing's *Ouroboros* as a reference: repeated metallic structural units,
radial segmentation, curling, closure and disassembly. I also liked the direct
action/sound/image feedback in Patatap, without wanting to recreate its shapes.

## Decisions made with AI assistance

OpenAI Codex helped translate the brief, inspect a locally supplied reference
clip, write the Python/OpenGL implementation, synthesize original audio and
debug the first version. This is substantial AI-generated code, not only
autocomplete. I still need to read, test and explain the action-to-response path.

Kept: a shared set of 648 repeated ribs transforms between six configurations.
The geometry is computed in a shader rather than using rendered video clips.
Sound and geometry share the same deliberate trigger, and a quantized loop lets
the player build and revise a short performance.

Changed/rejected: I rejected an earlier abstract glowing-object concept because
it lacked meaningful play. I also moved away from a generic colored-pad stage
after selecting the metallic radial reference. The reference supplies a visual
direction, not assets or music for redistribution.

The first graphical test revealed an oversized sculpture crossing the header
and controls. The rendering viewport was separated from the instrument area.
A Windows font-registry issue was fixed with direct standard-font paths and a
bundled Pygame-font fallback.

## Verification versus user research

### Browser migration and continuous structure — 29 October 2026

The owner reported that cycling a handful of presets still became repetitive.
This was useful direct feedback from the owner, not a substitute for the course's
separate user trial. The new browser implementation keeps the original ten
constructions but changes the automatic behavior: spectral profiles, contrast and
accumulated musical activity update aperture, layer distance, curling, sector
hinges, elongation, roll and depth. Related parts share hinges. The broader family
is held for longer passages, while dimensions continue evolving. I rejected the
earlier fixed-route suggestion because stronger beat pulses alone did not resolve
the owner's complaint about repetition.

WebGL2 shares the original rib mesh and construction code through an export
script. Audio decoding and playback use Web Audio; FFT/transient analysis runs in
a Worker to keep it off the drawing thread. No music upload or paid service is
required. Keyboard, tension, pointer control, decks, crossfader, 16-step loop,
overdub and browser-local save/restore provide deliberate user actions.

The assignment source was checked again. It permits Python as well as browser
projects and requires a public source repository; a live website is optional.
The browser port therefore improves access, rather than correcting a mandatory
format violation. Pages publication configuration is included, but publication
was not available at that stage while GitHub CLI was unauthenticated. A Sites registration was attempted
but the service connection failed; its state could not be confirmed, and no
second registration was attempted. No Sites deployment is claimed.

Codex generated substantial implementation and helped debug WebGL ES differences
(matrix blending and the shader version line). Automated worker/evolution checks
and actual browser demo/import checks are development evidence only. The owner
has supplied the human-trial account below. A post-change retest by that same
participant has not been confirmed.

Automated checks and local graphical smoke tests are development checks only.
They do not establish usability, musical quality or external-camera reliability.

## Human trial — reported by the author

The author confirmed that another person tried the keyboard interactions and
dragged the on-screen sliders. No participant identity is needed. The exact
trial date and whether guidance was given at the start were not recorded; the
account was documented on 29 October 2026.

| Actual observation reported by the author | Response made in the project |
|---|---|
| The participant initially perceived only S producing a single syllable/note; the sound was monotonous. | S and J now vary pitch within a harmonic palette. D/K supply changing chords and bass, A/L supply rhythm, and role-specific mixing and filtering make simultaneous parts more audible. An original multi-section score was added; the default demo later changed to a credited CC0 recording. |
| Shape transformations felt stiff. | Smooth morph interpolation and transient-led recoil, travelling folds and fin articulation were introduced. The original six constructions were restored after an overuse of central symmetry, with four extra radial constructions kept separately. The optional browser study further explores continuous structural parameters. |
| The participant suggested importing a song of their own. | A visible music-import control, U shortcut and drag-and-drop were added. Local frequency/transient analysis drives the geometry and automatic following; shape keys allow manual takeover. |

The author explained that these were the observations previously relayed during
development, not a new trial invented after implementation. They informed the
audio, movement and music-import changes above. These observations support the
reason for iteration; they do not demonstrate that every issue is now resolved.

**Retest:** the author has not confirmed a subsequent trial by the same person.
No claim is made that the participant approved the revised version. If a retest
is performed, record the actual action, hesitation and decision here.

## External-camera test — PENDING

The owner's built-in camera is damaged. Test with an external USB camera:
connection, correct device index, four motion zones, sensitivity, unplugging,
reconnecting, and continued keyboard operation when unavailable. Do not mark
this completed until it has been tried on actual hardware.

## Next author work

Review this AI-assisted record, check the real trial account, and explain one
input-to-response path in the code. A fresh retest is useful but is not claimed
here. Keep real subsequent commits. Screenshots and a program-rendered preview
are provided; neither is evidence of the human trial.

## Submission decision

### Further visual iteration after source upload

The author still found the desktop version repetitive: automatic playback cycled
presets, each with limited internal movement. This feedback exposed a gap between
the browser experiment and the submitted Python entry point. The Python renderer
now has a separate continuous construction engine. It has no preset route or
phrase-triggered form selector. Curvature, opening, layer spacing, depth, sector
hinges, screw and petal articulation develop from spectrum/history rather than
changing a silhouette ID on a timer.

An initial continuous-curvature oscillator still opened and closed too regularly
in the longer visual check, so it was replaced with a smooth coupled dynamical
system forced by the measured spectrum and percussion. This is not random
scattering. The same ordered ribs and sector anchors are retained, while internal
distances change substantially. All ten earlier shapes remain manual choices.
Indexed mesh reuse reduces repeated vertex work without removing triangles.

The new geometric checks compare normalized internal distance matrices, so a
rotation or zoom alone cannot satisfy them. Real playback checks now require a
fixed manual target and a developing curvature range instead of counting preset
switches. This is a further author-directed iteration; approval by the earlier
human trial participant has not been confirmed.

The author again reported that the result still looked like a few whole shapes
with small motions. The next iteration therefore changed the internal mechanism,
not just the amplitude of the previous controller. Six parent branches now each
contain three child fans, across up to nine rib layers. Independent damped joints
control winding, folding, roll and growth. The spine integrates a nonuniform
tangent field influenced by branch states. Early renders exposed conspicuous
breaks between branch groups; fading transforms at shared edges improved their
connection. Broad note-dependent force fields distribute attacks across branches.
Metal, glass and restrained exposure remain in place, and all ten manual forms
remain available.

The geometric tests now inspect the actual instance poses uploaded to the GPU,
including orthonormal frames, independent child motion and different responses
to different note histories at the same current loudness. Real playback also
checks child-joint movement. A one-minute render with the bundled recording is
provided for longer visual inspection. This is still author-directed iteration;
no new participant approval is claimed.

Verification on 30 October: 46 unit tests passed, the OpenGL smoke run exercised
all ten manual forms, and keyboard/loop/session and import/takeover checks passed.
Separate twelve-second playback runs measured 57.8 FPS for the bundled demo and
59.3 FPS for a second local recording. Mean/max transient scheduling lateness was
9.9/24.7 ms and 8.9/20.9 ms respectively. This measures event dispatch relative to
playback time, not end-to-end speaker/display latency or beat-estimation accuracy.

The author chose a public GitHub source repository as the submission, with the
Python artwork as the primary run target. Website deployment is not part of this
handoff; the browser experiment is retained and its publication workflow is
manual-only. Earlier notes describe exploration, not a requirement to host a site.

The existing implementation was consolidated into a real local source checkpoint
during submission preparation, followed by the documentation/trial checkpoint.
These commits were created now; no historical dates or earlier incremental
commits were fabricated. Preserve any later fixes and trial updates as further
actual commits.

Following the author's GitHub CLI browser authorization, the source and real
commit history were pushed to **https://github.com/CHEN526-f/recur** on the main
branch. The repository is public. Website deployment was not performed; its
workflow remains manual-only. A final documentation commit records the actual
repository address and submission steps. Canvas submission remains the author's
separate final action.

### Stage VJ direction and loop-editor feedback — 30 October 2026

The author rejected the articulated hierarchy as still looking like springs and
asked for stage VJ visuals. They also identified the A-to-S transition as a ring
breaking into a line, and said clicking the loop grid seemed to do nothing.
These observations changed the direction of the current runtime.

Automatic playback now uses six different spatial generators, with facets,
tapered blades and rounded crystals instead of the same curved rib everywhere.
A director chooses musical edits from real attacks, spectral novelty, phrasing
and recent composition usage. This is an explicit set of generative visual
families, not a claim of endless unrelated visual styles. Folding, depth travel,
surface curvature and spherical/torus reconfiguration continue within families.
Transitions pass through ordered folded/mirrored arrangements. Intermediate
renders exposed an unordered particle-cloud appearance; an ordered assembly
bridge and a latitude/longitude crystal layout improved that behavior. Manual
A-to-S transitions likewise use a folded mirror bridge; the original ten manual
forms remain available.

The loop grid previously only toggled stored cells; playback could be stopped,
LOCAL could block editing, or the selected deck could be silent in the crossfade.
Adding a cell now auditions it and starts loop playback. Editing pauses the track
or exits LOCAL and restores the user's pattern. A silent edited deck is moved
into the mix. Labels explain voices and steps; a playhead, dedicated play/pause,
deck gain and explicit mute status expose the actual state. GRID auditions do
not accidentally record a second cell or change the manual shape.

Verification includes 48 unit tests, real OpenGL renders of all six generators
and the A-to-S transition, all ten manual forms, and actual posted mouse events
for grid takeover, auto-start and silent-deck recovery. Demo and second-track
playback checks measured about 59 FPS on the development computer. Dispatch
lateness is measured separately from speaker/display latency. The one-minute
rendered preview is development evidence, not a new human-participant retest.

### Independent visual notes and English localization — 31 October 2026

The author again reported twitching and referenced Patatap's distinct key effects,
smooth combinations and simultaneous touch performance. They explicitly chose to
retain black/gold metal and limited glass instead of adopting flat graphics.
They also requested English everywhere except the project title.

The previous model still retargeted one global object on successive key presses.
The new default is therefore a polyphonic stage. Pulse, arcs, fan, ribbon, depth
outlines and sparks have separate captured parameters, clocks and envelopes.
New notes append to the composition; changes in the measured spectrum do not
warp existing notes. The viewport remains stable. Sculpture mode remains on F2.
Metal appearance uses a rounded cross-section normal/reflection treatment; sparse
glass samples the resolved opaque image. This is explicitly a 2.5D material model.

Keyboard and finger contacts have individual ownership. Held-key repeat is
suppressed, and releasing one contact leaves other contacts and animation tails
intact. Imported transients schedule the same voices, with conservative density
limits and band-based orchestration rather than a scene-switch playlist. This
mapping does not claim recognized melody notes or chords. Live overlays can
continue while imported audio plays.

English localization includes labels, notifications, help, file-chooser title,
run/submission documentation and the retained browser study. Proper project-title
characters are preserved. Non-ASCII imported filenames receive an English display
label; native operating-system controls follow the OS locale.

Verification distinguishes synthetic multi-finger events from physical hardware:
the latter has not been tested. The reference site's public description was read;
Windows browser interaction was stopped by the automation tool because it could
not reliably verify the current URL. No reference animation footage was captured
or imported. The author's observations above are real feedback; no additional
participant approval or post-change human trial is claimed.

Final development verification for this iteration: 57 Python unit tests and three
retained browser-study tests passed. The real desktop test processed three keys
and three synthetic fingers concurrently, confirmed independent release and held
key suppression, and let all notes expire naturally. Import, loop takeover,
silent-deck recovery and all ten sculpture forms passed their checks. A bundled
recording playback check ran about 59.7 FPS; mean/max transient dispatch lateness
was 8.2/19.4 ms. This is event dispatch timing, not a measurement of end-to-end
speaker/display latency. Longer rendered playback exposed excess stacked outlines;
automated note tails and bass accompaniment density were reduced while complete
manual one-shot gestures were retained. English UI images and a one-minute
H.264/AAC renderer preview are included as development evidence.
