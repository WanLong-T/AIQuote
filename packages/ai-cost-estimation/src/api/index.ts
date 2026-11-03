import type { ApiResponse, PaginatedData, PaginationParams } from '@aiquote/shared';

export interface EstimateListQuery extends Partial<PaginationParams> {
  keyword?: string;
  status?: '草稿' | '测算中' | '已完成';
}

export interface EstimateSummary {
  id: string;
  name: string;
  projectName: string;
  totalCost: number;
  status: '草稿' | '测算中' | '已完成';
  updatedAt: string;
}

export interface EstimateDetail extends EstimateSummary {
  assumptions: string[];
  costItems: Array<{ label: string; amount: number }>;
}

export interface EstimateCalculationInput {
  projectName: string;
  area: number;
  unitCost: number;
  contingencyRate: number;
}

export interface EstimateCalculationResult {
  totalCost: number;
  breakdown: Array<{ label: string; amount: number }>;
}

// TODO(api): Replace local fixtures with the AI cost estimation HTTP endpoint.
export async function listEstimates(
  query: EstimateListQuery = {},
): Promise<ApiResponse<PaginatedData<EstimateSummary>>> {
  await Promise.resolve();
  const page = query.page ?? 1;
  const pageSize = query.pageSize ?? 20;

  return {
    success: true,
    data: {
      page,
      pageSize,
      total: 2,
      items: [
        {
          id: 'estimate-001',
          name: '智能园区成本测算',
          projectName: '华东区域智能园区项目',
          totalCost: 128000000,
          status: '已完成',
          updatedAt: '2026-11-01T10:00:00+08:00',
        },
        {
          id: 'estimate-002',
          name: '绿色基建快速测算',
          projectName: '华南区域绿色基建项目',
          totalCost: 96000000,
          status: '测算中',
          updatedAt: '2026-11-02T09:30:00+08:00',
        },
      ],
    },
  };
}

// TODO(api): Replace local fixture lookup with an estimate detail HTTP endpoint.
export async function getEstimateDetail(estimateId: string): Promise<ApiResponse<EstimateDetail>> {
  await Promise.resolve();
  return {
    success: true,
    data: {
      id: estimateId,
      name: '智能园区成本测算',
      projectName: '华东区域智能园区项目',
      totalCost: 128000000,
      status: '已完成',
      updatedAt: '2026-11-01T10:00:00+08:00',
      assumptions: ['按示例工程量估算', '材料价格采用本地假设值'],
      costItems: [
        { label: '土建工程', amount: 64000000 },
        { label: '机电工程', amount: 42000000 },
        { label: '其他费用', amount: 22000000 },
      ],
    },
  };
}

// TODO(api): Replace local calculation with the backend estimation service.
export async function calculateEstimate(
  input: EstimateCalculationInput,
): Promise<ApiResponse<EstimateCalculationResult>> {
  await Promise.resolve();
  const baseCost = input.area * input.unitCost;
  const contingency = baseCost * input.contingencyRate;

  return {
    success: true,
    data: {
      totalCost: baseCost + contingency,
      breakdown: [
        { label: '基础成本', amount: baseCost },
        { label: '预备费', amount: contingency },
      ],
    },
  };
}
