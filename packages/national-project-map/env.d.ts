interface ImportMetaEnv {
  readonly VITE_DEV_PORT?: string;
  readonly VITE_NATIONAL_PROJECT_MAP_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
