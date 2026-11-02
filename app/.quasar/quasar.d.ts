/* oxlint-disable */
/* eslint-disable */
/// <reference types="@quasar/app-vite" />
/// <reference types="@quasar/app-vite/client" />

// https://quasar.dev/quasar-cli-vite/handling-import-meta-env#type-inference

// Automatically generated from raw build.define
declare const __VUE_PROD_DEVTOOLS__: boolean;
declare const __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: boolean;
declare const __VUE_I18N_FULL_INSTALL__: boolean;
declare const __VUE_I18N_LEGACY_API__: boolean;
declare const __VUE_I18N_PROD_DEVTOOLS__: boolean;
declare const __INTLIFY_PROD_DEVTOOLS__: boolean;
declare const __VUE_OPTIONS_API__: boolean;

// Automatically generated from process.env & dotenv files & build.define & build.defineEnv;
// Backend-only are not available in client code, so they are marked as optional
interface ImportMetaEnv {
  readonly QCLI_AMAP_KEY: string;
  readonly QCLI_AMAP_SECURITY_CODE: string;
  readonly QCLI_PROJECT_API_URL: string;
  readonly ALLUSERSPROFILE?: string;
  readonly APPDATA?: string;
  readonly BIDDING_DB_PASSWORD?: string;
  readonly CODEX_APP_TOOLS_PIPE_PATH?: string;
  readonly CODEX_CI?: number;
  readonly CODEX_INTERNAL_ORIGINATOR_OVERRIDE?: string;
  readonly CODEX_MCP_NODE_PATH?: string;
  readonly CODEX_PERMISSION_PROFILE?: string;
  readonly CODEX_SAGE_BACKFILL_TRACKER_TAB_REUSE?: number;
  readonly CODEX_SESSION_ID?: string;
  readonly CODEX_THREAD_ID?: string;
  readonly CODEX_VERSION?: string;
  readonly COLOR?: number;
  readonly COLORTERM?: string;
  readonly CommonProgramFiles?: string;
  readonly CommonProgramW6432?: string;
  readonly COMPUTERNAME?: string;
  readonly ComSpec?: string;
  readonly DriverData?: string;
  readonly EDITOR?: string;
  readonly GH_PAGER?: string;
  readonly GIT_PAGER?: string;
  readonly GLODON_COMMON_APPDATA?: string;
  readonly GLODON_COMMON_DESKTOP?: string;
  readonly GLODON_COMMON_DOCUMENT?: string;
  readonly GLODON_COMMON_FILES_32?: string;
  readonly GLODON_COMMON_FILES_64?: string;
  readonly GLODON_PROGRAM_FILES_32?: string;
  readonly GLODON_PROGRAM_FILES_64?: string;
  readonly GLODON_SYSTEM_32?: string;
  readonly GLODON_SYSTEM_64?: string;
  readonly GLODON_SYSTEM_DRIVE?: string;
  readonly GLODON_WINDOWS_DIR?: string;
  readonly HOME?: string;
  readonly HOMEDRIVE?: string;
  readonly HOMEPATH?: string;
  readonly INIT_CWD?: string;
  readonly JAVA_HOME?: string;
  readonly LANG?: string;
  readonly LC_ALL?: string;
  readonly LC_CTYPE?: string;
  readonly LOCALAPPDATA?: string;
  readonly LOGONSERVER?: string;
  readonly LOG_FORMAT?: string;
  readonly NODE?: string;
  readonly NODE_ENV?: string;
  readonly NODE_REPL_TRUSTED_BROWSER_CLIENT_SHA256S?: string;
  readonly NO_COLOR?: number;
  readonly npm_command?: string;
  readonly npm_config_cache?: string;
  readonly npm_config_globalconfig?: string;
  readonly npm_config_global_prefix?: string;
  readonly npm_config_init_module?: string;
  readonly npm_config_local_prefix?: string;
  readonly npm_config_node_gyp?: string;
  readonly npm_config_noproxy?: string;
  readonly npm_config_npm_version?: string;
  readonly npm_config_prefix?: string;
  readonly npm_config_userconfig?: string;
  readonly npm_config_user_agent?: string;
  readonly npm_execpath?: string;
  readonly npm_lifecycle_event?: string;
  readonly npm_lifecycle_script?: string;
  readonly npm_node_execpath?: string;
  readonly npm_package_engines_node?: string;
  readonly npm_package_json?: string;
  readonly npm_package_name?: string;
  readonly npm_package_version?: string;
  readonly NUMBER_OF_PROCESSORS?: number;
  readonly OneDrive?: string;
  readonly OS?: string;
  readonly PAGER?: string;
  readonly Path?: string;
  readonly PATHEXT?: string;
  readonly PROCESSOR_ARCHITECTURE?: string;
  readonly PROCESSOR_IDENTIFIER?: string;
  readonly PROCESSOR_LEVEL?: number;
  readonly PROCESSOR_REVISION?: string;
  readonly ProgramData?: string;
  readonly ProgramFiles?: string;
  readonly ProgramW6432?: string;
  readonly PROMPT?: string;
  readonly PSModulePath?: string;
  readonly PUBLIC?: string;
  readonly PyCharm?: string;
  readonly QtMsBuild?: string;
  readonly RUST_LOG?: string;
  readonly SystemDrive?: string;
  readonly SystemRoot?: string;
  readonly TEMP?: string;
  readonly TERM?: string;
  readonly TMP?: string;
  readonly USERDOMAIN?: string;
  readonly USERDOMAIN_ROAMINGPROFILE?: string;
  readonly USERNAME?: string;
  readonly USERPROFILE?: string;
  readonly windir?: string;
  readonly ZES_ENABLE_SYSMAN?: number;
}
