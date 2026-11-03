interface ImportMetaEnv {
  readonly VITE_DEV_PORT?: string;
  readonly VITE_AI_COST_ESTIMATION_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
