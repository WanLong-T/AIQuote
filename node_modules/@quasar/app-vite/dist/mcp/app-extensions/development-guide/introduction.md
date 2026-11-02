---
title: App Extension Development
---
This section of the docs deals with creating your own App Extensions.

It is assumed you have already installed one of the official App Extensions. Having this experience at your disposal is going to be very valuable when you start building your own App Extensions. If you run into problems, please visit our Discord server's channel `#app-extensions`.

An App Extension is essentially just an npm package that Quasar CLI loads to provide the functionality that you supplied.

## Creating the App Extension

Example "PNPM v11+ only!":

```bash
pnpm create quasar@latest
# then pick the AppExtension option
```

It will prompt you about your specific needs. Do you need an install script, an uninstall script, will you be prompting the user with some questions? Pick only what you will be using. You can manually add these later if you decide otherwise.

For the sake of this documentation page, let's assume we answered with `my-ext` to the App Extension `ext-id` question (regarding the prompts above). Remember that the folder name for the App Extension source folder can be different from the actual `ext-id`. At the end, we will publish our new npm package (`quasar-app-extension-my-ext`) from the `/ae` folder.

Based on your responses, a folder for your App Extension will be created with the following structure:

- **.**
  _PNPM workspace with /ae and /playground_
  - **ae**
    _The App Extension that you will publish_
    - **package.json**
    - **src**
      - **templates/**
        _optional folder for spawning files_
      - **runtime/**
        _optional folder with UI stuff_
      - **index.js**
        _(or .ts) Described in Index API_
      - **install.js**
        _(or .ts) Described in Install API_
      - **prompts.js**
        _(or .ts) Described in Prompts API_
      - **uninstall.js**
        _(or .ts) Described in Uninstall API_
  - **playground/**
    _A @quasar/app-vite project folder to test/develop with_

## App Extension Scripts description

Except for `/ae/src/index.js|ts`, all the other files are optional. You can manually add or remove them at any point in time.

| Name | Description |
| --- | --- |
| `/ae/src/prompts.js` | Handles the prompts when installing the App Extension |
| `/ae/src/install.js` | Extends the installation procedure of the App Extension |
| `/ae/src/index.js` | Is executed on `quasar dev` and `quasar build` |
| `/ae/src/uninstall.js` | Extends the uninstallation procedure of the App Extension |

## Handling package dependencies

If your App Extension needs packages at runtime, install them in the `/ae` folder as regular dependencies. Do not install packages supplied by Quasar CLI, such as `quasar`, `@quasar/extras`, or `@quasar/app-vite`. Use `api.compatibleWith()` in your install and index scripts to declare the versions that your extension supports; see the [Install API](install-api.md) and [Index API](index-api.md).

For example, if you are creating a UI component that depends on a package named `my-table`, run `pnpm add my-table` from the `/ae` folder.

> [!WARNING]
> Never install packages that are supplied by Quasar CLI as dependencies of your extension. Use `api.compatibleWith()` to require a compatible version without installing a second copy.

> [!IMPORTANT]
> If your App Extension's own code imports from the `quasar` package (a Quasar Plugin like Notify, a utility, etc.), also read [Injecting Quasar Plugin](../common-formulas-and-patterns/inject-quasar-plugin.md#using-the-plugin-from-your-own-code), otherwise your code can end up linked against a second copy of Quasar.

## Developing

### Commands to use

Notice `/package.json` scripts that you can use:

Example "Run from root folder":

```bash
# Lint & format
# (if you selected oxlint + oxfmt option)
pnpm run lint
pnpm run lint:check

# Use playground to develop;
# Helps you test the Index script as well
pnpm run dev
pnpm run dev -m ssr
# ...etc

# Invokes the AE into /playground when needed
# (like when changing the scripts themselves);
# Helps you run the Install & Prompts scripts
pnpm run invoke

# Uninstall & re-install AE;
# Helps you mainly to run the Uninstall script
pnpm run cycle
```

### Install and Prompts scripts

> [!NOTE]
> Learn more about what you can do with the [Prompts API](prompts-api.md) and the [Install API](install-api.md).

You will notice mentions of `invoking` an AE. The invoking procedure, as opposed to the "adding" one, assumes that the App Extension's package is already pnpm/yarn/npm/bun installed into the host app (and so, Quasar CLI skips that step).

Example "End-user commands using Index script":

```bash
quasar ext add <ext-id>
# or:
quasar ext invoke <ext-id>
```

### Uninstall script

> [!NOTE]
> Learn more about what you can do with the [Uninstall API](uninstall-api.md).

You will notice mentions of `uninvoking` an AE. Unlike removing an extension, uninvoking unregisters it from the host app but does not uninstall its package.

Example "End-user commands using Uninstall script":

```bash
quasar ext remove <ext-id>
# or:
quasar ext uninvoke <ext-id>
```

### Index script

The Index script is the heart of your App Extension.

This is where you can tamper with all `quasar.config` file options, extend the Vite configuration, register Quasar CLI commands, start up external services required for developing your app and many more.

Example "End-user commands using Index script":

```bash
quasar dev
quasar build
```

> [!NOTE]
> Learn more about what you can do with the [Index API](index-api.md).

A common use-case of what you can do with your Index script is to extend the host app's Vite config as follows:

Example "/ae/src/index.js (or .ts)":

```js
import { defineIndexScript } from '#q-app'

export default defineIndexScript(api => {
  api.extendViteConf((viteConf, { isClient, isServer }, api) => {
    // similar in use to /quasar.config > build > extendViteConf
  })
})
```

## Publishing

When you finalized your App Extension and you're ready to deploy it, all you need to do is to publish it to the npm repository.

- Make sure to edit `/ae/README.md`.
- Also edit `/ae/package.json` > `peerDependencies` if needed.
- In order to publish the AE, do it from within the `/ae` folder:

```bash
# from /ae folder ONLY:
pnpm login
pnpm publish
```

> [!IMPORTANT]
> It's important to remember to NOT strip out the `quasar-app-extension-` prefix from the `name` property of your extension's `/ae/package.json`, otherwise Quasar CLI will not recognize it.
