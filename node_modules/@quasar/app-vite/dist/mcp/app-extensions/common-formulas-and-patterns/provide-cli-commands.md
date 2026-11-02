---
title: Providing CLI Command(s)
related:
  - title: App Extension Index API
    path: ../development-guide/index-api.md
---
One powerful feature of Quasar CLI App Extensions is to provide commands that can be run by your users just as the Quasar CLI commands.

## Usage

Let's see how you can register a command that will become available as `quasar run <ext-id> <cmd> [...args]`. We will be editing our [Index script](../development-guide/index-api.md):

Example "/ae/src/index.js (or .ts)":

```js
import { defineIndexScript } from '#q-app'

export default defineIndexScript(api => {
  /**
   * @param {string} commandName
   * @param {function} fn
   *   (processArgv: string[]) => ?Promise
   */
  api.registerCommand('start', processArgv => {
    // do something here
    // this registers the "start" command
    // and this handler is executed when running
    // quasar run <ext-id> start
  })
})
```

Example with defining and parsing arguments:

Example "/ae/src/index.js (or .ts)":

```js
import { defineIndexScript } from '#q-app'
import { parseArgs } from 'node:util'

export default defineIndexScript(api => {
  /**
   * User can run in the host app:
   *   quasar run <ext-id> fun --name Gigi -d
   */
  api.registerCommand('fun', () => {
    try {
      const { values, positionals } = parseArgs({
        options: {
          name: { type: 'string', short: 'n' },
          debug: { type: 'boolean' }
        },
        strict: true,
        allowPositionals: true
      })

      console.log(values, positionals)
    } catch (err) {
      console.error(err.message)
    }
  })
})
```
