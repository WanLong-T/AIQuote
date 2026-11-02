---
title: Directory Structure
---
This is the structure of a project with all modes installed. There's no reason to be intimidated though!

> [!TIP]
> If you are a beginner, all you'll need to care about is the `/quasar.config` file (Quasar App Config file), `/src/router`, `/src/layouts`, `/src/pages` and optionally `/src/assets`.

- **.**
  - **public/**
    _Pure static assets (copied as-is)_
  - **src**
    - **assets/**
      _Dynamic assets (processed by Vite)_
    - **components/**
      _.vue components used in pages & layouts_
    - **css**
      _CSS/Sass/... files for your app_
      - **app.sass**
      - **quasar.variables.sass**
        _Quasar Sass variables for you to tweak_
    - **layouts/**
      _Layout .vue files_
    - **pages/**
      _Page .vue files_
    - **boot/**
      _Boot files (app initialization code)_
    - **router**
      _Vue Router_
      - **index.js**
        _(or .ts) Vue Router definition_
      - **routes.js**
        _(or .ts) App Routes definitions_
      - **typed-router.d.ts**
        _TypeScript only, along with build.filenameBasedRouting enabled_
    - **stores**
      _Pinia Stores_
      - **index.js**
        _(or .ts) Pinia initialization_
      - **<store>**
        _Pinia stores..._
      - **<store>...**
    - **App.vue**
      _Root Vue component of your App_
  - **src-ssr/**
    _SSR specific code (like production Node.js webserver)_
  - **src-ssg/**
    _SSG specific code (like ssg-renderer script)_
  - **src-pwa/**
    _PWA specific code (like Service Worker)_
  - **src-capacitor/**
    _Capacitor generated folder used to create Mobile Apps_
  - **src-cordova/**
    _Cordova generated folder used to create Mobile Apps_
  - **src-electron/**
    _Electron specific code (like "main" thread)_
  - **src-bex/**
    _BEX (browser extension) specific code (like "main" thread)_
  - **dist**
    _Where production builds go_
    - **spa**
      _Example when building SPA_
    - **ssr**
      _Example when building SSR_
    - **electron**
      _Example when building Electron_
    - **...**
  - **quasar.config.js**
    _(or .ts) Quasar App Config file_
  - **index.html**
    _Template for index.html_
  - **.gitignore**
    _GIT ignore paths_
  - **.editorconfig**
    _EditorConfig file_
  - **eslint.config.js**
    _ESLint config_
  - **postcss.config.js**
    _PostCSS config_
  - **jsconfig.json**
    _Editor config (if not using TypeScript)_
  - **tsconfig.json**
    _TypeScript config_
  - **env.d.ts**
    _TypeScript only_
  - **package.json**
    _npm scripts and dependencies_
  - **README.md**
    _Readme for your website/App_
