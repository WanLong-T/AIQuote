const SCORE_CATEGORIES = ['price', 'technical', 'qualification', 'commercial', 'personnel', 'performance', 'credit'];

export function finiteNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

export function calculateBidMetrics(bid, winner, controlPrice) {
  const price = finiteNumber(bid?.evaluatedPrice ?? bid?.correctedPrice ?? bid?.quotedPrice);
  const winnerPrice = finiteNumber(winner?.evaluatedPrice ?? winner?.correctedPrice ?? winner?.quotedPrice);
  const ceiling = finiteNumber(controlPrice);
  const discountRate = ceiling > 0 ? ((ceiling - price) / ceiling) * 100 : null;
  const winnerDiscountRate = ceiling > 0 ? ((ceiling - winnerPrice) / ceiling) * 100 : null;
  return {
    discountRate,
    winnerPriceDifference: winnerPrice > 0 ? price - winnerPrice : null,
    relativePriceDifference: winnerPrice > 0 ? ((price - winnerPrice) / winnerPrice) * 100 : null,
    discountRateDifference:
      discountRate === null || winnerDiscountRate === null ? null : discountRate - winnerDiscountRate,
  };
}

export function normalizeScore(score = {}) {
  const category = SCORE_CATEGORIES.includes(score.category) ? score.category : 'commercial';
  const rawScore = finiteNumber(score.rawScore);
  const convertedScore = finiteNumber(score.convertedScore, rawScore);
  const stageScore = finiteNumber(score.stageScore, convertedScore);
  const finalScore = finiteNumber(score.finalScore, stageScore);
  return {
    category,
    itemName: String(score.itemName || '').trim(),
    rawScore,
    convertedScore,
    stageScore,
    finalScore,
    maxScore: finiteNumber(score.maxScore),
    evidence: String(score.evidence || '').trim(),
    materialDifference: String(score.materialDifference || '').trim(),
  };
}

export function validateComparisonScope(scope = {}) {
  const required = ['sectionCode', 'bidRound', 'taxBasis', 'costBasis'];
  const missing = required.filter((field) => !String(scope[field] || '').trim());
  return { valid: missing.length === 0, missing };
}

export function buildGapAnalysis(ourScores = [], leaderScores = []) {
  const leaderMap = new Map(
    leaderScores.map((score) => {
      const normalized = normalizeScore(score);
      return [`${normalized.category}:${normalized.itemName}`, normalized];
    }),
  );
  return ourScores
    .map(normalizeScore)
    .map((ours) => {
      const leader = leaderMap.get(`${ours.category}:${ours.itemName}`);
      if (!leader) return null;
      return {
        category: ours.category,
        itemName: ours.itemName,
        ourFinalScore: ours.finalScore,
        leaderFinalScore: leader.finalScore,
        scoreGap: leader.finalScore - ours.finalScore,
        ourEvidence: ours.evidence,
        leaderEvidence: leader.evidence,
        materialDifference: ours.materialDifference || leader.materialDifference,
      };
    })
    .filter((item) => item && (item.scoreGap !== 0 || item.materialDifference));
}

export function summarizeCase(record = {}) {
  const bids = Array.isArray(record.bids) ? record.bids : [];
  const validBids = bids.filter((bid) => bid.validity === 'valid');
  const winner = bids.find((bid) => bid.isWinner) || validBids.find((bid) => Number(bid.candidateRank) === 1) || null;
  const ours = bids.find((bid) => bid.isOurs) || null;
  return {
    bidderCount: bids.length,
    validBidderCount: validBids.length,
    winner,
    ours,
    metrics: ours && winner ? calculateBidMetrics(ours, winner, record.controlPrice) : null,
    scope: validateComparisonScope(record.scope),
  };
}

export { SCORE_CATEGORIES };
