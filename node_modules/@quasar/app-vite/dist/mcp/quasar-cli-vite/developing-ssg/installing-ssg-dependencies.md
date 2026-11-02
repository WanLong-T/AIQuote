---
title: Installing SSG-specific dependencies
---
> [!WARNING]
> **Warning! Beta Stage**
>
> The Quasar SSG Mode is currently in the "beta" stage. Based on the community feedback, the API may change in the future, so check the release notes each time you upgrade "@quasar/app-vite".

The generated `/src-ssg/package.json` keeps build-time renderer dependencies separate from your application dependencies. Add a package here when it is imported directly by `/src-ssg/ssg-renderer`.

Example "/src-ssg/package.json":

```json
{
  "name": "quasar-ssg-app",
  "version": "1.0.0",
  "description": "Quasar SSG folder",
  "type": "module",
  "private": true,
  "dependencies": {}
}
```

> [!IMPORTANT]
> Packages imported by application code under `/src` still belong in the root `package.json`. Install only renderer-specific packages under `/src-ssg`.

For example, to discover Markdown files from the renderer with `tinyglobby`:

```bash
# run in /src-ssg
pnpm add tinyglobby
```
