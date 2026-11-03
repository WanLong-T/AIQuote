---
title: Preparation for SSR
related:
  - title: Configuring quasar.config file
    path: ../quasar-config-file.md
---
Quasar CLI selects the SSR build target through the mode argument passed to `quasar dev` and `quasar build`.

To develop or build an SSR website, first add SSR mode to the Quasar project:

```bash
quasar mode add ssr

# or, to skip the webserver prompt (useful for scripts/CI):
quasar mode add ssr --webserver hono # or fastify, express, koa
```

If you want to jump right in and start developing, you can skip the "quasar mode" command and issue:

```bash
quasar dev -m ssr
```

This will add SSR mode automatically, if it is missing. In a non-interactive environment (such as CI), where the webserver prompt cannot be answered, the Hono webserver is picked automatically.

After you choose Hono, Express, Fastify, or Koa as the webserver, a new folder appears in your project (explained in detail on the [Configuring SSR](configuring-ssr.md) page):

- **src-ssr**
  - **server-assets/**
    _copied as-is to dist_
  - **middlewares**
    _SSR middleware files_
    - **render.js**
      _(or .ts) middleware to render pages with Vue_
  - **server.js**
    _(or .ts) SSR webserver_
  - **package.json**
    _helps install SSR only deps directly under /src-ssr_
