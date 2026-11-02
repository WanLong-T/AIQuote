---
title: Installing BEX-specific dependencies
---
Notice the `/src-bex/package.json` file in your generated `/src-bex` folder. The purpose of it is for you to be able to install packages used by the BEX mode directly under this folder (and not pollute the common `/src`).

Example "/src-bex/package.json":

```json
{
  "name": "quasar-bex-app",
  "version": "1.0.0",
  "description": "Quasar BEX Folder",
  "private": true,
  "type": "module",
  "devDependencies": {
    "@types/chrome": "^0.2.5"
  }
}
```

Installing BEX specific packages:

```bash
# run in /src-bex for deps:
pnpm add <deps>

# run in /src-bex for deps used by the build system (eg. @types/chrome)
pnpm add -D <dev-deps>
```
