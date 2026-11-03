export interface PortalModule {
  key: 'map' | 'ai' | 'template' | 'result';
  label: string;
  role: string;
  description: string;
  icon: string;
  url: string;
  route: string;
}

export const portalModules: PortalModule[] = [
  {
    key: 'map',
    label: '全国项目地图',
    role: '发现商机 · 跟踪进度',
    description: '查看全国项目分布、开标预警和项目跟踪情况',
    icon: 'public',
    url: import.meta.env.VITE_NATIONAL_PROJECT_MAP_URL || 'http://localhost:3001',
    route: '/map',
  },
  {
    key: 'ai',
    label: 'AI 成本测算',
    role: '清单解析 · 锁定报价线',
    description: '基于项目数据进行成本分析和智能测算',
    icon: 'calculate',
    url: import.meta.env.VITE_AI_COST_ESTIMATION_URL || 'http://localhost:3002',
    route: '/ai',
  },
  {
    key: 'template',
    label: '投标模板分析',
    role: '智能识别 · 模拟评审',
    description: '解析招标文件并生成投标方案分析',
    icon: 'description',
    url: import.meta.env.VITE_BID_TEMPLATE_ANALYSIS_URL || 'http://localhost:3003',
    route: '/template',
  },
  {
    key: 'result',
    label: '投标结果分析',
    role: '中标复盘 · 经验沉淀',
    description: '复盘投标结果，分析竞争态势和中标情况',
    icon: 'analytics',
    url: import.meta.env.VITE_BID_RESULT_ANALYSIS_URL || 'http://localhost:3004',
    route: '/result',
  },
];

export function moduleEntryUrl(module: PortalModule): string {
  return module.url.replace(/\/$/, '') + '/#/';
}
