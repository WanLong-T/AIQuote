---
title: SSR with TypeScript
---
When SSR mode is added to a TypeScript project, Quasar scaffolds TypeScript files in `/src-ssr`. If the project was converted to TypeScript after SSR mode was added, rename the `.js` files in `/src-ssr` to `.ts` and apply the required type annotations.

Check the [SSR Webserver](ssr-webserver.md) and [SSR Middleware](ssr-middleware.md) pages for examples with TypeScript.

Depending on the webserver of your choice, you may also need to additionally [install @types/* packages](installing-ssr-dependencies.md) into your /src-ssr folder.
