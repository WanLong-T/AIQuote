interface ImportMetaEnv {
  readonly VITE_DEV_PORT?: string;
  readonly VITE_BID_TEMPLATE_ANALYSIS_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
