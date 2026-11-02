import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';

const sourceFile =
  process.argv[2] ?? 'D:/工程投标智能决策系统/模块1/项目数据爬虫/数据/clean/projects.json';
const outputFile = resolve(process.cwd(), 'public/data/projects.json');

const cityCenters = {
  南京市: [118.796877, 32.060255],
  无锡市: [120.31191, 31.49117],
  徐州市: [117.284124, 34.205768],
  常州市: [119.973987, 31.810689],
  苏州市: [120.585294, 31.299758],
  南通市: [120.894522, 31.981269],
  连云港市: [119.221487, 34.596653],
  淮安市: [119.015285, 33.610353],
  盐城市: [120.163561, 33.347382],
  扬州市: [119.412834, 32.394404],
  镇江市: [119.425836, 32.187849],
  泰州市: [119.923116, 32.455778],
  宿迁市: [118.275162, 33.963008],
};

function toYi(value) {
  return typeof value === 'number' && Number.isFinite(value)
    ? value / 100_000_000
    : null;
}

function normalizeDateTime(value) {
  return typeof value === 'string' ? value.trim() : '';
}

const verifiedOwnerCorrections = new Map([
  ['江苏川?实业集团有限公司', '江苏川昇实业集团有限公司'],
  ['南通海?开发建设有限公司', '南通海璟开发建设有限公司'],
]);

function normalizeOwner(value) {
  if (typeof value !== 'string') return '';
  const owner = value.split(/\s*项目建设采用\s*[:：]/, 1)[0].trim().replace(/[ 、,，]+$/u, '');
  return verifiedOwnerCorrections.get(owner) ?? owner;
}

function daysUntil(value) {
  if (!value) return -1;
  const target = new Date(value.replace(' ', 'T'));
  if (Number.isNaN(target.getTime())) return -1;
  return Math.ceil((target.getTime() - Date.now()) / 86_400_000);
}

function calculateRating({ amount, days, owner, category, city }) {
  let score = 0;

  if (amount >= 1) score += 40;
  else if (amount >= 0.3) score += 32;
  else if (amount >= 0.1) score += 24;
  else if (amount > 0) score += 14;

  if (days >= 3 && days <= 14) score += 30;
  else if (days >= 15 && days <= 30) score += 22;
  else if (days >= 0 && days < 3) score += 12;
  else if (days > 30) score += 10;

  if (owner) score += 10;
  if (category) score += 10;
  if (city) score += 10;

  if (score >= 76) return 'A';
  if (score >= 61) return 'B';
  if (score >= 41) return 'C';
  return 'D';
}

const raw = JSON.parse(await readFile(sourceFile, 'utf8'));
if (!Array.isArray(raw)) throw new Error('爬虫 projects.json 顶层必须是数组');

const data = raw.map((item, index) => {
  const city = item.city ?? '';
  const [lng, lat] = cityCenters[city] ?? [119.0, 33.0];
  const controlPrice = toYi(item.control_price);
  const estimatedContractAmount = toYi(item.estimated_contract_amount);
  const provisionalSum = toYi(item.provisional_sum);
  const openDate = normalizeDateTime(item.open_bid_time);
  const deadline = normalizeDateTime(item.bid_deadline);
  const countdownTarget = openDate || deadline;
  const days = daysUntil(countdownTarget);
  const amount = controlPrice ?? estimatedContractAmount ?? 0;
  const owner = normalizeOwner(item.owner_name || item.tenderer_name || '');
  const category = item.project_type ?? '';

  return {
    id: Number(item.source_row_id) || index + 1,
    name: item.project_name ?? '',
    category,
    province: item.province ?? '',
    city,
    district: item.district ?? '',
    lng,
    lat,
    owner,
    announcementDate: normalizeDateTime(item.publish_time),
    openDate,
    deadline,
    days,
    controlPrice,
    estimatedContractAmount,
    provisionalSum,
    amount,
    rating: calculateRating({ amount, days, owner, category, city }),
    status: '',
    ownerPerson: '',
    competitors: '',
    log: '',
    sourceName: item.source_platform || '江苏省建设工程招标网',
    sourceUrl: item.source_url ?? '',
    projectCode: item.project_code ?? '',
    sectionCode: item.section_code ?? '',
  };
});

const payload = {
  source: '江苏省建设工程招标网',
  sourceUrl: 'http://www.jszb.com.cn/jszb/YW_info/ZhaoBiaoGG/MoreInfo_ZBGG.aspx',
  fetchedAt: new Date().toISOString(),
  notice:
    '公开公告未披露的字段保持为空；ABCD为系统依据金额、截止紧迫度和信息完整度生成的初评，跟踪阶段、责任人及竞争对手等待企业录入。',
  data,
};

await mkdir(dirname(outputFile), { recursive: true });
await writeFile(outputFile, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
console.log(`已同步 ${data.length} 条项目到 ${outputFile}`);
