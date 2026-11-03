---
title: Lint and Format Code
---
## Oxlint + Oxfmt

[Oxlint](https://oxc.rs/docs/guide/usage/linter.html) and [Oxfmt](https://oxc.rs/docs/guide/usage/formatter.html) are next-generation, Rust-based tools from the [Oxc](https://oxc.rs) (JavaScript Oxidation Compiler) ecosystem, designed to replace traditional JavaScript/TypeScript linters and formatters with a heavy emphasis on speed and developer experience.

### Installation

Example "Javascript projects":

```bash
pnpm add -D oxlint oxfmt
```

Example "TypeScript projects":

```bash
pnpm add -D oxlint oxfmt oxlint-tsgolint typescript vue-tsc
```

### Package.json scripts

Example "/package.json":

```json
"scripts": {
  "lint": "oxfmt && oxlint --fix",
  "lint:check": "oxfmt --check && oxlint",
  "typecheck": "vue-tsc --noEmit"
}
```

### Configuration files

Create the following files:

Example "oxlint configuration":

```ts
import { defineConfig } from 'oxlint'

export default defineConfig({
  $schema: './node_modules/oxlint/configuration_schema.json',

  ignorePatterns: [
    '**/node_modules/',
    'dist/',
    'quasar.config.*.temporary.compiled*',
    '.quasar/',
    'src-cordova/',
    'src-capacitor/'
  ],

  options: {
    typeAware: true,
    typeCheck: true,
    maxWarnings: 10
  },

  plugins: ['typescript', 'vue', 'import', 'eslint', 'promise', 'unicorn'],

  categories: {
    correctness: 'error'
    // style: 'error',
    // pedantic: 'warn',
    // suspicious: 'error',
    // perf: 'error',
    // restriction: 'error'
  },

  rules: {},

  env: {
    builtin: true
  }
})
```

Example "oxfmt configuration":

```ts
import { defineConfig } from 'oxfmt'

export default defineConfig({
  $schema: './node_modules/oxfmt/configuration_schema.json',

  ignorePatterns: [
    '**/node_modules/',
    'dist/',
    'quasar.config.*.temporary.compiled*',
    '.quasar/',
    'src-cordova/',
    'src-capacitor/'
  ],

  printWidth: 80,
  arrowParens: 'avoid',
  bracketSpacing: true,
  bracketSameLine: false,
  htmlWhitespaceSensitivity: 'strict',
  semi: true,
  singleQuote: false,
  quoteProps: 'as-needed',
  trailingComma: 'none',
  useTabs: false,
  vueIndentScriptAndStyle: false
})
```

### VSCode configuration

Example "/.vscode/settings.json":

```json
{
  "editor.codeActionsOnSave": {
    "source.fixAll.oxc": "always"
  },
  "oxc.fmt.configPath": "oxfmt.config.ts",
  "editor.defaultFormatter": "oxc.oxc-vscode",
  "editor.formatOnSave": true
}
```

Play nice with other devs using your project and recommend them to install the appropriate extension. And don't forget to install it yourself too:

Example "/.vscode/extensions.json":

```json
{
  "recommendations": ["oxc.oxc-vscode"]
}
```

## ESLint + Prettier

Having a code linter (like [ESLint v9+](https://eslint.org/)) in place is highly recommended and ensures your code looks legible. It also helps you capture some errors before even running the code.

When you scaffold a Quasar project folder it will ask you if you want ESLint (also prettier as a code formatter).

### Javascript projects

#### Needed dependencies

```bash
pnpm add -D @eslint/js eslint@10 eslint-plugin-vue vue-eslint-parser globals vite-plugin-checker
```

If you want `prettier` as a code formatter, then install these too:

```bash
pnpm add -D prettier@3 @vue/eslint-config-prettier
```

#### The quasar.config file settings

Example "/quasar.config file":

```js
build: {
  vitePlugins: [
    [
      'vite-plugin-checker',
      {
        eslint: {
          lintCommand:
            'eslint -c ./eslint.config.js "./src*/**/*.{js,mjs,cjs,vue}"',
          useFlatConfig: true
        }
      },
      { server: false }
    ]
  ]
}
```

#### The ESLint configuration

Example "/eslint.config.js":

```js
import js from '@eslint/js'
import globals from 'globals'
import pluginVue from 'eslint-plugin-vue'
import pluginQuasar from '@quasar/app-vite/eslint'

// the following is optional, if you want prettier too:
import prettierSkipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default [
  {
    /**
     * Ignore the following files.
     * Please note that pluginQuasar.configs.recommended() already ignores
     * the "node_modules" folder for you (and all other Quasar project
     * relevant folders and files).
     *
     * ESLint requires "ignores" key to be the only one in this object
     */
    // ignores: []
  },

  ...pluginQuasar.configs.recommended(),
  js.configs.recommended,

  /**
   * https://eslint.vuejs.org
   *
   * pluginVue.configs.base
   *   -> Settings and rules to enable correct ESLint parsing.
   * pluginVue.configs[ 'flat/essential']
   *   -> base, plus rules to prevent errors or unintended behavior.
   * pluginVue.configs["flat/strongly-recommended"]
   *   -> Above, plus rules to considerably improve code readability and/or dev experience.
   * pluginVue.configs["flat/recommended"]
   *   -> Above, plus rules to enforce subjective community defaults to ensure consistency.
   */
  ...pluginVue.configs['flat/essential'],

  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',

      globals: {
        ...globals.browser,
        ...globals.node, // SSR, SSG, Electron, config files
        ga: 'readonly', // Google Analytics
        cordova: 'readonly',
        Capacitor: 'readonly',
        chrome: 'readonly', // BEX related
        browser: 'readonly' // BEX related
      }
    },

    // add your custom rules here
    rules: {
      'prefer-promise-reject-errors': 'off',
      // slots use the "#" shorthand everywhere, as in the Quasar docs
      'vue/v-slot-style': ['warn', 'shorthand'],

      // allow debugger during development only
      'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off'
    }
  },

  {
    files: ['src-pwa/sw/**/*.js'],
    languageOptions: {
      globals: {
        ...globals.serviceworker
      }
    }
  },

  prettierSkipFormatting // optional, if you want prettier
]
```

### TypeScript projects

#### Dependencies

```bash
pnpm add -D vue-tsc @vue/eslint-config-typescript @eslint/js eslint@10 eslint-plugin-vue globals vite-plugin-checker
```

If you want `prettier` as a code formatter, then install these too:

```bash
pnpm add -D prettier@3 @vue/eslint-config-prettier
```

#### The quasar.config settings

Example "/quasar.config file":

```js
build: {
  vitePlugins: [
    [
      'vite-plugin-checker',
      {
        vueTsc: true,
        eslint: {
          lintCommand:
            'eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"',
          useFlatConfig: true
        }
      },
      { server: false }
    ]
  ]
}
```

#### ESLint configuration file

Example "/eslint.config.js":

```js
import js from '@eslint/js'
import globals from 'globals'
import pluginVue from 'eslint-plugin-vue'
import pluginQuasar from '@quasar/app-vite/eslint'
import {
  defineConfigWithVueTs,
  vueTsConfigs
} from '@vue/eslint-config-typescript'

// the following is optional, if you want prettier too:
import prettierSkipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default defineConfigWithVueTs(
  {
    /**
     * Ignore the following files.
     * Please note that pluginQuasar.configs.recommended() already ignores
     * the "node_modules" folder for you (and all other Quasar project
     * relevant folders and files).
     *
     * ESLint requires "ignores" key to be the only one in this object
     */
    // ignores: []
  },

  pluginQuasar.configs.recommended(),
  js.configs.recommended,

  /**
   * https://eslint.vuejs.org
   *
   * pluginVue.configs.base
   *   -> Settings and rules to enable correct ESLint parsing.
   * pluginVue.configs[ 'flat/essential']
   *   -> base, plus rules to prevent errors or unintended behavior.
   * pluginVue.configs["flat/strongly-recommended"]
   *   -> Above, plus rules to considerably improve code readability and/or dev experience.
   * pluginVue.configs["flat/recommended"]
   *   -> Above, plus rules to enforce subjective community defaults to ensure consistency.
   */
  pluginVue.configs['flat/essential'],

  {
    files: ['**/*.ts', '**/*.vue'],
    rules: {
      '@typescript-eslint/consistent-type-imports': [
        'error',
        { prefer: 'type-imports' }
      ]
    }
  },
  vueTsConfigs.recommendedTypeChecked,

  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',

      globals: {
        ...globals.browser,
        ...globals.node, // SSR, SSG, Electron, config files
        process: 'readonly', // process.env.*
        ga: 'readonly', // Google Analytics
        cordova: 'readonly',
        Capacitor: 'readonly',
        chrome: 'readonly', // BEX related
        browser: 'readonly' // BEX related
      }
    },

    // add your custom rules here
    rules: {
      'prefer-promise-reject-errors': 'off',
      // slots use the "#" shorthand everywhere, as in the Quasar docs
      'vue/v-slot-style': ['warn', 'shorthand'],

      // allow debugger during development only
      'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off'
    }
  },

  {
    files: ['src-pwa/sw/**/*.ts'],
    languageOptions: {
      globals: {
        ...globals.serviceworker
      }
    }
  },

  prettierSkipFormatting // optional, if you want prettier
)
```

### Performance and ignoring files

> [!WARNING]
> Please be sure to ignore unused files to increase performance. If you lint unused files/folders the UX will degrade significantly.

You can ignore files by editing your `/eslint.config.js` file:

Example "/eslint.config.js":

```js
export default [
  {
    /**
     * Ignore the following files.
     * Please note that pluginQuasar.configs.recommended() already ignores
     * the "node_modules" folder for you (and all other Quasar project
     * relevant folders and files).
     *
     * ESLint requires "ignores" key to be the only one in this object
     */
    ignores: [] // <<<---- here!
  },
```

Notice that `pluginQuasar.configs.recommended()` from a few sections above will add the following to your ESLint `ignores` setting (no need to add them yourself too!):

```js
// not an exhaustive list auto-added to "ignores"
;[
  'dist/*',
  'src-capacitor/*',
  'src-cordova/*',
  '.quasar/*',
  'quasar.config.*.temporary.compiled*'
]
```

### Lint Rules

The linting rules can be removed, changed, or added. Notice some things:

- Some rules are standard ESLint ones. Example: 'brace-style'.
- Some rules are for eslint-plugin-vue. Example: 'vue/max-attributes-per-line'.

You can add/remove/change rules by first visiting [https://eslint.org/docs/rules/](https://eslint.org/docs/rules/) or [https://eslint.vuejs.org/rules](https://eslint.vuejs.org/rules).
