---
title: Browser compatibility
related:
  - title: Browser Support
    path: 'https://quasar.dev/start/browser-support'
  - title: Configuring quasar.config file
    path: quasar-config-file.md
---
In order to configure the browser compatibility for your app, you will need to edit the `/quasar.config` file:

Example "/quasar.config file":

```js
build: {
  target: {
    browser: 'baseline-widely-available',
    node: 'node22'
  }
}
```

Based on the Quasar Mode that you will be using (SPA/SSR/SSG/PWA/Electron/... etc) you will have client-side files (that run in the browser) and possibly Node.js running files. This is what the two keys of `target` Object above are for.

Furthermore, based on your `/postcss.config.js` file content, your CSS will also pass through `autoprefixer` for which you can configure the browser levels that you are interested in:

Example "/postcss.config.js":

```js
autoprefixer({
  overrideBrowserslist: ['baseline widely available']
})
```

More info on how to specify `autoprefixer` browser ranges: [browserslist](https://github.com/browserslist/browserslist).
