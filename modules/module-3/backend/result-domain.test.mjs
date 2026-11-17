import assert from 'node:assert/strict';
import test from 'node:test';
import {
  buildGapAnalysis,
  calculateBidMetrics,
  normalizeScore,
  summarizeCase,
  validateComparisonScope,
} from './result-domain.mjs';

test('calculates the four requested price comparison metrics', () => {
  const metrics = calculateBidMetrics({ correctedPrice: 91 }, { correctedPrice: 90 }, 100);
  assert.equal(metrics.discountRate, 9);
  assert.equal(metrics.winnerPriceDifference, 1);
  assert.ok(Math.abs(metrics.relativePriceDifference - 1.111111) < 0.00001);
  assert.equal(metrics.discountRateDifference, -1);
});

test('keeps raw, converted, stage and final scores separately', () => {
  assert.deepEqual(normalizeScore({ category: 'technical', itemName: '施工方案', rawScore: 8, convertedScore: 7.2, stageScore: 6.5, finalScore: 6.5 }).finalScore, 6.5);
});

test('rejects cross-scope comparison when a required dimension is missing', () => {
  assert.deepEqual(validateComparisonScope({ sectionCode: 'A', bidRound: '1', taxBasis: '含税' }), { valid: false, missing: ['costBasis'] });
});

test('finds score and material gaps against the leader', () => {
  const gaps = buildGapAnalysis(
    [{ category: 'performance', itemName: '类似业绩', finalScore: 3, evidence: '2项', materialDifference: '缺1项业绩' }],
    [{ category: 'performance', itemName: '类似业绩', finalScore: 5, evidence: '3项' }],
  );
  assert.equal(gaps[0].scoreGap, 2);
  assert.equal(gaps[0].materialDifference, '缺1项业绩');
});

test('summarizes winner and our bidder without mutating facts', () => {
  const record = {
    controlPrice: 100,
    scope: { sectionCode: 'A', bidRound: '1', taxBasis: '含税', costBasis: '全费用' },
    bids: [
      { bidderName: '我方', correctedPrice: 91, validity: 'valid', isOurs: true },
      { bidderName: '中标方', correctedPrice: 90, validity: 'valid', candidateRank: 1, isWinner: true },
    ],
  };
  const snapshot = JSON.stringify(record);
  assert.equal(summarizeCase(record).winner.bidderName, '中标方');
  assert.equal(JSON.stringify(record), snapshot);
});
