import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import mysql from 'mysql2/promise';

const root = resolve(import.meta.dirname, '..');
const sourceFile = resolve(root, 'data/aiquote-analysis/aiquote-projects.json');
const mapDirectory = resolve(root, 'public/data/maps');
const execute = process.argv.includes('--execute');

function text(value) { return typeof value === 'string' && value.trim() ? value.trim() : null; }
function dateTime(value) {
  const normalized = text(value);
  if (!normalized) return null;
  return /^\d{4}-\d{2}-\d{2}$/.test(normalized) ? `${normalized} 00:00:00` : normalized;
}
function amount(value) {
  if (value === null || value === undefined || value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed.toFixed(2) : null;
}
function identity(row) {
  return createHash('sha256').update([row.source_url, row.section_code, row.project_name, row.publish_time].join('|')).digest('hex').slice(0, 24);
}

async function administrativeCenters() {
  const cities = new Map();
  const provinces = new Map();
  for (const name of await readdir(mapDirectory)) {
    if (!/^\d{6}\.json$/.test(name) || name === '100000.json') continue;
    const code = name.slice(0, 6);
    const geo = JSON.parse(await readFile(resolve(mapDirectory, name), 'utf8'));
    const points = [];
    for (const feature of geo.features || []) {
      const props = feature.properties || {};
      const center = props.center || props.centroid;
      if (props.name && Array.isArray(center)) {
        cities.set(props.name, center);
        points.push(center);
      }
    }
    if (points.length) provinces.set(code.slice(0, 2), [points.reduce((s, p) => s + p[0], 0) / points.length, points.reduce((s, p) => s + p[1], 0) / points.length]);
  }
  const provinceCodes = new Map([
    ['北京市','11'],['天津市','12'],['河北省','13'],['山西省','14'],['内蒙古自治区','15'],['辽宁省','21'],['吉林省','22'],['黑龙江省','23'],['上海市','31'],['江苏省','32'],['浙江省','33'],['安徽省','34'],['福建省','35'],['江西省','36'],['山东省','37'],['河南省','41'],['湖北省','42'],['湖南省','43'],['广东省','44'],['广西壮族自治区','45'],['海南省','46'],['重庆市','50'],['四川省','51'],['贵州省','52'],['云南省','53'],['西藏自治区','54'],['陕西省','61'],['甘肃省','62'],['青海省','63'],['宁夏回族自治区','64'],['新疆维吾尔自治区','65'],
  ]);
  return { cities, provinces, provinceCodes };
}

const rows = JSON.parse(await readFile(sourceFile, 'utf8')).filter((row) => row.province && row.province !== '江苏省' && row.project_name);
const centers = await administrativeCenters();
const db = await mysql.createConnection({
  host: process.env.BIDDING_DB_HOST || '127.0.0.1', port: Number(process.env.BIDDING_DB_PORT || 3306),
  user: process.env.BIDDING_DB_USER || 'root', password: process.env.BIDDING_DB_PASSWORD || '',
  database: process.env.BIDDING_DB_NAME || 'bidding_system', charset: 'utf8mb4', dateStrings: true,
});
const [existingRows] = await db.query('SELECT source_url, section_code FROM projects');
const existingUrls = new Set(existingRows.map((row) => text(row.source_url)).filter(Boolean));
const existingSections = new Set(existingRows.map((row) => text(row.section_code)).filter(Boolean));
const pending = rows.filter((row) => !(text(row.source_url) && existingUrls.has(text(row.source_url))) && !(text(row.section_code) && existingSections.has(text(row.section_code))));
const provinceCounts = Object.fromEntries([...new Set(pending.map((row) => row.province))].sort().map((province) => [province, pending.filter((row) => row.province === province).length]));
console.log(JSON.stringify({ mode: execute ? 'execute' : 'dry-run', source: rows.length, duplicates: rows.length - pending.length, pending: pending.length, provinceCounts }, null, 2));

if (execute && pending.length) {
  const sql = `INSERT INTO projects
    (project_id, project_name, parent_project_name, project_code, section_code, project_type,
     province, city, district, owner_name, tenderer_name, main_entity_name, main_entity_type,
     publish_time, bid_deadline, control_price, estimated_contract_amount, provisional_sum,
     tracking_stage, rating, source_platform, source_row_id, source_url, list_project_name,
     data_quality_status, quality_warnings, quality_errors, crawl_time,
     longitude, latitude, geocode_level, geocode_source, geocoded_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`;
  await db.beginTransaction();
  try {
    for (const row of pending) {
      const cityCenter = centers.cities.get(row.city);
      const provinceCenter = centers.provinces.get(centers.provinceCodes.get(row.province));
      const center = cityCenter || provinceCenter || null;
      const id = identity(row);
      const entity = text(row.owner_name) || text(row.tenderer_name);
      await db.execute(sql, [
        `AIQUOTE-${id}`, text(row.project_name), text(row.project_name), text(row.project_code), text(row.section_code), text(row.project_type),
        text(row.province), text(row.city), text(row.district), text(row.owner_name), text(row.tenderer_name), entity, entity ? '建设/招标单位' : null,
        dateTime(row.publish_time), dateTime(row.bid_deadline), amount(row.control_price), amount(row.estimated_contract_amount), amount(row.provisional_sum),
        'LEAD', 'UNRATED', text(row.source_platform), id, text(row.source_url), text(row.project_name),
        text(row.data_quality_status) || 'IMPORTED', JSON.stringify(['来自AIQuote历史快照，导入后应复核时效与原公告']), JSON.stringify([]), new Date(),
        center?.[0] ?? null, center?.[1] ?? null, cityCenter ? 'city_centroid' : provinceCenter ? 'province_centroid' : null,
        center ? 'amap_boundary' : null, center ? new Date() : null,
      ]);
    }
    await db.commit();
  } catch (error) {
    await db.rollback();
    throw error;
  }
  console.log(`Imported ${pending.length} projects.`);
}
await db.end();
