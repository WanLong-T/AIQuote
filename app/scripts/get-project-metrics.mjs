import mysql from 'mysql2/promise';

const pool = mysql.createPool({
  host: process.env.BIDDING_DB_HOST || '127.0.0.1',
  port: Number(process.env.BIDDING_DB_PORT || 3306),
  user: process.env.BIDDING_DB_USER || 'root',
  password: process.env.BIDDING_DB_PASSWORD || '',
  database: process.env.BIDDING_DB_NAME || 'bidding_system',
  charset: 'utf8mb4',
  dateStrings: true,
});

const closedStatuses = new Set([
  '已开标', '已中标', '未中标', '废标', '流标', '已终止',
  'OPENED', 'WON', 'LOST', 'VOID', 'FAILED', 'TERMINATED',
]);

function daysUntil(value) {
  if (!value) return -1;
  const target = new Date(String(value).replace(' ', 'T'));
  return Number.isNaN(target.getTime()) ? -1 : Math.ceil((target.getTime() - Date.now()) / 86_400_000);
}

try {
  const [rows] = await pool.query(
    'SELECT open_bid_time, bid_deadline, tracking_stage FROM projects',
  );
  const opportunityCount = rows.filter((row) => {
    const deadline = row.open_bid_time || row.bid_deadline;
    const days = daysUntil(deadline);
    return (days >= 0 || !deadline) && !closedStatuses.has(row.tracking_stage || '');
  }).length;
  process.stdout.write(JSON.stringify({ projectCount: rows.length, opportunityCount }));
} finally {
  await pool.end();
}
