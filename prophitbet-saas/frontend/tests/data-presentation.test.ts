import { afterEach, describe, expect, it, vi } from 'vitest';
import { groupMatchPredictions } from '../lib/prediction-groups';
import { cleanLeagueName, cn, formatDate, formatMatchDay, formatMatchKickoff,
  formatSASTDateTime, formatUtcToLocal, getCountryPriority, getLeaguePriority,
  matchesLeagueFilter, planBadgeColor, resultColor, sortUpcomingFirst } from '../lib/utils';

afterEach(() => vi.useRealTimers());

describe('league identity', () => {
  const english = { league_id: 6, league_name: 'Premier-League', country: 'England' };
  const russian = { league_id: 26, league_name: 'Premier-League', country: 'Russia' };
  it('requires country for ambiguous display names', () => {
    expect(matchesLeagueFilter(english, 'Premier League')).toBe(true);
    expect(matchesLeagueFilter(russian, 'Premier League')).toBe(false);
    expect(matchesLeagueFilter({ league_name: 'Premier-League' }, 'Premier League')).toBe(false);
    expect(matchesLeagueFilter(russian, 'Russian Premier League')).toBe(true);
    expect(matchesLeagueFilter({ country: 'Brazil', league_name: 'Serie-A' }, 'Serie A')).toBe(false);
    expect(matchesLeagueFilter({ country: 'Scotland', league_name: 'Premiership' }, 'PSL')).toBe(false);
  });
  it('uses IDs authoritatively and fails closed for unknown names', () => {
    expect(matchesLeagueFilter(russian, 'ALL', 6)).toBe(false);
    expect(matchesLeagueFilter(english, 'wrong label', 6)).toBe(true);
    expect(matchesLeagueFilter({}, 'Premier League', 6)).toBe(false);
    expect(matchesLeagueFilter(russian, 'league:26')).toBe(true);
    expect(matchesLeagueFilter(english, 'league:26')).toBe(false);
    expect(matchesLeagueFilter(english, 'unknown')).toBe(false);
    expect(matchesLeagueFilter({}, '')).toBe(true);
    expect(matchesLeagueFilter({}, 'all')).toBe(true);
  });
  it.each([
    ['Premier-League', 'Russia', 'Russian Premier League'], ['Serie-A', 'Brazil', 'Serie A (Brazil)'],
    ['Liga-1', 'Portugal', 'Liga Portugal'], ['Liga-1', 'Romania', 'Liga 1 (Romania)'],
    ['Super-League', 'Greece', 'Super League (Greece)'], ['Super-League', 'Switzerland', 'Swiss Super League'],
    ['Super-League', 'China', 'Chinese Super League'], ['Premiership', 'Scotland', 'Scottish Premiership'],
    ['Bundesliga-1', 'Germany', 'Bundesliga'], ['Betway-Premiership', 'South Africa', 'Betway Premiership'],
    ['Other-League', 'Other', 'Other League'], ['', '', ''],
  ])('labels %s in %s', (league, country, expected) => {
    expect(cleanLeagueName(league, country)).toBe(expected);
  });
  it('prioritizes configured leagues and countries with a stable fallback', () => {
    expect(getLeaguePriority('Betway-Premiership', 'South Africa')).toBe(1);
    expect(getLeaguePriority('Premier-League', 'England')).toBe(2);
    expect(getLeaguePriority('Premier-League', 'Russia')).toBe(100);
    expect(getCountryPriority('ENGLAND')).toBe(2);
    expect(getCountryPriority('Unknown')).toBe(50);
  });
});

describe('fixture grouping', () => {
  const match = { id: '1', league_id: 6, home_team: 'A', away_team: 'B',
    match_date: '2026-10-06T10:00:00Z', market_type: 'result', created_at: '2026-10-01' };
  it('groups markets and retains the newest version of each market', () => {
    const total = { ...match, id: '2', market_type: 'over_under' };
    const newer = { ...match, id: '3', created_at: '2026-10-02' };
    const grouped = groupMatchPredictions([total, newer, match]);
    expect(grouped).toHaveLength(1);
    expect(grouped[0].id).toBe('3');
    expect(grouped[0].markets.map(row => row.id)).toEqual(['2', '3']);
    expect(groupMatchPredictions([total])[0].id).toBe('2');
  });
  it('normalizes time zones and spelling whitespace but preserves fixture identity', () => {
    expect(groupMatchPredictions([match, { ...match, id: '2', home_team: ' a ',
      match_date: '2026-10-06T12:00:00+02:00', market_type: 'goals' }])).toHaveLength(1);
    expect(groupMatchPredictions([match, { ...match, league_id: 26 }])).toHaveLength(2);
    expect(groupMatchPredictions([match, { ...match, match_date: '2026-10-07T10:00:00Z' }])).toHaveLength(2);
  });
  it('does not merge missing or invalid kickoff identities', () => {
    expect(groupMatchPredictions([{ ...match, match_date: null },
      { ...match, id: '2', match_date: 'invalid' }])).toHaveLength(2);
    expect(groupMatchPredictions([{ ...match, market_type: undefined, created_at: undefined }])[0].id).toBe('1');
    expect(groupMatchPredictions([])).toEqual([]);
  });
});

describe('dates and ordering', () => {
  it('renders explicit South African time, not the host time zone', () => {
    expect(formatSASTDateTime('2026-10-06T10:00:00Z')).toContain('12:00 SAST');
  });
  it.each([formatDate, formatUtcToLocal, formatMatchDay, formatMatchKickoff, formatSASTDateTime])(
    'renders missing dates as unavailable', formatter => {
      expect(formatter(null)).toBe('—');
      expect(formatter(undefined)).toBe('—');
    });
  it('rejects invalid dates in time formatters', () => {
    expect(formatDate('invalid')).toBe('—');
    expect(formatMatchDay('invalid')).toBe('—');
    expect(formatUtcToLocal('invalid')).toBe('—');
    expect(formatMatchKickoff('invalid')).toBe('—');
    expect(formatSASTDateTime('invalid')).toBe('—');
  });
  it('uses calendar-day labels and orders upcoming then settled matches', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 6, 12));
    expect(formatMatchDay(new Date(2026, 9, 6, 16).toISOString())).toBe('Today');
    expect(formatMatchDay(new Date(2026, 9, 7, 16).toISOString())).toBe('Tomorrow');
    expect(formatMatchDay(new Date(2026, 9, 5, 16).toISOString())).toBe('Yesterday');
    expect(formatMatchDay('2026-10-01T12:00:00Z')).toContain('Oct');
    const upcoming = { match_date: '2026-10-07T10:00:00Z' };
    const later = { match_date: '2026-10-08T10:00:00Z' };
    const settled = { match_date: '2026-10-06T10:00:00Z', actual_result: 'H' };
    expect(sortUpcomingFirst(upcoming, settled)).toBeLessThan(0);
    expect(sortUpcomingFirst(settled, upcoming)).toBeGreaterThan(0);
    expect(sortUpcomingFirst(upcoming, later)).toBeLessThan(0);
    expect(sortUpcomingFirst(settled, {})).toBeLessThan(0);
    expect(sortUpcomingFirst(settled, { match_date: 'invalid' })).toBeLessThan(0);
    expect(sortUpcomingFirst({ match_date: 'invalid' }, settled)).toBeGreaterThan(0);
  });
});

it('uses defined badge styles and merges conflicting utility classes', () => {
  expect(cn('p-2', false, 'p-4')).toBe('p-4');
  for (const result of ['H', 'A', 'D', 'Over', 'Under', 'unknown']) {
    expect(resultColor(result)).toMatch(/^text-/);
  }
  for (const plan of ['elite', 'pro', 'free']) expect(planBadgeColor(plan)).toContain('border-');
});
