---
title: Preparation for PWA
related:
  - title: Configuring quasar.config file
    path: ../quasar-config-file.md
---
Quasar CLI selects the PWA build target through the mode argument passed to `quasar dev` and `quasar build`.

In order to build a PWA, we first need to add the PWA mode to our Quasar project:

```bash
quasar mode add pwa
```

If you want to jump right in and start developing, you can skip the "quasar mode" command and issue:

```bash
quasar dev -m pwa
```

This will add PWA mode automatically, if it is missing.

A new folder will appear in your project folder (which is explained in detail on the [Configuring PWA](configuring-pwa.md) page):

- **src-pwa**
  - **register-sw.js**
    _(or .ts) UI code *managing* service worker (main thread)_
  - **manifest.json**
    _Your PWA manifest file_
  - **package.json**
    _helps install PWA only deps directly under /src-pwa_
  - **sw**
    _Service worker context (WebWorker)_
    - **custom-sw.js**
      _(or .ts) Optional custom service worker file (InjectManifest mode ONLY)_
    - **tsconfig.json**
      _TypeScript only - WebWorker lib, scoped to /src-pwa/sw/_

All the files above are going to be detailed in the next pages, but the high overview is:

- The `register-sw.js` file is part of the UI code and communicates with the service worker.
- The `manifest.json` is the PWA manifest file.
- When using InjectManifest, you can write your own custom service worker (`sw/custom-sw.js`). It lives in `/src-pwa/sw/`, code runs in WebWorker context (no DOM), and compiled separately from the rest of the app.

Should you want to use different filenames, you can do so by editing the `/quasar.config` file:

Example "/quasar.config file":

```js
sourceFiles: {
  pwaRegisterServiceWorker: 'src-pwa/register-sw',
  pwaServiceWorker: 'src-pwa/sw/custom-sw',
  pwaManifestFile: 'src-pwa/manifest.json',
}
```
