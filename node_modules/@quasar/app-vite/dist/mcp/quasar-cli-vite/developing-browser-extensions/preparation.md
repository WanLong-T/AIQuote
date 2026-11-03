---
title: Preparation for BEX
---
Quasar CLI selects the browser-extension build target through the mode and target arguments passed to `quasar dev` and `quasar build`.

## Add Quasar BEX Mode

In order to build a BEX, we first need to add the BEX mode to our Quasar project:

```bash
quasar mode add bex
```

If you want to jump right in and start developing, you can skip the "quasar mode" command and issue:

```bash
quasar dev -m bex -T [chrome|firefox]
# default target is "chrome", so -T can be omitted
```

This will add BEX mode automatically, if it is missing, by creating the `/src-bex` folder into your project.

> [!NOTE]
> The `src-bex` folder is just a standard browser extension folder so you are free to use it as you would any other browser extension project folder. Please refer to supported Browser Extension documentation to learn more.
>
> - [Google Chrome Browser Extension Documentation](https://developer.chrome.com/extensions)
> - [Firefox Browser Extension Documentation](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions)
> - **Other Chromium Based Browsers** - Refer to their specific documentation.

## The Anatomy of "/src-bex"

The new folder has the following structure:

- **src-bex**
  - **assets**
    - **content.css**
      _CSS file which is auto injected into the consuming webpage via the manifest.json_
  - **icons**
    _Icons of your app for all platforms_
    - **icon-128x128.png **
      _Icon file at 128px x 128px_
    - **icon-16x16.png**
      _Icon file at 16px x 16px_
    - **icon-48x48.png**
      _Icon file at 48px x 48px_
  - **_locales/**
    _Optional BEX locales files that you might define in manifest_
  - **manifest.json**
    _The browser extension manifest file_
  - **background.js**
    _(or .ts) Standard background script BEX file (auto injected via manifest.json)_
  - **my-content-script.js**
    _(or .ts) Standard content script BEX file - auto injected via manifest.json (you can have multiple content scripts)_
  - **package.json**
    _helps install BEX only deps directly under /src-bex_
  - **bex-end.d.ts**
    _TypeScript only_

The next section will discuss these in more detail.
