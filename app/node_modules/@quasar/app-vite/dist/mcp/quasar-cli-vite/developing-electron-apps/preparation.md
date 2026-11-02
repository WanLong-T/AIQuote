---
title: Preparation for Electron
---
## Add Quasar Electron mode

Add Electron mode to create `/src-electron` and install its workspace dependencies with your project's package manager:

```bash
quasar mode add electron
```

The main process and preload sources live in `/src-electron`; the renderer UI remains in `/src`.

> [!TIP]
> **Using pnpm with an older Electron version?**
>
> Electron v43+ downloads its binary on first launch, so no special setup is needed. Older Electron versions download it through a postinstall script instead — which pnpm does not run unless allowlisted. The scaffolded `/src-electron/pnpm-workspace.yaml` allowlists it through `onlyBuiltDependencies`. If your project predates this scaffolding and you pin Electron < 43 (symptom: the Electron binary is missing when running the app), add to `/src-electron/pnpm-workspace.yaml`:
>
> ```yaml
> onlyBuiltDependencies:
>   - electron
> ```
>
> ...then run `pnpm install` inside `/src-electron`.

The new folder has the following structure:

- **src-electron**
  - **electron-assets**
    _Assets that can be referenced from Electron files_
    - **icons**
      _Icons of your app for all platforms_
      - **icon.icns**
        _Icon file for macOS_
      - **icon.ico**
        _Icon file for Windows_
      - **icon.png**
        _PNG icon used by Linux and at runtime_
  - **electron-preload.js**
    _(or .ts) Electron preload script (exposes a controlled API to the renderer)_
  - **electron-main.js**
    _(or .ts) Main process code_
  - **package.json**
    _Electron-specific dependencies_

### Native dependencies

Most Electron packages use prebuilt binaries and require no local compiler. A dependency containing a native Node.js addon may need to be rebuilt for Electron's ABI.

On Windows, install Python 3 and Visual Studio's **Desktop development with C++** workload if a native dependency must compile. The Node.js installer can install the **Tools for Native Modules** for you. On macOS, install the Xcode Command Line Tools; on Linux, install Python, `make`, and a supported C/C++ compiler. See Electron's [native modules guide](https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules/) for rebuilding and troubleshooting native dependencies.

## Start developing

Run:

```bash
quasar dev -m electron

# passing extra parameters and/or options to
# underlying "electron" executable:
quasar dev -m electron -- --force-device-scale-factor=1
# when on Windows and using Powershell:
quasar dev -m electron '--' --force-device-scale-factor=1
```

This also adds Electron mode automatically when it is missing. It opens the application window and, with the default template, the renderer DevTools.

Arguments after `--` are forwarded to the Electron executable. Avoid disabling Chromium's sandbox as a general workaround; doing so removes an important security boundary.
