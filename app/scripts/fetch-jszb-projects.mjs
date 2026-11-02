import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';

const LIST_URL = 'http://www.jszb.com.cn/jszb/YW_info/ZhaoBiaoGG/MoreInfo_ZBGG.aspx';
const DETAIL_BASE = 'http://www.jszb.com.cn/jszb/YW_info/ZhaoBiaoGG/';
const OUTPUT_FILE = resolve(process.cwd(), 'public/data/projects.json');
const SOURCE_NAME = '江苏省建设工程招标网';
const REQUEST_DELAY_MS = 800;
const MAX_PROJECTS = 20;

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

const districtToCity = {
  江宁: '南京市',
  浦口: '南京市',
  六合: '南京市',
  溧水: '南京市',
  高淳: '南京市',
  江阴: '无锡市',
  宜兴: '无锡市',
  新吴: '无锡市',
  惠山: '无锡市',
  锡山: '无锡市',
  铜山: '徐州市',
  丰县: '徐州市',
  沛县: '徐州市',
  睢宁: '徐州市',
  邳州: '徐州市',
  新沂: '徐州市',
  武进: '常州市',
  金坛: '常州市',
  溧阳: '常州市',
  吴江: '苏州市',
  昆山: '苏州市',
  太仓: '苏州市',
  常熟: '苏州市',
  张家港: '苏州市',
  苏州工业园区: '苏州市',
  海安: '南通市',
  如皋: '南通市',
  如东: '南通市',
  启东: '南通市',
  海门: '南通市',
  通州: '南通市',
  东海: '连云港市',
  灌云: '连云港市',
  灌南: '连云港市',
  赣榆: '连云港市',
  涟水: '淮安市',
  盱眙: '淮安市',
  金湖: '淮安市',
  洪泽: '淮安市',
  清江浦: '淮安市',
  东台: '盐城市',
  大丰: '盐城市',
  建湖: '盐城市',
  射阳: '盐城市',
  阜宁: '盐城市',
  滨海: '盐城市',
  响水: '盐城市',
  江都: '扬州市',
  高邮: '扬州市',
  仪征: '扬州市',
  宝应: '扬州市',
  丹阳: '镇江市',
  句容: '镇江市',
  扬中: '镇江市',
  丹徒: '镇江市',
  靖江: '泰州市',
  泰兴: '泰州市',
  兴化: '泰州市',
  姜堰: '泰州市',
  沭阳: '宿迁市',
  泗阳: '宿迁市',
  泗洪: '宿迁市',
};

function sleep(ms) {
  return new Promise((resolvePromise) => setTimeout(resolvePromise, ms));
}

function decodeHtml(value) {
  return value
    .replace(/&nbsp;|&#160;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)));
}

function htmlToText(html) {
  let text = decodeHtml(
    html
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/p>|<\/tr>|<\/div>/gi, '\n')
      .replace(/<[^>]+>/g, ' '),
  )
    .replace(/[\t\u00a0]+/g, ' ')
    .replace(/ +/g, ' ')
    .replace(/\s*\n\s*/g, '\n')
    .trim();
  for (let index = 0; index < 3; index += 1) {
    text = text.replace(/([\u3400-\u9fff])\s+(?=[\u3400-\u9fff])/g, '$1');
  }
  return text;
}

async function fetchGb2312(url) {
  const response = await fetch(url, {
    headers: {
      Accept: 'text/html,application/xhtml+xml',
      'User-Agent': 'BiddingDecisionSystem/1.0 (low-frequency public notice collector)',
    },
    signal: AbortSignal.timeout(30_000),
  });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${url}`);
  const bytes = await response.arrayBuffer();
  return new TextDecoder('gb18030').decode(bytes);
}

function extractListItems(html) {
  const pattern =
    /window\.open\("(?<url>\.\.\/ZhaoBiaoGG\/ViewReportDetail\.aspx\?[^"\s]+)"[^>]*href="javascript:void\(0\);"[^>]*title="(?<title>[^"]+)"/gi;
  return [...html.matchAll(pattern)].slice(0, MAX_PROJECTS).map((match) => ({
    url: new URL(match.groups.url, DETAIL_BASE).href,
    title: decodeHtml(match.groups.title).trim(),
  }));
}

function pick(text, patterns, fallback = '') {
  for (const pattern of patterns) {
    const match = text.match(pattern);
    const value = match?.[1]?.trim();
    if (value) return value.replace(/[，。；;]+$/, '').trim();
  }
  return fallback;
}

function normalizeDate(value) {
  const match = value.match(/(20\d{2})\s*[年/-]\s*(\d{1,2})\s*[月/-]\s*(\d{1,2})/);
  if (!match) return '';
  return `${match[1]}-${match[2].padStart(2, '0')}-${match[3].padStart(2, '0')}`;
}

function daysUntil(dateText) {
  if (!dateText) return -1;
  const target = new Date(`${dateText}T00:00:00+08:00`);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.ceil((target.getTime() - today.getTime()) / 86_400_000);
}

function inferCity(title, text) {
  const location = pick(text, [/建设地点[：:]?\s*([^\n]{2,80})/]);
  const haystack = `${title} ${location}`;
  for (const city of Object.keys(cityCenters)) {
    if (haystack.includes(city) || haystack.includes(city.replace(/市$/, ''))) return city;
  }
  for (const [district, city] of Object.entries(districtToCity)) {
    if (haystack.includes(district)) return city;
  }
  return '南京市';
}

function normalizeCategory(raw) {
  if (/市政/.test(raw)) return '市政工程';
  if (/水利|水务|防洪|河道/.test(raw)) return '水利工程';
  if (/公路|道路|交通/.test(raw)) return '公路工程';
  if (/房屋|建筑|装饰|安装|工程总承包/.test(raw)) return '房建工程';
  return raw || '其他工程';
}

function scoreRating(amount, days) {
  if (amount >= 3 || (amount >= 1 && days <= 7)) return 'A';
  if (amount >= 1 || days <= 14) return 'B';
  return 'C';
}

function parseDetail(html, item, index) {
  const text = htmlToText(html);
  const name = pick(
    text,
    [/项目名称\s+([^\n]+?)(?=\s+标段编号)/],
    item.title.replace(/^\[[^\]]+\]/, ''),
  );
  const categoryRaw = pick(text, [
    /工程类型\s*[：:]?\s*(市政工程施工|房屋建筑施工|单独装饰装修施工|园林绿化|工程监理|设计|材料设备采购|电力|水利|机电设备|其它)/,
    /工程类型\s+([^\n]+?)(?=\s+申请人|\s+公告信息)/,
  ]);
  const ownerRaw = pick(
    text,
    [
      /招标人为\s*([^，。\n]{2,80})/,
      /招标人\s*[：:]\s*([^，。；;\n]{2,80})/,
      /招标人名称\s+([^\n]+?)(?=\s+代理机构名称)/,
    ],
    '公告未明确',
  );
  const owner =
    ownerRaw.split(/招标代理机构|招标人地址|地址[：:]|联系人[：:]|电话[：:]/)[0].trim() ||
    '公告未明确';
  const announcementDate = normalizeDate(
    pick(text, [/公告开始时间\s+(20\d{2}[^\n]{0,20})/, /公告发布日期\s+(20\d{2}[^\n]{0,20})/]),
  );
  const deadline = normalizeDate(
    pick(text, [
      /投标文件递交的截止时间[^\n]{0,30}?为\s*(20\d{2}[^，。\n]{0,35})/,
      /投标截止时间[）)]?\s*为?\s*(20\d{2}[^，。\n]{0,35})/,
      /公告结束时间\s+(20\d{2}[^\n]{0,20})/,
    ]),
  );
  const openDate = normalizeDate(
    pick(
      text,
      [
        /开标时间[：:]?\s*(20\d{2}[^，。\n]{0,35})/,
        /投标文件开启时间[：:]?\s*(20\d{2}[^，。\n]{0,35})/,
      ],
      deadline,
    ),
  );
  const amountWan = Number(
    pick(
      text,
      [
        /标段估算价（万元）[\s\S]{0,260}?\s(\d+(?:\.\d+)?)\s/,
        /(?:工程)?合同估算价\s*[：:]?\s*(?:约\s*)?(\d+(?:\.\d+)?)\s*万元/,
        /合同估算价\s*[：:]?\s*项目总投资(?:约)?\s*(\d+(?:\.\d+)?)\s*万元/,
        /合同估算价[：:]?\s*(\d+(?:\.\d+)?)\s*万元/,
        /最高投标限价[：:]?\s*(\d+(?:\.\d+)?)\s*万元/,
      ],
      '0',
    ),
  );
  const provisionalWan = Number(pick(text, [/暂列金额[：:]?\s*(\d+(?:\.\d+)?)\s*万元/], '0'));
  const city = inferCity(item.title, text);
  const [lng, lat] = cityCenters[city] ?? cityCenters['南京市'];
  const days = daysUntil(openDate || deadline);
  const amount = amountWan / 10_000;

  return {
    id: Number(new URL(item.url).searchParams.get('RowID')) || index + 1,
    name,
    category: normalizeCategory(categoryRaw),
    province: '江苏省',
    city,
    lng,
    lat,
    owner,
    days,
    amount,
    estimatedContractAmount: amount || null,
    provisionalSum: provisionalWan ? provisionalWan / 10_000 : null,
    rating: scoreRating(amount, days),
    status: '线索阶段',
    ownerPerson: '未分配',
    announcementDate,
    openDate: openDate || deadline,
    deadline,
    competitors: '待企业跟进后补充',
    log: `${announcementDate || '近期'}由${SOURCE_NAME}发布，已自动采集入库。`,
    sourceName: SOURCE_NAME,
    sourceUrl: item.url,
  };
}

async function main() {
  console.log(`正在读取：${LIST_URL}`);
  const listHtml = await fetchGb2312(LIST_URL);
  const items = extractListItems(listHtml);
  if (!items.length) throw new Error('未识别到公告详情链接，网站结构可能已变化');

  const projects = [];
  for (const [index, item] of items.entries()) {
    await sleep(index === 0 ? 0 : REQUEST_DELAY_MS);
    try {
      const detailHtml = await fetchGb2312(item.url);
      const project = parseDetail(detailHtml, item, index);
      if (project.deadline && project.days >= 0) projects.push(project);
      console.log(
        `[${index + 1}/${items.length}] ${project.name} · ${project.deadline || '截止时间缺失'}`,
      );
    } catch (error) {
      console.warn(`[${index + 1}/${items.length}] 采集失败：${item.title}`, error.message);
    }
  }

  const payload = {
    source: SOURCE_NAME,
    sourceUrl: LIST_URL,
    fetchedAt: new Date().toISOString(),
    notice: '仅采集公开招标公告；评级为系统规则生成，责任人、竞争对手和跟踪阶段属于企业内部字段。',
    data: projects,
  };
  await mkdir(dirname(OUTPUT_FILE), { recursive: true });
  await writeFile(OUTPUT_FILE, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
  console.log(`完成：${projects.length} 条未截止真实公告已写入 ${OUTPUT_FILE}`);
}

main().catch((error) => {
  console.error('采集失败：', error);
  process.exitCode = 1;
});
