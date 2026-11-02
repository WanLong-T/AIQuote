---
title: Page Routing with Vue Router
---
You'll notice that your Quasar project contains a `/src/router` folder. This holds the routing configuration of your website/app:

- "/src/router/index.js" holds the Vue Router initialization code
- "/src/router/routes.js" holds the routes of your website/app

> [!NOTE]
> Quasar documentation assumes you are already familiar with [Vue Router](https://github.com/vuejs/vue-router). Below it's described only the basics of how to make use of it in a Quasar CLI project. For the full list of its features please visit the [Vue Router documentation](https://router.vuejs.org/).

## Basic Usage

The `/src/router/routes.js` needs to import your website/app's Pages and Layouts. Read more on [Routing with Layouts and Pages](https://quasar.dev/layout/routing-with-layouts-and-pages) documentation page.

When using Pinia, the store is not directly importable from other scripts, but it is passed to the exported function of `/src/router/index.js`, so it can be accessed from there. For example you can use the `Router.beforeEach` method to check authentication in the router:

Example "/src/router.js":

```js
import { defineRouter } from '#q-app'

export default defineRouter(({ store /*, ssrContext */ }) => {
  // ...
  const userStore = useUserStore(store)

  Router.beforeEach((to, from) => {
    if (
      to.matched.some(record => record.meta.requiresAuth) &&
      !userStore.isSignedIn
    ) {
      return { name: 'account-signin', query: { next: to.fullPath } }
    }
  })
  // ...
})
```

> [!NOTE]
> If you are developing a SSR/SSG app, then you can check out the [ssrContext](developing-ssr/ssr-context.md) Object that gets supplied server-side.

## Filename-Based Routing *(Vue Router v5+)*

### How to enable

Should you want to use Vue Router's filename-based routing, rather than manually handling the `/src/router/routes` file, then kill the devserver (if running), then edit:

Example "/quasar.config file":

```ts
build: {
  /**
   * Should you want to use Vue Router's filename-based routing feature.
   * Set to `true` or an options object for vue-router/vite plugin (to override
   * or add to the default options).
   *
   * Restart the dev server and your IDE when toggling this option,
   * or run "quasar prepare" command.
   *
   * @type boolean | VueRouterVitePluginOptions
   * @default false
   */
  filenameBasedRouting: true
}
```

You also need to edit:

Example "/src/router/index file":

```js
- import routes from './routes'
+ import { routes, handleHotUpdate } from 'vue-router/auto-routes'

export default defineRouter((/* { store, ssrContext } */) => {
  const Router = createRouter({
    routes
    // the rest....
  })

+   // enable HMR for it
+   if (import.meta.hot) {
+     handleHotUpdate(Router)
+   }

  return Router
})
```

Please note that you need to restart the dev server after toggling this option, or run "quasar prepare" command. You might also need to restart your IDE afterwards, too.

### Folder structure

When this feature is enabled, you will need to:

- Change the `/src/pages` folder structure to match [Vue Router naming convention](https://router.vuejs.org/file-based-routing/file-based-routing.html)
- Delete `/src/router/routes.js|ts` file
- Delete `/src/layouts` because it serves no purpose now (or incorporate it into `/src/pages`)

Here is an example of the folder structure:

- **/src**
  - **router**
    - **index.js**
      _(or .ts)_
  - **pages**
    - **index.vue**
      _layout for route "/"_
    - **index**
      - **(index).vue**
        _page for route "/"_
      - **second.vue**
        _page for route "/second"_
    - **admin.vue**
      _layout for route "/admin"_
    - **admin**
      - **(index).vue**
        _page for route "/admin"_
      - **account.vue**
        _page for route "/admin/account"_

### Default options

When `filenameBasedRouting` is set to `true` or an options object is supplied (overriding or adding to the default config), this is the default options supplied to the `vue-router/vite` plugin:

```js
{
  // where are paths relative to:
  root: <root_project_folder>,

  // where to generate the types (if on TypeScript projects):
  dts: './src/router/typed-router.d.ts',
}
```

For more info on the object: [Vue Router configuration](https://router.vuejs.org/file-based-routing/configuration.html).
