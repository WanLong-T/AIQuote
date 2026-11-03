import type { ApiResponse, PaginatedData, PaginationParams } from '@aiquote/shared';

export interface ProjectMapQuery extends Partial<PaginationParams> {
  keyword?: string;
  province?: string;
  status?: string;
}

export interface ProjectMapPoint {
  id: string;
  name: string;
  province: string;
  city: string;
  amount: number;
  status: '招标中' | '已中标' | '已完成';
  longitude: number;
  latitude: number;
}

export interface ProjectDetail extends ProjectMapPoint {
  owner: string;
  deadline: string;
  description: string;
}

// TODO(api): Replace local fixtures with the national project map HTTP endpoint.
export async function listProjectMapPoints(
  query: ProjectMapQuery = {},
): Promise<ApiResponse<PaginatedData<ProjectMapPoint>>> {
  await Promise.resolve();
  const page = query.page ?? 1;
  const pageSize = query.pageSize ?? 20;

  return {
    success: true,
    data: {
      page,
      pageSize,
      total: 3,
      items: [
        {
          id: 'project-001',
          name: '华东区域智能园区项目',
          province: '上海市',
          city: '上海市',
          amount: 128000000,
          status: '招标中',
          longitude: 121.4737,
          latitude: 31.2304,
        },
        {
          id: 'project-002',
          name: '华南区域绿色基建项目',
          province: '广东省',
          city: '广州市',
          amount: 96000000,
          status: '已中标',
          longitude: 113.2644,
          latitude: 23.1291,
        },
        {
          id: 'project-003',
          name: '西部数据中心配套工程',
          province: '四川省',
          city: '成都市',
          amount: 76000000,
          status: '已完成',
          longitude: 104.0665,
          latitude: 30.5728,
        },
      ],
    },
  };
}

// TODO(api): Replace local fixture lookup with a project detail HTTP endpoint.
export async function getProjectDetail(projectId: string): Promise<ApiResponse<ProjectDetail>> {
  await Promise.resolve();
  return {
    success: true,
    data: {
      id: projectId,
      name: '华东区域智能园区项目',
      province: '上海市',
      city: '上海市',
      amount: 128000000,
      status: '招标中',
      longitude: 121.4737,
      latitude: 31.2304,
      owner: '示例建设单位',
      deadline: '2026-12-31',
      description: '用于模块联调的项目详情假数据。',
    },
  };
}
