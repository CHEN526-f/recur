# Visual refinement — iteration log

## Current: stage VJ and spatial reassembly — 30 October 2026

The author rejected the hierarchy below as still spring-like. The current
runtime uses six spatial generators in `recur/vj.py`: moving polygon tunnels,
mirrored fans, folded surfaces, crystal spheres/toruses, ribbons and prism rooms.
Their facet, tapered-blade and rounded-crystal profiles differ from the old C rib.
Musical attacks, novelty, phrasing and recent usage drive the stage director.
There is no fixed playlist; each generator also develops its internal geometry.

Edits pass through an ordered folded surface or mirror assembly. The end lands
on an estimated beat; drum articulation still uses the measured transient. The
original manual A-to-S transition now uses a segmented folded bridge as well.
The original ten shapes remain manual choices. Flat-panel normal transforms are
corrected for anisotropic scale, and their light level is slightly reduced.

Current evidence: `demo.mp4`, `evolution-sequence.jpg`, `manual-reassembly.jpg`,
`vj-families.jpg` and `loop-editor.png`. The loop grid now auditions and starts on
cell addition and exposes play/mute/deck state. These are development checks.
The following sections document superseded approaches and the feedback on them.

## Articulated hierarchy — 30 October 2026

The next critique was that continuous global bending still read as a few familiar
outlines. That iteration added six parent branches and
three child fans per parent across up to nine layers. Parent folding/stretching,
child winding/roll/growth and a locally varying spine are separate motions.
Distinct initial joint states avoid synchronized unfolding. Measured notes apply
forces to overlapping regions, then damped joints settle them. Drum attacks also
fold alternating parent joints and open the fins immediately.

The first hierarchical render had conspicuous gaps. Joint influence now fades
at shared edges so neighboring groups remain joined. The previous global-strip
shader was removed. The CPU computes instance centers and orthonormal frames
once; both surface passes read the same floating-point pose texture. Tests use
these actual poses, rather than a separate obsolete path formula.

The one-minute preview shows the current automatic construction. Original manual
forms, restrained bloom, metal and limited glass remain available. The following
sections record earlier approaches and their limitations.

## Python continuous morphogenesis — after the initial source upload

The owner still found the Python artwork to be a repeated preset carousel with
minor articulation. The runtime preset selectors and their precomputed routes
have now been removed from the Python music/score path. The ten manual forms
remain intact; automatic playback keeps its manual target unchanged and drives
one continuously remodelling construction instead.

Ordered rib indices map onto a mean-centred bent strip. Varying curvature takes
the strip through open arches and nested spirals. Sector anchors fan related ribs,
while spacing, aperture, depth, layer screw and petal harmonics change internal
structure. The main geometry and emerging outer layers share this construction.
The spectrum and percussion force a smooth Lorenz-type coupled controller with
musical memory. The first periodic-curvature attempt was rejected after its
regular opening/closing became apparent in the longer preview. This controller
has no assigned pose loop or randomized preset choice.

Drum recoil remains scheduled from measured audio. Manual notes add a smaller
amount of structural articulation while keeping the chosen foundation. Pause
freezes the controller; silent audio supplies no structural time progression.
Exposure, metal, glass and bloom are unchanged. Indexed meshes retain the same
triangles while avoiding repeated work on identical vertices.

The preceding 36-second renderer preview held one manual target throughout. Geometric
checks compare normalized pairwise distances, so camera rotation or zoom cannot
pass as structural change. The actual playback test also asserts one fixed target
and a developing curvature range. These are development checks, not a confirmed
retest by the earlier human participant. Older dated sections below document the
preceding implementations, including their superseded preset behavior.

## Measured recording playback — 29 October

The default T / DEMO now plays the bundled CC0 recording *Technological Messup*
by Centurion_of_war. Attribution and source links are in `assets/music/CREDITS.md`.
The original 32-bar synthesizer composition remains under G / LOCAL.

DEMO and user imports share 100 Hz spectral-flux analysis, short energy-slope
timing refinement and transient classification. The audio playback cursor drives
the attack scheduler. Major morphs anticipate selected beat accents by up to
320 ms and finish on them; actual drum recoil is triggered at the measured
attacks. Beat estimation guides phrasing, not replacement drum sounds. Tempo
inference can be ambiguous in syncopated or beatless recordings. Neither song
emotion nor musical key is claimed to be recognized.

Regression checks include offbeat hats, continuous pitched accompaniment,
synthetic kicks within 25 ms of their known timing, silent/steady-tone rejection,
one-shot event consumption and morph completion on accents. The actual app's
12-second `--rhythm-test` was also run separately with the default recording and
an independently imported *Dance field* (CC0, same author). Each ran at about
59 FPS with approximately 10 ms mean attack scheduling delay. This is software
scheduling latency, not a measurement of the speaker/display hardware latency.
Simultaneous graphical tests contended for the GPU, so playback checks are run
one at a time. `tools/preview_track.py` exports the measured path with the source
recording to `captures/rhythm-demo.mp4` for inspection. Facet fins are narrowed
tangentially to retain discrete modules instead of overlapping into a solid mass.

## Audible music now produces visible articulation — 29 October

The SONG transport previously excluded its events from form selection, while the
geometry used only a 3.5% bass scale change. Dense melody also accumulated enough
excitation to pin expansion near its maximum. The result felt almost static.

SONG now chooses a construction every two bars with smooth existing morphs,
covering all ten shapes while retaining the original six as the majority.
Manual keys take over; Auto/Y returns to the current phrase. Stopping restores
the previous deck forms. No construction was removed or replaced.

A shared articulation stage affects both inner and outer geometry: kick attacks
produce up to 20% recoil, sustained midrange drives travelling folds and layer
torsion, and high-frequency attacks hinge individual fins. Envelopes decay rather
than accumulate, keeping attacks distinct. Imported audio drives these envelopes
through measured spectral rises; constant tones do not produce fictitious kicks.
Song motion uses the score's beat, including braking and pause. Section/phrase
expansion opens at the peak and recedes during breaks instead of saturating.
Metal, glass fraction, exposure and bloom settings are retained.

The added checks cover actual construction displacement, bounded articulation of
all ten forms, transient recovery, sustained tones, silence, pause, manual
takeover and phrase expansion. `tools/preview_motion.py` renders the real score
and shader to `captures/motion/song-motion.mp4`, with a contact sheet for inspection.
This is development verification, not a human trial.

## Music import and automatic following

A visible Chinese-labelled import button opens a user-operated native file
chooser. Drag-and-drop and CLI import remain available. Import starts playback
and automatic following. Low/mid/high envelopes drive continuous deformation;
spectral balance, transients and section contrast choose forms on musical accents
after several beats, rather than switching at each drum hit. Quiet passages hold the
form. Manual shape selection takes over without stopping the track; Auto resumes
following. No existing form or performance control was removed.

## Current direction: restore the six originals, add separately

The user rejected replacing the entire vocabulary with central symmetry. The
original serpent, open ribbon, curled bloom, rectangular crystal field, orbital
bands and folded tide have been restored to A/S/D/J/K/L, with their original
centre paths, scale and local articulation. Iris/corona/rosette/facet remain as
four extra choices on 4/5/6/7. Materials, bloom, glass, audio and interaction
controls are retained. No global symmetry constraint is imposed on the originals.
The notes below describe the preceding iterations and why this correction was
needed. The original six and the extra four now have separate regression checks.

The new reference frames prompted a change in scale: a high-register phrase or
performed release can open the sculpture across the screen. The user then asked
for richer metal, some glass, restrained exposure, and a coherent overall form
instead of an unrelated strip crossing the centre.

The inner sculpture now transforms into the same architecture as its outer fins.
The latest revision uses one polar mechanism with four/six/eightfold harmonics,
paired orbital planes and an elongated serpent. Four inner layers become ten
layers during expansion. All forms share angular module indices and ordered
radii. Morphing blends bounded construction parameters rather than unrelated
Cartesian vertex clouds; common-centre symmetry survives transitions. Opposing
ribs, ring order and silent-audio response have automated checks.
Glass-note phrases, chords, and short noise accents accumulate different
amounts of expansion. Isolated bass notes leave the space quiet. The audible
deck's crossfader gain scales the response. Expansion and return have separate,
smooth envelopes. A release sustains the space briefly; pause freezes it.

Rounded fins and beveled crystal tiles replace the flat cuboid appearance.
Gold, silver and copper use conductor Fresnel response, a GGX highlight, and
procedural studio reflections. About one fin in thirteen is a dielectric accent:
it transmits and slightly refracts the resolved opaque scene, with cooler edges
and a Fresnel reflection. This is a real-time screen-space approximation; it does
not trace multiple glass layers or objects outside the framebuffer.

HDR rendering retains separate tight and broad bloom. Exposure and source light
were reduced after the user rejected the overbright result. The final small
bloom increase affects the highlight halos rather than the surface light level.
ACES tone mapping rolls off highlights. No reference frame, model, video, texture
or soundtrack is embedded in the implementation.

`python tools/preview_crescendo.py` exercises a quiet passage, high notes and a
return to quiet, saving actual OpenGL proof frames in
`captures/crescendo/`. These and the unit checks are development verification,
not a human usability trial. Actual musical and aesthetic feedback remains the
author's decision.

The supplied 113.76-second local video was sampled across its duration, with a
closer 38–60-second sequence study. Common centre, repeated modules, hinged
sectors and alternating inner/outer motion informed this revision; its models,
texture, video frames and soundtrack are not used as product assets.

The local fallback sound was revoiced into D minor nine: soft tuned kick and bass,
quiet glass plucks, a warm pad and subdued shaker. Imported music is decoded and
analysed in frequency bands, then its measured envelopes drive geometry. Phrase
changes originally used the user-selected BPM; the current importer estimates
tempo and uses measured beat accents as described above.
`captures/structure-preview.mp4` demonstrates the actual renderer with this local
fallback sound. It is clearly distinct from the still-unfinished Suno workflow.
