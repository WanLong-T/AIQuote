---
title: Installing PWA-specific dependencies
---
Notice the `/src-pwa/package.json` file in your generated `/src-pwa` folder. The purpose of it is for you to be able to install packages used by the PWA mode directly under this folder (and not pollute the common `/src`).

Example "/src-pwa/package.json":

```json
{
  "name": "quasar-pwa-app",
  "version": "1.0.0",
  "description": "Quasar PWA Folder",
  "private": true,
  "type": "module",
  "dependencies": {
    "register-service-worker": "^1.7.2"
  },
  "devDependencies": {
    "workbox-build": "^7.0.0",
    "workbox-cacheable-response": "^7.0.0",
    "workbox-core": "^7.0.0",
    "workbox-expiration": "^7.0.0",
    "workbox-precaching": "^7.0.0",
    "workbox-routing": "^7.0.0",
    "workbox-strategies": "^7.0.0"
  }
}
```

Installing PWA specific packages:

```bash
# run in /src-pwa for deps used by /src-pwa/register-sw file:
pnpm add <deps>

# run in /src-pwa for deps used by the build system (eg. workbox-* suite)
pnpm add -D <dev-deps>
```
