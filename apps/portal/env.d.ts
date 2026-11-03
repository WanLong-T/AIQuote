interface ImportMetaEnv {
  readonly VITE_DEV_PORT?: string;
  readonly VITE_NATIONAL_PROJECT_MAP_URL?: string;
  readonly VITE_AI_COST_ESTIMATION_URL?: string;
  readonly VITE_BID_TEMPLATE_ANALYSIS_URL?: string;
  readonly VITE_BID_RESULT_ANALYSIS_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
