---
title: Upgrade guide on Electron
---
## Upgrading Electron

When you add the Electron mode in a Quasar project for the first time you will get the latest version of the Electron package. At some point in time, you will want to upgrade the Electron version.

Review Electron's [breaking changes](https://www.electronjs.org/docs/latest/breaking-changes) and release notes before upgrading. Move through major versions deliberately and rebuild any native dependencies afterward.

```bash
# from /src-electron:
pnpm add -D electron@latest
```
