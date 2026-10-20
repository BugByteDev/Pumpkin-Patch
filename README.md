# Pumpkin Patch

Native Python jack-o'-lantern creator. The application UI is painted with PySide6/QPainter; Python and PyOpenGL own the 3D viewport. GPU shading uses GLSL. The desktop application does not use a browser engine, HTML UI, or JavaScript, and does not require Blender at runtime.

## Downloads

[Windows x64 and Linux x64 beta downloads](https://github.com/BugByteDev/Pumpkin-Patch/releases) are available from GitHub Releases. Extract the entire archive before launching. Neither Python nor Blender needs to be installed.

## Run

On this Mac, open `releases/Pumpkin Patch.app`. This is an Apple Silicon build with the Python runtime, native libraries, font, and body lattices included.

For source development, use Python 3.13:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

On Windows use `.venv\Scripts\python` instead. Linux needs a working desktop/OpenGL driver and Qt platform dependencies.

## Controls

- Drag to rotate, scroll to zoom. The pumpkin follows the horizontal drag direction. Front view resets the camera.
- New pumpkins start with a blank face: no eyes, eyebrows, nose, mouth, teeth, extras, or custom cuts. Existing drafts and saved designs retain their features.
- Pick any body or optional part in the face shop. None removes the part. Left/right features can be linked or edited independently.
- Move, resize and rotate features in the right inspector. Whole faces provides 24 starting designs; every facial part remains editable.
- Freehand carver locks the front view. Draw a closed shape and release. Stabilize adjusts stroke smoothing; Mirror cuts previews and carves an exact reflected counterpart. Undo cut removes a reflected pair together.
- Light it up animates the lid and candle. Candlelight keeps the doodle renderer.
- Save to my patch stores a local gallery entry. Save file writes an editable `.pumpkin` design. Open file reads one.
- Export GLB writes an indexed, smooth, hollow carved model with separate closed parts in metres, sized to the selected diameter. Smoothly clipped palette boundaries and baked materials preserve the doodle colors without depending on vertex-color support; compatible viewers also use unlit shading. The lighting is static; screen-space outlines and animated candlelight remain in the app. Lit designs include the candle and flame. Check fine details in a slicer before printing.
- GLB exports, editable pumpkin files and carving guides are automatically revealed in Finder after a successful save on macOS.
- Carving guide writes printable HTML with vector outlines, white teeth to keep, instructions, a scale factor and a 5 cm calibration. This is an exported document, not the app UI.
- Ctrl/Command Z undoes; Shift Ctrl/Command Z redoes. Escape exits a carving tool. Alt F resets the front view; Alt L toggles candlelight.

Your current draft is autosaved. On macOS, the draft and gallery live in `~/Library/Application Support/PumpkinPatch`. No account or network connection is needed.

## Library

8 bodies, 6 stems, 4 lids, 24 eyes, 8 eyebrows, 12 noses, 48 mouths, 12 tooth arrangements, 8 extras, and 24 complete face presets. Teeth are removable independently and grow from the actual mouth rim. No AI-generated raster images are used.

## Validate and rebuild

```sh
python -m unittest discover -s tests
python -m pip install pyinstaller
pyinstaller PumpkinPatch.spec
```

Build on the target operating system. The macOS Apple Silicon app is built locally. Windows x64 and Linux x64 beta builds are compiled on their native operating systems with GitHub Actions. Both pass the test suite and compiled-app software OpenGL checks, including spawned carving workers and saved gallery previews. Hardware drivers, native file dialogs and printing still need real-world testing.

`tools/build_assets.py` rebuilds the bundled base surfaces with Blender. The editable Blender source and base GLBs are in `assets/`. Runtime Boolean carving uses manifold3d and does not use voxels.

The older `web/` and `server.py` files are retained as the earlier UI reference. They are not imported by `main.py` and are not bundled into the native app.

The Patrick Hand font is redistributed under its included OFL license in `assets/fonts/`. Third-party runtime components retain their respective upstream licenses.

### Preview and geometry caching

Run `python tools/prerender.py` before packaging after changing preset designs or mesh styling. Preset, body and stem thumbnails ship in `assets/previews`; the app reads these PNGs directly. All artwork is rendered from the app's own meshes.

Edited pumpkin meshes and thumbnails are cached by their visual contents under the application data folder's `cache` directory. Restarting or renaming a pumpkin reuses the cache. Color and candlelight changes reuse geometry; a changed carving produces a new mesh. Old designs and caches are retained. If the drive is nearly full, the app continues in memory and skips new cache writes. Bump `model_cache.VERSION` after changing mesh or shading rules.

Unlit pumpkins redraw on interaction and window exposure. Lit pumpkins also redraw for the candle animation.

## Free Windows and Linux builds

The **Build Windows and Linux beta** workflow in GitHub Actions builds both x64 platforms on standard free public-repository runners. Run it manually from the Actions tab. It refuses private repositories, does not use paid runners or Actions caches, and stores downloads as Release assets rather than billed Actions artifacts. A draft prerelease is published only when both platform jobs pass.

Each job runs the full test suite, compiles with PyInstaller, then starts the compiled app from a temporary directory outside the source tree. The smoke check uses isolated data, checks the blank pumpkin, a scary preset, custom carving, rotation, candlelight, gallery, info, editable save, carving guide and GLB export, and saves screenshots. Linux uses Xvfb/Mesa; Windows uses a hash-verified Mesa driver for CI only. That driver is not shipped in the app and never replaces system drivers.

Downloads are a Windows ZIP and Linux tar.gz. Extract the whole archive and keep `_internal` beside the executable. Python and Blender are not required. Hardware driver compatibility, native file dialogs and printing still need manual testing, so these releases are marked beta.
