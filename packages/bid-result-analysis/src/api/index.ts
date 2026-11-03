import type { ApiResponse, PaginatedData, PaginationParams } from '@aiquote/shared';

export interface BidResultQuery extends Partial<PaginationParams> {
  keyword?: string;
  region?: string;
}

export interface BidResultSummary {
  id: string;
  projectName: string;
  winningCompany: string;
  winningAmount: number;
  region: string;
  announcedAt: string;
}

export interface BidResultDetail extends BidResultSummary {
  bidderCount: number;
  priceRanking: Array<{ company: string; amount: number; rank: number }>;
  notes: string[];
}

// TODO(api): Replace local fixtures with the bid result analysis HTTP endpoint.
export async function listBidResults(
  query: BidResultQuery = {},
): Promise<ApiResponse<PaginatedData<BidResultSummary>>> {
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
          id: 'bid-result-001',
          projectName: '华东区域智能园区项目',
          winningCompany: '示例建设集团有限公司',
          winningAmount: 126500000,
          region: '华东',
          announcedAt: '2026-10-28',
        },
        {
          id: 'bid-result-002',
          projectName: '华南区域绿色基建项目',
          winningCompany: '示例工程股份有限公司',
          winningAmount: 94200000,
          region: '华南',
          announcedAt: '2026-10-25',
        },
      ],
    },
  };
}

// TODO(api): Replace local fixture lookup with a bid result detail HTTP endpoint.
export async function getBidResult(resultId: string): Promise<ApiResponse<BidResultDetail>> {
  await Promise.resolve();
  return {
    success: true,
    data: {
      id: resultId,
      projectName: '华东区域智能园区项目',
      winningCompany: '示例建设集团有限公司',
      winningAmount: 126500000,
      region: '华东',
      announcedAt: '2026-10-28',
      bidderCount: 8,
      priceRanking: [
        { company: '示例建设集团有限公司', amount: 126500000, rank: 1 },
        { company: '示例工程股份有限公司', amount: 127900000, rank: 2 },
      ],
      notes: ['用于结果分析页面联调的本地假数据。'],
    },
  };
}
