# Astropi Mission Zero Video Gallery Generator Requirements

## Mock emulator

- Write a Python script to record astropi mission zero animation to a folder. 
- iterate through all the astropi mission zero files (i.e. NAME.py) in a folder
- https://missions.astro-pi.org/mz/code_submissions/new
- check the animation fulfills mission zero requirements
- record the animation, output into out/NAME.mp4
- emulator mock MUST be realistic, timing, gaps and colors must be as in the webapp 

## Gallery

- Create a gallery of previews (use the png screenshots).  A click on the preview should open a lightbox and run the video. 
- Each preview should have as title astropi participant name and the project name.
- Previews may be large, I'd say 3 previews per row on desktop
- Page should display a prominent logo of ESA and Raspberry Pi foundation on one side, and a placeholder logo of the local instructor company carrying out the activity on the other side
- Must be attractive for youngsters, let them noticed they accomplished something important. 

### HTML Requirements:

- MUST work well both on desktop and mobile
- MUST support platforms >= Windows 10 21H2, MacOS 14 (Sonoma), IOS 18.6, Android 11, Ubuntu 24.

### Performance

- MUST load fast: vanilla JS, zero framework dependencies, single HTML file.
- MUST be responsive: interactive elements (sliders, buttons) MUST NOT lag.
- MUST keep CPU usage very low:
  - No persistent animation loops (setInterval, requestAnimationFrame running indefinitely).
  - All timers MUST be finite and self-clearing.
  - Slider updates MUST use targeted DOM patching (update specific element properties), never full innerHTML re-renders.

### Visual effects

- Static backgrounds only, no moving background symbols.
- Slight CSS transitions are acceptable (opacity fades, height transitions, hover state changes).
- Easter eggs on hover/click are acceptable (do not feel obliged to include them)