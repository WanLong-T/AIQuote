import type { ApiResponse, PaginatedData, PaginationParams } from '@aiquote/shared';

export interface TemplateAnalysisQuery extends Partial<PaginationParams> {
  keyword?: string;
  status?: '待分析' | '分析中' | '已完成';
}

export interface TemplateAnalysisSummary {
  id: string;
  fileName: string;
  projectName: string;
  status: '待分析' | '分析中' | '已完成';
  score: number | null;
  updatedAt: string;
}

export interface TemplateAnalysisDetail extends TemplateAnalysisSummary {
  extractedFields: Array<{ label: string; value: string }>; 
  riskItems: Array<{ level: '高' | '中' | '低'; message: string }>;
}

// TODO(api): Replace local fixtures with the bid template analysis HTTP endpoint.
export async function listTemplateAnalyses(
  query: TemplateAnalysisQuery = {},
): Promise<ApiResponse<PaginatedData<TemplateAnalysisSummary>>> {
  await Promise.resolve();
  const page = query.page ?? 1;
  const pageSize = query.pageSize ?? 20;

  return {
    success: true,
    data: {
      page,
      pageSize,
      total: 1,
      items: [
        {
          id: 'template-analysis-001',
          fileName: '智能园区招标文件.pdf',
          projectName: '华东区域智能园区项目',
          status: '已完成',
          score: 86,
          updatedAt: '2026-11-02T08:30:00+08:00',
        },
      ],
    },
  };
}

// TODO(api): Replace local fixture lookup with an analysis detail HTTP endpoint.
export async function getTemplateAnalysis(
  analysisId: string,
): Promise<ApiResponse<TemplateAnalysisDetail>> {
  await Promise.resolve();
  return {
    success: true,
    data: {
      id: analysisId,
      fileName: '智能园区招标文件.pdf',
      projectName: '华东区域智能园区项目',
      status: '已完成',
      score: 86,
      updatedAt: '2026-11-02T08:30:00+08:00',
      extractedFields: [
        { label: '项目类型', value: '房建' },
        { label: '计划工期', value: '720 日历天' },
        { label: '投标截止时间', value: '2026-12-20 09:30' },
      ],
      riskItems: [{ level: '中', message: '技术标评分细则需要逐项响应。' }],
    },
  };
}

// TODO(api): Replace local file analysis with the backend document analysis service.
export async function analyzeTemplate(fileName: string): Promise<ApiResponse<TemplateAnalysisSummary>> {
  await Promise.resolve();
  return {
    success: true,
    data: {
      id: 'template-analysis-draft',
      fileName,
      projectName: '待提取项目名称',
      status: '分析中',
      score: null,
      updatedAt: new Date().toISOString(),
    },
  };
}
