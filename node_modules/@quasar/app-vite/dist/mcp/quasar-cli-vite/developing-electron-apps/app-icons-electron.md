---
title: App Icons for Electron
---
These images represent your application in the operating system, including the desktop, file browser, taskbar or dock, tray, and relevant stores. The `icon.ico` file is for Windows, `icon.icns` is for macOS, and `icon.png` is used where a PNG is required. If you discover any that are missing, please [open an issue](https://github.com/quasarframework/quasar/issues).

## Icon Genie CLI

> [!TIP]
> We highly recommend using the [Icon Genie CLI](../../icongenie/introduction.md), because it consumes a source icon and automatically clones, scales, minifies and places the icons in the appropriate directories for you. When needed, it also tells you what tags you'll need to add to your /index.html file.

Quickly bootstrap the necessary images with Icon Genie CLI. For a complete list of options, please visit the [Icon Genie CLI](../../icongenie/command-list.md) command list page.

```bash
icongenie generate -m electron -i /path/to/source/icon.png
```

## Manual instructions

- **src-electron**
  - **electron-assets**
    - **icons**
      - **icon.ico**
      - **icon.icns**
      - **icon.png**
