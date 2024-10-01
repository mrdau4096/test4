# Test4
## _Simple 3D rendering/physics system created with Python and OpenGL_
### _(If I were you, I wouldn't expect too much from this.)_
I have created this as part of my Computer-Science Non-Exam Assessment project. The intention was to create a simplistic representation of a late 90s/early 2000s 3D FPS game, to learn the processes of 3D rendering and physics simulation. This was not created to be a 100% realistic depiction of reality in any way - compromises **have** been made. I intend to infrequently update this github repo, as I flesh out the idea more. Do not expect AAA quality from this project, this is my first foray into a 3D game. The latest release will be listed on the right-hand-side, with installation instructions within said page.
_**Thank you for visiting this page, and if you download; I thank you.**_

### All assets, scenes, UI, etc are non-final!
_They will change, in due time._



## Features;
- 3D textured graphics featuring simplistic lighting.
- Physics system, with support for external physics bodies and the player.
- Semi-featured, functional HUD.
- Human-readable data files for easier debugging
- Billboarded sprites. (DOOM93 demon-type sprite usage soon)
- Object-Oriented internal systems.
- 5 minute load time on low-end devices. _(Roughly 5s on anything capable)_


## Planned;
- Obligatory bugfixes.
- Items for the player to hold/use.
- Proper menus to interact with, rather than ESC = quit()
- Projectile and Hitscan weapons.
- Scene editing program within the filepath.


## Known Bugs;
- Transparent surfaces do not pass shadows through correctly.
- Sprites do not render correctly.
- Player "rebounds" off of the floor at high velocities/low framerates.
- When turning camera, speed appears inconsistant.
- Both sides of a triangle appear lit, if one side is. (Direction ignored by lighting)