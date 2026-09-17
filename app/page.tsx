'use client';

import { useState, useMemo, useEffect } from 'react';

const FPL_SUCCESS_TIPS = [
  {
      "num": 1,
      "icon": "⏳",
      "title_he": "שמירת חילופים (Roll Transfers)",
      "title_en": "Roll Your Free Transfers",
      "desc_he": "אל תבצע חילוף אוטומטי בכל מחזור רק כי יש לך חילוף פנוי. צבירת 2 עד 5 חילופים חינמיים מעניקה גמישות אסטרטגית אדירה למהפכות סגל קטנות ללא קנס נקודות.",
      "desc_en": "Never burn a free transfer just because you have one. Stacking 2 to 5 free transfers provides massive strategic leverage to overhaul multiple positions without taking point hits.",
      "rule_he": "אין מהלך בוער? שמור את החילוף ותהנה מכוח תמרון כפול במחזור הבא.",
      "rule_en": "No urgent move? Roll the transfer and gain double flexibility next week.",
      "tag_he": "סבלנות",
      "tag_en": "Patience",
  },
  {
      "num": 2,
      "icon": "🛡️",
      "title_he": "הימנעות ממינוסים מיותרים (Avoid -4 Hits)",
      "title_en": "Avoid Unnecessary -4 Point Hits",
      "desc_he": "שחקן שנרכש בקנס 4- נקודות נדרש להבקיע או לבשל רק כדי לאפס את העלות שלו. קח מינוס רק במקרה חירום של חוסר 11 שחקנים כשירים או עבור קפטן מובהק לטווח ארוך.",
      "desc_en": "A player bought on a -4 hit must effectively return a goal or assist just to break even. Take hits strictly for injury crises or long-term high-ceiling captains.",
      "rule_he": "מינוסים מצטברים שוחקים את הדירוג: הימנע מהם ככל האפשר.",
      "rule_en": "Point hits erode long-term rank. Take them only for emergencies or long-term holds.",
      "tag_he": "משמעת",
      "tag_en": "Discipline",
  },
  {
      "num": 3,
      "icon": "👑",
      "title_he": "משמעת קפטן ובעלות אפקטיבית (Captaincy)",
      "title_en": "Captaincy Discipline & Effective Ownership",
      "desc_he": "אל תהמר על קפטן הרפתקני רק כדי 'להתחכם'. מעל 60% מהניקוד מגיע מהקפטן; בחר בשחקן המוביל עם ה-xP והבעלות הגבוהים ביותר (כמו האלנד או ברונו פרננדס).",
      "desc_en": "Don't gamble on wild differential captains. Over 60% of your rank progress relies on the armband; trust high-xP, high-ownership talismans with favorable fixtures.",
      "rule_he": "הקפטן מגן על הדירוג - את הדיפרנציאלים מייצרים בשחקני השדה.",
      "rule_en": "The armband protects your rank - let your outfield picks provide the differential edge.",
      "tag_he": "קפטן",
      "tag_en": "Captaincy",
  },
  {
      "num": 4,
      "icon": "🗓️",
      "title_he": "תכנון בטווחי 3-5 מחזורים (3-5 GW Blocks)",
      "title_en": "Plan in 3-5 Gameweek Horizons",
      "desc_he": "לעולם אל תקנה שחקן בשביל משחק אחד בלבד. בחן תמיד את לוח המשחקים (FDR) של 3 עד 5 המחזורים הבאים כדי להימנע מחילופי 'כיבוי שריפות' שבוע לאחר מכן.",
      "desc_en": "Never buy a player for a single fixture. Always evaluate the upcoming 3 to 5 gameweek run (FDR) to avoid burning future transfers fixing short-term punts.",
      "rule_he": "חשוב תמיד שבועיים-שלושה קדימה לפני כל לחיצה על כפתור הרכש.",
      "rule_en": "Always review the next 3-5 fixtures before confirming any market transfer.",
      "tag_he": "תכנון",
      "tag_en": "Planning",
  },
  {
      "num": 5,
      "icon": "⏱️",
      "title_he": "החלטות סמוך לדדליין (Wait for Press Conferences)",
      "title_en": "Wait for Press Conferences & News",
      "desc_he": "המתן למסיבות העיתונאים של ימי שישי ולעדכוני פציעות אחרונים לפני ביצוע חילוף. העברות מוקדמות באמצע השבוע מסתכנות בפציעות באימונים או בגביעים אירופיים.",
      "desc_en": "Delay transfers until Friday press conferences and verified deadline team news. Mid-week transfers risk training knocks and European rotation surprises.",
      "rule_he": "סבלנות מונעת אסונות: המתן לעדכוני המאמנים הרשמיים לפני חילופים.",
      "rule_en": "Patience prevents blunders: hold transfers until verified press conferences.",
      "tag_he": "תזמון",
      "tag_en": "Timing",
  },
  {
      "num": 6,
      "icon": "🪑",
      "title_he": "ספסל חסכוני ובטוח דקות (Smart Bench Enablers)",
      "title_en": "Smart Bench & Budget Enablers",
      "desc_he": "אל תקבור מיליונים יקרים בספסל. דאג לשחקן ספסל אחד או שניים בטוחים לפתוח במחיר רצפה (£4.0m-£4.5m) שייכנסו אוטומטית בעת הצורך, והשקע את הכסף ב-11 הפותחים.",
      "desc_en": "Do not trap valuable team value on your bench. Keep 1-2 cheap, guaranteed starters (£4.0m-£4.5m) as auto-sub safety nets while maximizing funds on your Starting XI.",
      "rule_he": "ספסל זול עם דקות קבועות מאפשר הרכב פותח עתיר כוכבים.",
      "rule_en": "A cheap bench with secure minutes funds premium heavy hitters in your starting XI.",
      "tag_he": "תקציב",
      "tag_en": "Budget",
  },
  {
      "num": 7,
      "icon": "📊",
      "title_he": "ללא פאניקה - אמון בנתונים (Trust Underlying Data)",
      "title_en": "Avoid Knee-Jerking & Trust Analytics",
      "desc_he": "אל תמכור שחקן איכותי רק כי סיים עם 2 נקודות במחזור בודד, ואל תרוץ לקנות שחקן שהבקיע שער מקרי. סמוך על מדדי ה-xG/xA והנתונים הסטטיסטיים לאורך זמן.",
      "desc_en": "Do not rage-sell premium assets after a single blank, nor chase random defensive flukes. Trust underlying expected metrics (xG, xA, xP) over past variance.",
      "rule_he": "מזל חולף, תוחלת מנצחת: שחקן שמייצר מצבים טובים יחזיר נקודות לאורך זמן.",
      "rule_en": "Variance is temporary, underlying process is permanent: trust high-xG/xA stars.",
      "tag_he": "אנליטיקה",
      "tag_en": "Analytics",
  },
  {
      "num": 8,
      "icon": "🏦",
      "title_he": "שמירה על רזרבה בבנק (£0.5m-£1.0m ITB)",
      "title_en": "Keep Liquidity In The Bank (£0.5m-£1.0m ITB)",
      "desc_he": "השארת סכום צנוע של 0.5-1.0 מיליון ליש\"ט בבנק מעניקה גמישות אדירה לעבור מיד לשחקן פורץ או כוכב בכושר בלי צורך לפרק חצי סגל או לקחת מינוסים.",
      "desc_en": "Maintaining £0.5m-£1.0m in the bank allows you to instantly jump onto emerging breakout stars without requiring multi-transfer squad surgery.",
      "rule_he": "כסף בבנק הוא חופש תמרון שמגן עליך משינויי מחירים מהירים.",
      "rule_en": "Cash in the bank equals agility: it shields you from rapid market price rises.",
      "tag_he": "גמישות",
      "tag_en": "Flexibility",
  },
  {
      "num": 9,
      "icon": "⚡",
      "title_he": "תזמון צ'יפים במחזורים מיוחדים (DGW & BGW)",
      "title_en": "Strategic Chip Timing (DGW & BGW)",
      "desc_he": "שמור את הצ'יפים החזקים (Wildcard, Free Hit, Bench Boost, Triple Captain) למחזורים הכפולים (DGW) והריקים (BGW) בחצי השני של העונה לקצירת עשרות נקודות יתרון.",
      "desc_en": "Preserve high-impact chips (Wildcard, Free Hit, Bench Boost, Triple Captain) for late-season Double (DGW) and Blank (BGW) weeks to exploit massive point swings.",
      "rule_he": "צ'יפ במחזור כפול שווה פי שניים או שלושה לעומת מחזור רגיל.",
      "rule_en": "A chip played in a Double Gameweek yields massively higher returns.",
      "tag_he": "צ'יפים",
      "tag_en": "Chips",
  },
  {
      "num": 10,
      "icon": "🎯",
      "title_he": "דיפרנציאלים מחושבים לטיפוס בליגה (Target Differentials)",
      "title_en": "Target High-Upside Differentials",
      "desc_he": "שחקנים בבעלות של מעל 60% מגנים על הדירוג שלך; אבל כדי לסגור פערים בליגה הפרטית שלך כשאתה רודף מאחור, שחקני מפתח איכותיים בבעלות מתחת ל-10% הם המנוע לניצחון.",
      "desc_en": "High-ownership players protect rank; but to bridge deficits in private mini-leagues, high-upside low-ownership differentials (<10%) are the true accelerators.",
      "rule_he": "שמור על שלד בטוח להגנה על הדירוג, והוסף 1-2 דיפרנציאלים לעקיפה.",
      "rule_en": "Anchor with essential template players, and hunt differentials to bridge gaps.",
      "tag_he": "מיני-ליגות",
      "tag_en": "Mini-Leagues",
  },
]



const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

export default function Home() {
  const [teamId, setTeamId] = useState('');
  const [data, setData] = useState<any>(null);

  const [initLoading, setInitLoading] = useState(true);
  const [tipIndex, setTipIndex] = useState(0);



  const [originalData, setOriginalData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [swapSourceId, setSwapSourceId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'pitch' | 'transfer' | 'planner' | 'analysis' | 'radar' | 'budget' | 'leagues' | 'tips'>('planner');
  const [appAlert, setAppAlert] = useState<string | null>(null);
  const [transferOutId, setTransferOutId] = useState<number | null>(null);
  const [transferRecs, setTransferRecs] = useState<any[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [transferError, setTransferError] = useState('');

  // חדש: מצב כהה ושפות
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isEnglish, setIsEnglish] = useState(false);

  // מילון תרגומים
  const dict = {
    he: {
      changeTeam: "החלף קבוצה",
      darkMode: "מצב כהה",
      lightMode: "מצב בהיר",
      overallRank: "דירוג כללי",
      bank: "יתרה בבנק",
      xp: "תוחלת נקודות (xP)",
      squadScore: "ציון סגל נוכחי",
      timeUntil: "זמן נותר עד נעילת חילופים",
      pitchTab: "הסגל על המגרש",
      transferTab: "מעבדת חילופים",
      analysisTab: "ניתוח סגל וחסרונות",
      radarTab: "רדאר רכש עילית",
      budgetTab: "תרחישי תקציב",
      plannerTab: "מתכנן מחזורים",
      leaguesTab: "מיני-ליגות וראש בראש",
      tipsTab: "טיפים להצלחה 💡",
      cap: "קפטן (C):",
      vcap: "סגן קפטן (VC):",
      enterId: "הזן את מספר הקבוצה שלך",
      placeholder: "לדוגמה: 139103",
      connect: "התחבר",
      loading: "טוען...",
      engineFor: "מנוע המלצות למחזור",
      teamWord: "קבוצה:"
    },
    en: {
      changeTeam: "Change Team",
      darkMode: "Dark Mode",
      lightMode: "Light Mode",
      overallRank: "Overall Rank",
      bank: "Bank Balance",
      xp: "Expected Points (xP)",
      squadScore: "Squad Score",
      timeUntil: "Time until GW deadline",
      pitchTab: "Pitch View",
      transferTab: "Transfer Lab",
      analysisTab: "Squad Analysis",
      radarTab: "Elite Radar",
      budgetTab: "Budget Scenarios",
      plannerTab: "GW Planner",
      leaguesTab: "Mini-Leagues & H2H",
      tipsTab: "Tips & Tricks 💡",
      cap: "Captain (C):",
      vcap: "Vice Captain (VC):",
      enterId: "Enter your Team ID",
      placeholder: "Example: 139103",
      connect: "Connect",
      loading: "Loading...",
      engineFor: "AI Engine for GW",
      teamWord: "Team:"
    }
  };
  
  const t = isEnglish ? dict.en : dict.he;
  
  // צבעי המערכת בהתאם למצב (Dark/Light)
  const bgMain = isDarkMode ? "bg-gray-900 text-gray-100" : "bg-[#f8f9fa] text-gray-900";
  const bgCard = isDarkMode ? "bg-gray-800 border-gray-700 text-white" : "bg-white border-gray-200 text-gray-900";
  const bgBox = isDarkMode ? "bg-gray-800 shadow-md text-white" : "bg-white shadow-sm text-gray-900";

  const textMuted = isDarkMode ? "text-gray-400" : "text-gray-500";
  const textHighlight = isDarkMode ? "text-gray-200" : "text-[#1a202c]";

  const fetchTeam = async (overrideId?: string) => {
    const idToFetch = (overrideId || teamId)?.toString().trim();
    if (!idToFetch) return;
    setLoading(true);
    setError('');
    setTransferError('');
    setSwapSourceId(null);
    setTransferOutId(null);
    setTransferRecs([]);
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/${idToFetch}`);
      if (!res.ok) throw new Error(`[Debug] HTTP ${res.status} from ${res.url} | ID: '${idToFetch}'`);
      const result = await res.json();
      setOriginalData(result);
      localStorage.setItem('fpl_team_id', idToFetch);
      
      const savedPlanStr = localStorage.getItem(`fpl_plan_${idToFetch}`);
      if (savedPlanStr) {
        try {
          const savedPlan = JSON.parse(savedPlanStr);
          // Only load if it matches the current upcoming GW, so outdated plans are wiped
          if (savedPlan.next_gw === result.next_gw) {
            setData(savedPlan);
            return;
          }
        } catch (e) {}
      }
      setData(result);
    } catch (err: any) {
      setError(err.message);
      if (overrideId) localStorage.removeItem('fpl_team_id');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const savedId = localStorage.getItem('fpl_team_id');
    if (savedId) {
      setTeamId(savedId);
      fetchTeam(savedId).finally(() => setInitLoading(false));
    } else {
      setInitLoading(false);
    }
    
    const interval = setInterval(() => {
      setTipIndex(prev => (prev + 1) % FPL_SUCCESS_TIPS.length);
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (data && data.team_id) {
      localStorage.setItem(`fpl_plan_${data.team_id}`, JSON.stringify(data));
    }
  }, [data]);

  const handleReset = () => {
    if (originalData) {
      setData(originalData);
      setSwapSourceId(null);
      setTransferOutId(null);
    }
  };

  const handleRestorePlayer = (position: number) => {
    if (!originalData) return;
    const originalPlayer = originalData.squad.find((p: any) => p.position === position);
    const currentPlayer = data.squad.find((p: any) => p.position === position);
    if (!originalPlayer || !currentPlayer) return;

    const newBank = data.bank + currentPlayer.cost - originalPlayer.cost;
    const newSquad = data.squad.map((p: any) => p.position === position ? originalPlayer : p);
    
    setData({ ...data, squad: newSquad, bank: newBank });
  };

  const executeTransfer = (newPlayer: any) => {
    if (!transferOutId) return;
    const oldPlayer = data.squad.find((p: any) => p.id === transferOutId);
    if (!oldPlayer) return;

    const newBank = data.bank + oldPlayer.cost - newPlayer.cost;
    
    // בדיקת חריגה מהתקציב - הוסרה לבקשת המשתמש כדי לאפשר תכנון
    // if (newBank < 0) {
    //   setTransferError(isEnglish ? `Cannot afford ${newPlayer.name}. You are short £${Math.abs(newBank).toFixed(1)}M.` : `אין לך מספיק תקציב עבור ${newPlayer.name}. חסר לך £${Math.abs(newBank).toFixed(1)}M.`);
    //   return;
    // }

    const upcoming_fixtures = [];
    for (let offset = 0; offset <= 38 - data.next_gw; offset++) {
      const gw = data.next_gw + offset;
      const gwFixtures = data.schedule[gw] || [];
      let found = false;
      for (const match of gwFixtures) {
        if (match.home_team === newPlayer.team) {
          upcoming_fixtures.push({ gw, opponent: `${match.away_team} (H)`, difficulty: match.home_diff });
          found = true;
          break;
        } else if (match.away_team === newPlayer.team) {
          upcoming_fixtures.push({ gw, opponent: `${match.home_team} (A)`, difficulty: match.away_diff });
          found = true;
          break;
        }
      }
      if (!found) {
        upcoming_fixtures.push({ gw, opponent: "Blank", difficulty: 5 });
      }
    }

    setTransferError('');
    const newSquad = data.squad.filter((p: any) => p.id !== oldPlayer.id);
    
    newSquad.push({
      ...newPlayer,
      position: oldPlayer.position,
      is_captain: oldPlayer.is_captain,
      is_vice_captain: oldPlayer.is_vice_captain,
      fixture: upcoming_fixtures[0]?.opponent || "Blank",
      fixture_diff: upcoming_fixtures[0]?.difficulty || 5,
      upcoming_fixtures: upcoming_fixtures
    });

    setData({ ...data, squad: newSquad, bank: newBank });
    setTransferOutId(null);
    setTransferRecs([]);
    setSearchQuery('');
    setActiveTab('pitch');
  };
  const executeVirtualTransfer = (oldPlayerId: number, newPlayer: any) => {
    const oldPlayer = data.squad.find((p: any) => p.id === oldPlayerId);
    if (!oldPlayer) return;
    const newBank = data.bank + oldPlayer.cost - newPlayer.cost;
    const newSquad = data.squad.filter((p: any) => p.id !== oldPlayer.id);

    const upcoming_fixtures = [];
    for (let offset = 0; offset <= 38 - data.next_gw; offset++) {
      const gw = data.next_gw + offset;
      const gwFixtures = data.schedule[gw] || [];
      let found = false;
      for (const match of gwFixtures) {
        if (match.home_team === newPlayer.team) {
          upcoming_fixtures.push({ gw, opponent: `${match.away_team} (H)`, difficulty: match.home_diff });
          found = true;
          break;
        } else if (match.away_team === newPlayer.team) {
          upcoming_fixtures.push({ gw, opponent: `${match.home_team} (A)`, difficulty: match.away_diff });
          found = true;
          break;
        }
      }
      if (!found) {
        upcoming_fixtures.push({ gw, opponent: "Blank", difficulty: 5 });
      }
    }

    newSquad.push({
      ...newPlayer,
      position: oldPlayer.position,
      is_captain: oldPlayer.is_captain,
      is_vice_captain: oldPlayer.is_vice_captain,
      fixture: upcoming_fixtures[0]?.opponent || "Blank",
      fixture_diff: upcoming_fixtures[0]?.difficulty || 5,
      upcoming_fixtures: upcoming_fixtures
    });
    setData({ ...data, squad: newSquad, bank: newBank });
  };

  const handlePlayerClick = async (playerId: number) => {
    if (activeTab === 'transfer') {
      setTransferError('');
      setTransferOutId(playerId);
      const playerToSell = data.squad.find((p: any) => p.id === playerId);
      if (playerToSell) {
        setLoadingRecs(true);
        try {
          const budget = data.bank + playerToSell.cost;
          const currentSquadIds = data.squad.map((p: any) => p.id);
          const res = await fetch(`${API_BASE_URL}/api/transfer-lab`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              pos_code: playerToSell.pos_code,
              max_budget: budget,
              current_squad_ids: currentSquadIds
            })
          });
          const recs = await res.json();
          setTransferRecs(recs);
        } catch (err) {
          console.error("Failed to fetch recs", err);
        } finally {
          setLoadingRecs(false);
        }
      }
    } else {
      handleSwapClick(playerId);
    }
  };

  const starters = data?.squad.filter((p: any) => p.position <= 11) || [];
  const bench = data?.squad.filter((p: any) => p.position > 11) || [];

  const totalXP = starters.reduce((acc: number, p: any) => acc + (p.xp * (p.multiplier || 1)), 0);
  const avgFDR = starters.reduce((acc: number, p: any) => acc + (p.fixture_diff || 3), 0) / (starters.length || 1);
  const avgForm = starters.reduce((acc: number, p: any) => acc + (p.form || 0), 0) / (starters.length || 1);
  
  const injuryPenalty = starters.reduce((acc: number, p: any) => {
    if (p.chance_of_playing === 0) return acc + 6;
    if (p.chance_of_playing !== null && p.chance_of_playing !== undefined && p.chance_of_playing < 100) return acc + 3;
    return acc;
  }, 0);

  // Extremely strict Squad Score Algorithm (Comparing to Elite platforms like FPL Review / FFH)
  // Most active teams will land between 70-85. Getting above 90 will require near-perfect optimization.
  // Base 20. 
  // 1 point per xP above 30 (e.g., 65 xP = 35 points)
  // Form multiplier: avgForm * 3
  // FDR multiplier: (3.0 - avgFDR) * 10
  const rawScore = 20 + Math.max(0, totalXP - 30) + (avgForm * 3) + ((3.0 - avgFDR) * 10) - injuryPenalty;
  const calculatedSquadScore = Math.min(99, Math.max(10, Math.round(rawScore)));
  
  const currentCaptain = data?.squad.find((p: any) => p.is_captain);
  const currentVice = data?.squad.find((p: any) => p.is_vice_captain);

  const handleCaptainClick = (playerId: number) => {
    const newSquad = data.squad.map((p: any) => {
      if (p.id === playerId) return { ...p, is_captain: true, is_vice_captain: false, multiplier: 2 };
      if (p.is_captain && p.id !== playerId) return { ...p, is_captain: false, multiplier: 1 };
      return p;
    });
    setData({ ...data, squad: newSquad });
  };

  const handleViceClick = (playerId: number) => {
    const newSquad = data.squad.map((p: any) => {
      if (p.id === playerId) return { ...p, is_vice_captain: true, is_captain: false, multiplier: 1 };
      if (p.is_vice_captain && p.id !== playerId) return { ...p, is_vice_captain: false };
      return p;
    });
    setData({ ...data, squad: newSquad });
  };

  const handleSwapClick = (playerId: number) => {
    if (swapSourceId === null) {
      setSwapSourceId(playerId);
    } else if (swapSourceId === playerId) {
      setSwapSourceId(null);
    } else {
      const newSquad = [...data.squad];
      const p1 = newSquad.find((p: any) => p.id === swapSourceId);
      const p2 = newSquad.find((p: any) => p.id === playerId);
      
      if (p1 && p2) {
        // --- בדיקת חוקיות מערך ---
        let isValid = true;
        if (p1.pos_code !== p2.pos_code) {
          // אי אפשר להחליף שוער עם שחקן שדה
          if (p1.pos_code === 1 || p2.pos_code === 1) {
            isValid = false;
          } else {
            const p1Pitch = p1.position <= 11;
            const p2Pitch = p2.position <= 11;
            
            // אם אחד נכנס ואחד יוצא, צריך לבדוק שמירה על מינימום שחקנים לעמדה
            if (p1Pitch !== p2Pitch) {
              const leaving = p1Pitch ? p1 : p2;
              const entering = p1Pitch ? p2 : p1;
              
              const pitchAfter = newSquad.filter((p: any) => p.position <= 11 && p.id !== leaving.id);
              pitchAfter.push(entering);
              
              const defs = pitchAfter.filter((p: any) => p.pos_code === 2).length;
              const fwds = pitchAfter.filter((p: any) => p.pos_code === 4).length;
              
              // חוקי FPL: מינימום 3 שחקני הגנה ומינימום 1 חלוץ בהרכב הפותח
              if (defs < 3 || fwds < 1) {
                isValid = false;
              }
            }
          }
        }
        
        if (!isValid) {
          setAppAlert(isEnglish ? "Invalid formation! FPL rules require 1 GK, at least 3 Defenders, and at least 1 Forward." : "חילוף לא חוקי! לפי חוקי הפנטזי חובה להציב שוער 1, לפחות 3 שחקני הגנה, ולפחות חלוץ 1.");
          setSwapSourceId(null);
          return;
        }
        // ------------------------

        const tempPos = p1.position;
        p1.position = p2.position;
        p2.position = tempPos;
      }
      setData({ ...data, squad: newSquad });
      setSwapSourceId(null);
    }
  };

  const handleSetCaptain = (id: number) => {
    const newSquad = [...data.squad];
    const oldCap = newSquad.find((p: any) => p.is_captain);
    const newCap = newSquad.find((p: any) => p.id === id);
    if (!newCap) return;

    if (newCap.is_vice_captain) {
      newCap.is_vice_captain = false;
      if (oldCap) oldCap.is_vice_captain = true;
    } else {
      if (oldCap) oldCap.is_captain = false;
    }
    
    newCap.is_captain = true;
    newSquad.forEach((p: any) => p.multiplier = 1);
    const finalCap = newSquad.find((p: any) => p.is_captain);
    if (finalCap) finalCap.multiplier = 2;

    setData({ ...data, squad: newSquad });
  };

  const handleSetViceCaptain = (id: number) => {
    const newSquad = [...data.squad];
    const oldVice = newSquad.find((p: any) => p.is_vice_captain);
    const newVice = newSquad.find((p: any) => p.id === id);
    if (!newVice) return;

    if (newVice.is_captain) {
      newVice.is_captain = false;
      newVice.multiplier = 1;
      if (oldVice) {
        oldVice.is_captain = true;
        oldVice.multiplier = 2;
      }
    } else {
      if (oldVice) oldVice.is_vice_captain = false;
    }
    
    newVice.is_vice_captain = true;
    setData({ ...data, squad: newSquad });
  };

  const filteredRecs = transferRecs.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.team.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <main className={`min-h-screen font-sans pb-24 md:pb-0 transition-colors duration-300 ${bgMain}`} dir={isEnglish ? "ltr" : "rtl"}>
      
      {!data && !initLoading && (
        <div className="flex flex-col items-center justify-center min-h-screen bg-[#37003c] text-white relative">
          <button 
            onClick={() => setIsEnglish(!isEnglish)} 
            className="absolute top-4 right-4 text-sm font-bold px-4 py-2 rounded-lg border-2 border-white/30 text-white hover:bg-white/20 transition-all z-50"
          >
            {isEnglish ? 'עברית' : 'English'}
          </button>
          
          <div className="z-10 flex flex-col items-center w-full max-w-md px-4">
            <div className="mb-8 text-center">
              <h1 className="text-5xl md:text-6xl font-black mb-2 text-[#01fc7a] tracking-tight">FPL Elite Scout</h1>
              <p className="text-purple-200 font-medium text-lg">{isEnglish ? 'Next-Gen AI Squad Planner' : 'מערכת תכנון סגל מבוססת AI'}</p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-xl w-full text-[#37003c]" dir={isEnglish ? "ltr" : "rtl"}>
              <h2 className="text-xl font-bold mb-6 text-center text-[#37003c]">{t.enterId}</h2>
              <div className="flex flex-col gap-4">
                <input 
                  type="number" 
                  value={teamId} 
                  onChange={(e) => setTeamId(e.target.value)} 
                  placeholder={t.placeholder} 
                  className="w-full bg-gray-50 border border-gray-300 rounded-xl p-4 text-center text-2xl font-black focus:outline-none focus:ring-2 focus:ring-[#01fc7a] transition-all placeholder:text-gray-400 placeholder:text-lg placeholder:font-medium" 
                  onKeyDown={(e) => e.key === 'Enter' && fetchTeam()} 
                />
                <button 
                  onClick={() => fetchTeam()} 
                  disabled={loading || !teamId} 
                  className="w-full bg-[#01fc7a] hover:bg-[#00e36d] text-[#37003c] px-6 py-4 rounded-xl font-black text-lg shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
                >
                  {loading ? t.loading : (isEnglish ? 'Start Managing' : 'התחבר לקבוצה')}
                </button>
              </div>
              {error && <p className="text-red-400 mt-4 text-center font-bold bg-red-900/40 p-2 rounded-lg">{error}</p>}
            </div>
            
            {/* Rotating Tips */}
            <div className="mt-12 h-24 w-full flex flex-col items-center justify-center text-center px-4 opacity-80">
              <span className="text-2xl mb-2">{FPL_SUCCESS_TIPS[tipIndex]?.icon}</span>
              <p className="text-sm font-medium text-purple-200 max-w-sm">
                {isEnglish ? FPL_SUCCESS_TIPS[tipIndex]?.title_en : FPL_SUCCESS_TIPS[tipIndex]?.title_he}
              </p>
              <p className="text-xs text-white/60 mt-1 max-w-sm hidden md:block">
                {isEnglish ? FPL_SUCCESS_TIPS[tipIndex]?.desc_en : FPL_SUCCESS_TIPS[tipIndex]?.desc_he}
              </p>
            </div>
          </div>
        </div>
      )}
      
      {!data && initLoading && (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-green-900">
           <div className="animate-pulse text-white font-bold text-xl">{isEnglish ? 'Loading your squad...' : 'טוען את הקבוצה שלך...'}</div>
        </div>
      )}

      {data && (
        <div className="max-w-6xl mx-auto p-4 sm:p-6 pb-20">
          
          {/* Header Row */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
            <div className="flex gap-2 w-full md:w-auto">
              <button onClick={() => { setData(null); localStorage.removeItem('fpl_team_id'); }} className={`flex-1 md:flex-none px-6 py-2 border rounded-md text-sm font-medium hover:opacity-80 transition-opacity ${bgCard}`}>{t.changeTeam}</button>
              <button onClick={() => setIsEnglish(!isEnglish)} className={`flex-1 md:flex-none px-6 py-2 border rounded-md text-sm font-medium hover:opacity-80 transition-opacity ${bgCard}`}>{isEnglish ? 'עברית' : 'English'}</button>
              <button onClick={() => setIsDarkMode(!isDarkMode)} className={`flex-1 md:flex-none px-6 py-2 border rounded-md text-sm font-medium hover:opacity-80 transition-opacity ${bgCard}`}>{isDarkMode ? t.lightMode : t.darkMode}</button>
            </div>
            <div className={`w-full md:w-auto ${isEnglish ? 'text-left' : 'text-right'}`}>
              <h2 className={`text-2xl font-black ${textHighlight}`}>{data.team_name}</h2>
              <p className={`text-sm ${textMuted}`}>{t.engineFor} {data.next_gw} | {t.teamWord} {data.team_id}</p>
            </div>
          </div>

          {/* Metrics Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className={`border-2 border-red-300 rounded-xl p-4 flex flex-col justify-between ${bgBox} ${isEnglish ? 'items-start' : 'items-end'}`}>
              <p className={`text-xs font-bold ${textMuted}`}>{t.overallRank}</p>
              <p className="text-2xl font-black">{data.rank.toLocaleString()}</p>
            </div>
            <div className={`border-2 border-orange-300 rounded-xl p-4 flex flex-col justify-between ${bgBox} ${isEnglish ? 'items-start' : 'items-end'}`}>
              <p className={`text-xs font-bold ${textMuted}`}>{t.bank}</p>
              <p className="text-2xl font-black">£{data.bank.toFixed(1)}m</p>
            </div>
            <div className={`border-2 border-blue-300 rounded-xl p-4 flex flex-col justify-between ${bgBox} ${isEnglish ? 'items-start' : 'items-end'}`}>
              <p className={`text-xs font-bold ${textMuted}`}>{t.xp}</p>
              <p className="text-2xl font-black">{totalXP.toFixed(1)}</p>
            </div>
            <div className={`border-2 border-green-300 rounded-xl p-4 flex flex-col justify-between ${bgBox} ${isEnglish ? 'items-start' : 'items-end'}`}>
              <p className={`text-xs font-bold ${textMuted}`}>{t.squadScore}</p>
              <p className="text-2xl font-black">{calculatedSquadScore || 0} <span className={`text-sm ${textMuted}`}>/ 100</span></p>
            </div>
          </div>

          {/* Timer Box */}
          <div className={`border border-green-400 rounded-xl p-4 mb-8 flex flex-col items-center justify-center ${bgBox}`}>
            <p className={`text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{t.timeUntil} (GW {data.next_gw})</p>
            <p className="text-xl font-bold text-green-600">2d 8h 54m 46s</p>
          </div>

          {/* Tabs Menu */}
          <div className="hidden md:flex overflow-x-auto gap-6 border-b border-gray-200 mb-6 pb-2 text-sm font-bold whitespace-nowrap scrollbar-hide">
            <button onClick={() => setActiveTab('pitch')} className={`${activeTab === 'pitch' ? `${textHighlight} border-b-2 border-red-500` : `${textMuted} hover:opacity-80`}`}>{t.pitchTab}</button>
            <button onClick={() => setActiveTab('transfer')} className={`${activeTab === 'transfer' ? `${textHighlight} border-b-2 border-red-500` : `${textMuted} hover:opacity-80`}`}>{t.transferTab}</button>
            <button onClick={() => setActiveTab('analysis')} className={`${activeTab === 'analysis' ? `${textHighlight} border-b-2 border-red-500` : `${textMuted} hover:opacity-80`}`}>{t.analysisTab}</button>
            <button onClick={() => setActiveTab('radar')} className={`${activeTab === 'radar' ? `${textHighlight} border-b-2 border-red-500` : `${textMuted} hover:opacity-80`}`}>{t.radarTab}</button>
            <button onClick={() => setActiveTab('budget')} className={`${activeTab === 'budget' ? `${textHighlight} border-b-2 border-red-500` : `${textMuted} hover:opacity-80`}`}>{t.budgetTab}</button>
            <button onClick={() => setActiveTab('planner')} className={`${activeTab === 'planner' ? `${textHighlight} border-b-2 border-red-500` : `${textMuted} hover:opacity-80`}`}>{t.plannerTab}</button>
            <button onClick={() => setActiveTab('leagues')} className={`${activeTab === 'leagues' ? `${textHighlight} border-b-2 border-red-500` : `${textMuted} hover:opacity-80`}`}>{t.leaguesTab}</button>
            <button onClick={() => setActiveTab('tips')} className={`${activeTab === 'tips' ? `${textHighlight} border-b-2 border-red-500` : `${textMuted} hover:opacity-80`}`}>{t.tipsTab}</button>
          </div>

          {/* Captain / VC Selectors & Reset Squad */}
          {activeTab === 'pitch' && (
            <div className="flex flex-col md:flex-row gap-4 md:gap-8 mb-6 items-end">
              <div className="flex-1 w-full">
                <label className={`block text-xs font-bold mb-0 sm:mb-1 ${textMuted} ${isEnglish ? 'text-left' : 'text-right'}`}>{t.cap}</label>
                <select 
                  className={`w-full border rounded-md p-2 text-sm ${bgCard}`}
                  value={currentCaptain?.id || ''}
                  onChange={(e) => handleSetCaptain(Number(e.target.value))}
                >
                  {data.squad.map((p: any) => <option key={p.id} value={p.id}>{p.name} ({p.team}) — xP: {p.xp}</option>)}
                </select>
              </div>
              <div className="flex-1 w-full">
                <label className={`block text-xs font-bold mb-0 sm:mb-1 ${textMuted} ${isEnglish ? 'text-left' : 'text-right'}`}>{t.vcap}</label>
                <select 
                  className={`w-full border rounded-md p-2 text-sm ${bgCard}`}
                  value={currentVice?.id || ''}
                  onChange={(e) => handleSetViceCaptain(Number(e.target.value))}
                >
                  {data.squad.map((p: any) => <option key={p.id} value={p.id}>{p.name} ({p.team}) — xP: {p.xp}</option>)}
                </select>
              </div>
              <div className="flex-none">
                <button onClick={() => fetchTeam()} className={`w-full md:w-auto px-6 py-2 border rounded-md text-sm font-bold hover:opacity-80 transition-opacity text-white bg-red-600 border-red-700 shadow-md`}>
                  {isEnglish ? '🔄 Reset Virtual Changes' : '🔄 איפוס סגל וחילופים'}
                </button>
              </div>
            </div>
          )}
          {/* FPL Pitch Area */}
          {activeTab === 'pitch' && (
            <div className="max-w-4xl mx-auto">
              <div className="bg-[#126b3f] rounded-t-lg p-1 md:p-4 relative shadow-md overflow-hidden min-h-[360px] md:min-h-[500px] flex flex-col justify-around">
                <div className="absolute inset-0 opacity-20 pointer-events-none overflow-hidden">
                  {/* Center Line & Circle */}
                  <div className="absolute top-1/2 left-0 right-0 h-1 bg-white"></div>
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 border-4 border-white rounded-full"></div>
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full"></div>
                  
                  {/* Top Penalty Area */}
                  <div className="absolute top-0 left-1/4 right-1/4 h-32 border-4 border-t-0 border-white"></div>
                  <div className="absolute top-0 left-[35%] right-[35%] h-12 border-4 border-t-0 border-white"></div>
                  <div className="absolute top-[8rem] left-1/2 -translate-x-1/2 w-20 h-10 border-4 border-transparent border-b-white rounded-full"></div>
                  
                  {/* Bottom Penalty Area */}
                  <div className="absolute bottom-0 left-1/4 right-1/4 h-32 border-4 border-b-0 border-white"></div>
                  <div className="absolute bottom-0 left-[35%] right-[35%] h-12 border-4 border-b-0 border-white"></div>
                  <div className="absolute bottom-[8rem] left-1/2 -translate-x-1/2 w-20 h-10 border-4 border-transparent border-t-white rounded-full"></div>
                </div>
                
                <div className="flex justify-center z-10">
                  {starters.filter((p: any) => p.pos_code === 1).map((p: any) => (
                    <PlayerCard key={p.id} player={p} activeId={swapSourceId} onActionClick={handleSwapClick} />
                  ))}
                </div>
                <div className="flex justify-center gap-0 sm:gap-6 z-10 mt-3 sm:mt-6">
                  {starters.filter((p: any) => p.pos_code === 2).map((p: any) => (
                    <PlayerCard key={p.id} player={p} activeId={swapSourceId} onActionClick={handleSwapClick} />
                  ))}
                </div>
                <div className="flex justify-center gap-0 sm:gap-6 z-10 mt-3 sm:mt-6">
                  {starters.filter((p: any) => p.pos_code === 3).map((p: any) => (
                    <PlayerCard key={p.id} player={p} activeId={swapSourceId} onActionClick={handleSwapClick} />
                  ))}
                </div>
                <div className="flex justify-center gap-0 sm:gap-6 z-10 mt-3 sm:mt-6">
                  {starters.filter((p: any) => p.pos_code === 4).map((p: any) => (
                    <PlayerCard key={p.id} player={p} activeId={swapSourceId} onActionClick={handleSwapClick} />
                  ))}
                </div>
              </div>
              
              <div className="bg-[#0e5230] rounded-b-lg p-1 md:p-4 flex justify-center gap-0 sm:gap-6 shadow-md z-20 relative border-t-2 border-white/20 border-dashed">
                {bench.sort((a: any, b: any) => a.position - b.position).map((p: any) => (
                  <PlayerCard key={p.id} player={p} isBench activeId={swapSourceId} onActionClick={handleSwapClick} />
                ))}
              </div>
            </div>
          )}

          {activeTab === 'transfer' && (
            <div className={`mt-4 p-3 md:p-6 rounded-2xl shadow-sm border ${bgCard}`}>
              
              <div className="flex flex-col lg:flex-row gap-8">
                {/* Left Side (or Right in RTL) - Pitch for selecting player */}
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-4">
                    <h4 className={`text-lg font-bold ${textHighlight}`}>
                      {transferOutId ? (isEnglish ? 'Select replacement below' : 'בחר מחליף למטה') : (isEnglish ? 'Select player to sell' : 'בחר שחקן למכירה')}
                    </h4>
                    {transferOutId && (
                      <button 
                        onClick={() => { setTransferOutId(null); setTransferRecs([]); setSearchQuery(''); }} 
                        className={`px-4 py-2 border rounded-md text-sm font-bold hover:opacity-80 ${bgCard}`}
                      >
                        {isEnglish ? 'Cancel' : 'ביטול'}
                      </button>
                    )}
                  </div>

                  <div className="bg-[#126b3f] rounded-lg p-2 sm:p-4 relative shadow-inner min-h-[400px] flex flex-col justify-around border-4 border-purple-500/50 overflow-hidden">
                    <div className="absolute inset-0 opacity-20 pointer-events-none">
                      <div className="absolute top-1/2 left-0 right-0 h-1 bg-white"></div>
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 border-4 border-white rounded-full"></div>
                      <div className="absolute top-0 left-1/4 right-1/4 h-24 border-4 border-t-0 border-white"></div>
                      <div className="absolute bottom-0 left-1/4 right-1/4 h-24 border-4 border-b-0 border-white"></div>
                    </div>
                    <div className="flex justify-center z-10">
                      {starters.filter((p: any) => p.pos_code === 1).map((p: any) => (
                        <PlayerCard key={p.id} player={p} activeId={transferOutId} onActionClick={handlePlayerClick} transferMode />
                      ))}
                    </div>
                    <div className="flex justify-center gap-2 sm:gap-4 z-10 mt-4">
                      {starters.filter((p: any) => p.pos_code === 2).map((p: any) => (
                        <PlayerCard key={p.id} player={p} activeId={transferOutId} onActionClick={handlePlayerClick} transferMode />
                      ))}
                    </div>
                    <div className="flex justify-center gap-2 sm:gap-4 z-10 mt-4">
                      {starters.filter((p: any) => p.pos_code === 3).map((p: any) => (
                        <PlayerCard key={p.id} player={p} activeId={transferOutId} onActionClick={handlePlayerClick} transferMode />
                      ))}
                    </div>
                    <div className="flex justify-center gap-2 sm:gap-4 z-10 mt-4">
                      {starters.filter((p: any) => p.pos_code === 4).map((p: any) => (
                        <PlayerCard key={p.id} player={p} activeId={transferOutId} onActionClick={handlePlayerClick} transferMode />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Side - Recommendations */}
                {transferOutId ? (
                  <div className={`flex-1 p-4 rounded-xl border ${bgBox} shadow-lg border-t-4 border-t-purple-500 flex flex-col`}>
                    <h3 className={`text-xl font-black mb-4 flex items-center gap-2 ${textHighlight}`}>
                      <span>🧪</span> {isEnglish ? 'Transfer Lab' : 'מעבדת העברות'}
                    </h3>
                    
                    {transferError && (
                      <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 mb-4 rounded shadow-sm font-bold text-sm">
                        ⚠️ {transferError}
                      </div>
                    )}

                    {loadingRecs ? (
                      <p className={`font-bold animate-pulse ${textMuted}`}>{isEnglish ? 'Calculating smart alternatives...' : 'מחשב אלטרנטיבות חכמות...'}</p>
                    ) : (
                      <div className="flex flex-col h-full">
                        
                        {/* Top 3 AI Recs */}
                        {searchQuery === '' && transferRecs.length > 0 && (
                          <div className="mb-6">
                            <h4 className={`text-sm font-bold mb-3 ${textMuted}`}>
                              {isEnglish ? 'Top 3 AI Recommendations:' : '3 ההמלצות המובילות של המערכת (לפי xP):'}
                            </h4>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                              {transferRecs.slice(0, 3).map((rec, idx) => (
                                <button 
                                  key={rec.id} 
                                  onClick={() => executeTransfer(rec)}
                                  className={`w-full text-center p-3 rounded-xl border flex flex-col items-center gap-2 hover:border-purple-500 transition-colors group ${isDarkMode ? 'bg-gray-800 border-gray-700 hover:bg-gray-700' : 'bg-purple-50/50 border-purple-100 hover:bg-purple-50'}`}
                                >
                                  <div className="bg-purple-600 text-white w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shadow-sm group-hover:scale-110 transition-transform">
                                    {idx + 1}
                                  </div>
                                  <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${rec.team_code}-66.webp`} className="w-10" />
                                  <div className="w-full">
                                    <p className={`font-black text-sm truncate ${textHighlight}`}>{rec.name}</p>
                                    <p className={`text-xs font-bold ${textMuted}`}>{rec.team}</p>
                                  </div>
                                  <div className={`w-full text-xs font-bold px-2 py-1 rounded flex justify-between ${isDarkMode ? 'bg-gray-900' : 'bg-white shadow-sm'}`}>
                                    <span className={textHighlight}>£{rec.cost.toFixed(1)}</span>
                                    <span className="text-emerald-500">{rec.xp.toFixed(1)} XP</span>
                                  </div>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Search */}
                        <div className="mb-4">
                          <input 
                            type="text" 
                            placeholder={isEnglish ? "Search by name or team..." : "חפש שחקן לפי שם או קבוצה..."} 
                            value={searchQuery}
                            onChange={(e) => { setSearchQuery(e.target.value); setTransferError(''); }}
                            className={`w-full border rounded-lg p-2 focus:outline-none focus:border-purple-500 ${bgCard}`}
                          />
                        </div>

                        {/* Full Table */}
                        <div className={`flex-1 max-h-[400px] overflow-y-auto rounded-lg border ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                          <table className={`w-full text-sm ${isEnglish ? 'text-left' : 'text-right'}`}>
                            <thead className={`sticky top-0 z-10 text-xs uppercase font-bold ${isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'}`}>
                              <tr>
                                <th className="px-3 py-2">{isEnglish ? 'Player' : 'שחקן'}</th>
                                <th className="px-3 py-2 text-center">{isEnglish ? 'Team' : 'קבוצה'}</th>
                                <th className="px-3 py-2 text-center">{isEnglish ? 'Price' : 'מחיר'}</th>
                                <th className="px-3 py-2 text-center">{isEnglish ? 'Points' : 'נקודות'}</th>
                                <th className="px-3 py-2 text-center">xP</th>
                                <th className="px-3 py-2 text-center"></th>
                              </tr>
                            </thead>
                            <tbody>
                              {[...(searchQuery === '' ? transferRecs.slice(3) : filteredRecs)].sort((a, b) => b.total_points - a.total_points).map(rec => (
                                <tr key={rec.id} className={`border-b last:border-0 ${isDarkMode ? 'border-gray-700 hover:bg-gray-700/50' : 'border-gray-200 hover:bg-gray-50'}`}>
                                  <td className="px-3 py-2 font-bold flex items-center gap-2">
                                    <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${rec.team_code}-66.webp`} className="w-6 h-auto" />
                                    <span className={textHighlight}>{rec.name}</span>
                                  </td>
                                  <td className={`px-3 py-2 text-center text-xs font-bold ${textMuted}`}>{rec.team}</td>
                                  <td className={`px-3 py-2 text-center font-bold ${textHighlight}`}>£{rec.cost.toFixed(1)}</td>
                                  <td className={`px-3 py-2 text-center font-bold text-blue-500`}>{rec.total_points}</td>
                                  <td className="px-3 py-2 text-center text-emerald-500 font-bold">{rec.xp.toFixed(1)}</td>
                                  <td className="px-3 py-2 text-center">
                                    <button 
                                      onClick={() => executeTransfer(rec)} 
                                      className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-xs font-bold transition-colors"
                                    >
                                      {isEnglish ? 'Select' : 'בחר'}
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {filteredRecs.length === 0 && (
                            <p className="text-red-500 font-bold p-4 text-center">
                              {isEnglish ? 'No matching players found in your budget.' : 'לא נמצאו שחקנים מתאימים בתקציב שלך.'}
                            </p>
                          )}
                        </div>

                      </div>
                    )}
                  </div>
                ) : (
                  <div className={`flex-1 p-8 rounded-xl border flex flex-col items-center justify-center text-center ${bgBox}`}>
                    <div className="text-6xl mb-4 opacity-50">💸</div>
                    <h3 className={`text-xl font-black mb-2 ${textHighlight}`}>
                      {isEnglish ? 'Ready to make a transfer?' : 'מוכן לבצע העברה?'}
                    </h3>
                    <p className={textMuted}>
                      {isEnglish ? 'Select a player from the pitch to see AI recommendations and search for replacements.' : 'בחר שחקן מהמגרש כדי לראות המלצות חכמות ולחפש לו מחליפים.'}
                    </p>
                  </div>
                )}
              </div>

            </div>
          )}

          {activeTab === 'analysis' && (
            <div className={`mt-4 p-3 md:p-6 rounded-2xl shadow-sm border ${bgCard}`}>
              <h3 className={`text-2xl font-black mb-6 flex items-center gap-2 ${textHighlight}`}>
                <span>📊</span> {isEnglish ? 'Squad Analysis & AI Insights' : 'ניתוח סגל ותובנות AI'}
              </h3>
              
              <SquadAnalysisTab data={data} isEnglish={isEnglish} isDarkMode={isDarkMode} textMuted={textMuted} textHighlight={textHighlight} bgBox={bgBox} />
            </div>
          )}

          {activeTab === 'radar' && (
            <div className={`mt-4 p-3 md:p-6 rounded-2xl shadow-sm border ${bgCard}`}>
              <h3 className={`text-2xl font-black mb-6 flex items-center gap-2 ${textHighlight}`}>
                <span>📡</span> {isEnglish ? 'Elite Transfer Radar' : 'רדאר רכש עילית'}
              </h3>
              <EliteRadarTab isEnglish={isEnglish} isDarkMode={isDarkMode} textMuted={textMuted} textHighlight={textHighlight} bgBox={bgBox} />
            </div>
          )}
          {activeTab === 'budget' && (
            <div className={`mt-4 p-3 md:p-6 rounded-2xl shadow-sm border ${bgCard}`}>
              <h3 className={`text-2xl font-black mb-6 flex items-center gap-2 ${textHighlight}`}>
                <span>💰</span> {isEnglish ? 'Budget Scenarios' : 'תרחישי תקציב (המלצות מבוססות AI)'}
              </h3>
              <BudgetScenariosTab teamId={data.team_id} isEnglish={isEnglish} isDarkMode={isDarkMode} textMuted={textMuted} textHighlight={textHighlight} bgBox={bgBox} onTransfer={executeVirtualTransfer} />
            </div>
          )}

          {activeTab === 'planner' && (
            <div className={`mt-4 p-3 md:p-6 rounded-2xl shadow-sm border ${bgCard} relative`}>
              <h3 className={`text-2xl font-black mb-6 flex items-center gap-2 ${textHighlight}`}>
                <span>🗓️</span> {isEnglish ? 'Gameweek Planner' : 'מתכנן מחזורים'}
              </h3>
              <GWPlannerTab 
                data={data} 
                isEnglish={isEnglish} 
                isDarkMode={isDarkMode} 
                textMuted={textMuted} 
                textHighlight={textHighlight} 
                bgBox={bgBox} 
                onSwap={handleSwapClick}
                onCaptain={handleCaptainClick}
                onVice={handleViceClick}
                onReset={handleReset}
                originalData={originalData}
                onRestorePlayer={handleRestorePlayer}
                swapSourceId={swapSourceId} 
                onSell={(id: number) => {
                  setTransferOutId(id);
                  const playerToSell = data.squad.find((p: any) => p.id === id);
                  if (playerToSell) {
                    setLoadingRecs(true);
                    const budget = data.bank + playerToSell.cost;
                    const currentSquadIds = data.squad.map((p: any) => p.id);
                    fetch(`${API_BASE_URL}/api/transfer-lab`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ pos_code: playerToSell.pos_code, max_budget: budget, current_squad_ids: currentSquadIds })
                    }).then(res => res.json()).then(recs => {
                      setTransferRecs(recs);
                    }).catch(err => {
                      console.error("Failed to fetch recs", err);
                    }).finally(() => {
                      setLoadingRecs(false);
                    });
                  }
                }}
              />
              
              {/* Transfer Lab Modal in Planner */}
              {transferOutId && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                  <div className={`w-full max-w-4xl max-h-[90vh] overflow-hidden p-6 rounded-2xl shadow-2xl flex flex-col ${isDarkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white'}`}>
                    <div className="flex justify-between items-center mb-4">
                      <h3 className={`text-2xl font-black flex items-center gap-2 ${textHighlight}`}>
                        <span>🧪</span> {isEnglish ? 'Transfer Lab (Planner Mode)' : 'מעבדת העברות (מצב מתכנן)'}
                      </h3>
                      <button 
                        onClick={() => { setTransferOutId(null); setTransferRecs([]); setSearchQuery(''); }}
                        className={`text-gray-500 hover:text-gray-800 ${isDarkMode ? 'hover:text-white' : ''}`}
                      >
                        ✕
                      </button>
                    </div>
                    
                    {transferError && (
                      <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 mb-4 rounded shadow-sm font-bold text-sm">
                        ⚠️ {transferError}
                      </div>
                    )}

                    {loadingRecs ? (
                      <p className={`font-bold animate-pulse ${textMuted}`}>{isEnglish ? 'Calculating smart alternatives...' : 'מחשב אלטרנטיבות חכמות...'}</p>
                    ) : (
                      <div className="flex flex-col h-full overflow-hidden">
                        
                        {/* Top 3 AI Recs */}
                        {searchQuery === '' && transferRecs.length > 0 && (
                          <div className="mb-6 shrink-0">
                            <h4 className={`text-sm font-bold mb-3 ${textMuted}`}>
                              {isEnglish ? 'Top 3 AI Recommendations:' : '3 ההמלצות המובילות של המערכת (לפי xP):'}
                            </h4>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                              {transferRecs.slice(0, 3).map((rec, idx) => (
                                <button 
                                  key={rec.id} 
                                  onClick={() => { executeTransfer(rec); setActiveTab('planner'); }}
                                  className={`w-full text-center p-3 rounded-xl border flex flex-col items-center gap-2 hover:border-purple-500 transition-colors group ${isDarkMode ? 'bg-gray-800 border-gray-700 hover:bg-gray-700' : 'bg-purple-50/50 border-purple-100 hover:bg-purple-50'}`}
                                >
                                  <div className="bg-purple-600 text-white w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shadow-sm group-hover:scale-110 transition-transform">
                                    {idx + 1}
                                  </div>
                                  <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${rec.team_code}-66.webp`} className="w-10" />
                                  <div className="w-full">
                                    <p className={`font-black text-sm truncate ${textHighlight}`}>{rec.name}</p>
                                    <p className={`text-xs font-bold ${textMuted}`}>{rec.team}</p>
                                  </div>
                                  <div className={`w-full text-xs font-bold px-2 py-1 rounded flex justify-between ${isDarkMode ? 'bg-gray-900' : 'bg-white shadow-sm'}`}>
                                    <span className={textHighlight}>£{rec.cost.toFixed(1)}</span>
                                    <span className="text-emerald-500">{rec.xp.toFixed(1)} XP</span>
                                  </div>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Search */}
                        <div className="mb-4 shrink-0">
                          <input 
                            type="text" 
                            placeholder={isEnglish ? "Search by name or team..." : "חפש שחקן לפי שם או קבוצה..."} 
                            value={searchQuery}
                            onChange={(e) => { setSearchQuery(e.target.value); setTransferError(''); }}
                            className={`w-full border rounded-lg p-2 focus:outline-none focus:border-purple-500 ${bgCard}`}
                          />
                        </div>

                        {/* Full Table */}
                        <div className={`flex-1 overflow-y-auto rounded-lg border min-h-[200px] ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                          <table className={`w-full text-sm ${isEnglish ? 'text-left' : 'text-right'}`}>
                            <thead className={`sticky top-0 z-10 text-xs uppercase font-bold ${isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'}`}>
                              <tr>
                                <th className="px-3 py-2">{isEnglish ? 'Player' : 'שחקן'}</th>
                                <th className="px-3 py-2 text-center">{isEnglish ? 'Team' : 'קבוצה'}</th>
                                <th className="px-3 py-2 text-center">{isEnglish ? 'Price' : 'מחיר'}</th>
                                <th className="px-3 py-2 text-center">{isEnglish ? 'Points' : 'נקודות'}</th>
                                <th className="px-3 py-2 text-center">xP</th>
                                <th className="px-3 py-2 text-center"></th>
                              </tr>
                            </thead>
                            <tbody>
                              {[...(searchQuery === '' ? transferRecs.slice(3) : filteredRecs)].sort((a, b) => b.total_points - a.total_points).map(rec => (
                                <tr key={rec.id} className={`border-b last:border-0 ${isDarkMode ? 'border-gray-700 hover:bg-gray-700/50' : 'border-gray-200 hover:bg-gray-50'}`}>
                                  <td className="px-3 py-2 font-bold flex items-center gap-2">
                                    <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${rec.team_code}-66.webp`} className="w-6 h-auto" />
                                    <span className={textHighlight}>{rec.name}</span>
                                  </td>
                                  <td className={`px-3 py-2 text-center text-xs font-bold ${textMuted}`}>{rec.team}</td>
                                  <td className={`px-3 py-2 text-center font-bold ${textHighlight}`}>£{rec.cost.toFixed(1)}</td>
                                  <td className={`px-3 py-2 text-center font-bold text-blue-500`}>{rec.total_points}</td>
                                  <td className="px-3 py-2 text-center text-emerald-500 font-bold">{rec.xp.toFixed(1)}</td>
                                  <td className="px-3 py-2 text-center">
                                    <button 
                                      onClick={() => { executeTransfer(rec); setActiveTab('planner'); }} 
                                      className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-xs font-bold transition-colors"
                                    >
                                      {isEnglish ? 'Select' : 'בחר'}
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {filteredRecs.length === 0 && (
                            <p className="text-red-500 font-bold p-4 text-center">
                              {isEnglish ? 'No matching players found in your budget.' : 'לא נמצאו שחקנים מתאימים בתקציב שלך.'}
                            </p>
                          )}
                        </div>

                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* App Alert Modal */}
      {appAlert && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4">
          <div className={`w-full max-w-sm overflow-hidden p-6 rounded-2xl shadow-2xl flex flex-col items-center text-center ${isDarkMode ? 'bg-gray-800 border border-gray-700 text-white' : 'bg-white text-gray-900'}`}>
            <div className="text-4xl mb-4">⚠️</div>
            <p className="font-bold mb-6">{appAlert}</p>
            <button 
              onClick={() => setAppAlert(null)}
              className="bg-purple-600 hover:bg-purple-700 text-white font-black py-2 px-8 rounded-xl shadow-md transition-colors"
            >
              {isEnglish ? 'OK' : 'הבנתי'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'leagues' && (
        <div className={`mt-4 p-3 md:p-6 rounded-2xl shadow-sm border ${bgCard} relative`}>
          <h3 className={`text-2xl font-black mb-6 flex items-center gap-2 ${textHighlight}`}>
            <span>🏆</span> {isEnglish ? 'Mini-Leagues & H2H' : 'מיני-ליגות והשוואת ראש בראש'}
          </h3>
          <LeaguesTab 
            data={data} 
            isEnglish={isEnglish} 
            isDarkMode={isDarkMode} 
            textMuted={textMuted} 
            textHighlight={textHighlight} 
            bgBox={bgBox} 
          />
        </div>
      )}

      {activeTab === 'tips' && (
        <div className={`mt-4 relative`}>
          <TipsTab 
            isEnglish={isEnglish} 
            isDarkMode={isDarkMode} 
            textMuted={textMuted} 
            textHighlight={textHighlight} 
            bgBox={bgBox} 
          />
        </div>
      )}

      {/* Mobile Bottom Navigation */}
      {data && (
        <div className="md:hidden fixed bottom-0 left-0 right-0 bg-[#37003c] z-[100] flex overflow-x-auto scrollbar-hide shadow-[0_-10px_20px_-5px_rgba(0,0,0,0.3)]">
          {[
            { id: 'pitch', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="18" rx="2" ry="2"></rect><line x1="2" y1="12" x2="22" y2="12"></line><circle cx="12" cy="12" r="3"></circle></svg>, nameEn: 'Pitch', nameHe: 'מגרש' },
            { id: 'transfer', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 1l4 4-4 4"></path><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><path d="M7 23l-4-4 4-4"></path><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg>, nameEn: 'Transfers', nameHe: 'העברות' },
            { id: 'planner', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>, nameEn: 'Planner', nameHe: 'תכנון' },
            { id: 'analysis', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>, nameEn: 'Analysis', nameHe: 'ניתוח' },
            { id: 'radar', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>, nameEn: 'Radar', nameHe: 'ראדאר' },
            { id: 'budget', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>, nameEn: 'Budget', nameHe: 'תקציב' },
            { id: 'leagues', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"></path></svg>, nameEn: 'Leagues', nameHe: 'ליגות' },
            { id: 'tips', icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"></path></svg>, nameEn: 'Tips', nameHe: 'טיפים' }
          ].map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id as any)} className={`flex-shrink-0 flex flex-col items-center justify-center w-[72px] py-3 gap-1.5 transition-colors ${activeTab === tab.id ? 'text-[#01fc7a]' : 'text-purple-200/70'}`}>
              <div className={`transition-transform duration-300 ${activeTab === tab.id ? 'scale-110 drop-shadow-[0_0_8px_rgba(1,252,122,0.5)]' : ''}`}>{tab.icon}</div>
              <span className={`text-[10px] tracking-wide ${activeTab === tab.id ? 'font-bold' : 'font-medium'}`}>{isEnglish ? tab.nameEn : tab.nameHe}</span>
            </button>
          ))}
        </div>
      )}
    </main>

  );
}

function SquadAnalysisTab({ data, isEnglish, isDarkMode, textMuted, textHighlight, bgBox }: any) {
  const _starters = data.squad.filter((p: any) => p.position <= 11);
  const _bench = data.squad.filter((p: any) => p.position > 11);
  
  const hardFixtures = _starters.filter((p: any) => p.fixture_diff >= 4);
  const lowXp = _starters.filter((p: any) => p.xp < 2.5);
  const highestXpPlayer = [..._starters].sort((a: any, b: any) => b.xp - a.xp)[0];
  const _currentCap = _starters.find((p: any) => p.is_captain);
  const capSuboptimal = _currentCap && highestXpPlayer && _currentCap.id !== highestXpPlayer.id && (highestXpPlayer.xp - _currentCap.xp > 0.5);

  const teamCounts = data.squad.reduce((acc: any, p: any) => {
    acc[p.team] = (acc[p.team] || 0) + 1;
    return acc;
  }, {});
  const maxedTeams = Object.keys(teamCounts).filter(t => teamCounts[t] >= 3);

  const innerBoxBg = isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-100 border-gray-200';
  const tableHeaderBg = isDarkMode ? 'bg-gray-800' : 'bg-gray-100';

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
      <div className={`p-5 rounded-xl border ${bgBox}`}>
        <h4 className="text-lg font-bold mb-4 flex items-center gap-2 text-red-500">
          <span>⚠️</span> {isEnglish ? 'Urgent Weaknesses' : 'נקודות תורפה דחופות (בהרכב)'}
        </h4>
        <ul className="space-y-4">
          {hardFixtures.length > 0 && (
            <li className={`flex flex-col p-3 rounded-lg border ${isDarkMode ? 'bg-red-900/30 border-red-900/50' : 'bg-red-50 border-red-100'}`}>
              <span className={`font-bold text-sm ${isDarkMode ? 'text-red-400' : 'text-red-700'}`}>{isEnglish ? 'Hard Fixtures (FDR 4+)' : 'משחקים קשים קרובים (FDR 4+)'}</span>
              <span className={`text-xs mt-1 ${textMuted}`}>{hardFixtures.map((p:any) => p.name).join(', ')}</span>
            </li>
          )}
          {lowXp.length > 0 && (
            <li className={`flex flex-col p-3 rounded-lg border ${isDarkMode ? 'bg-orange-900/30 border-orange-900/50' : 'bg-orange-50 border-orange-100'}`}>
              <span className={`font-bold text-sm ${isDarkMode ? 'text-orange-400' : 'text-orange-700'}`}>{isEnglish ? 'Low Expected Points (< 2.5 xP)' : 'תוחלת נקודות נמוכה למחזור הקרוב (< 2.5 xP)'}</span>
              <span className={`text-xs mt-1 ${textMuted}`}>{lowXp.map((p:any) => p.name).join(', ')}</span>
            </li>
          )}
          {capSuboptimal && (
            <li className={`flex flex-col p-3 rounded-lg border ${isDarkMode ? 'bg-yellow-900/30 border-yellow-900/50' : 'bg-yellow-50 border-yellow-100'}`}>
              <span className={`font-bold text-sm ${isDarkMode ? 'text-yellow-500' : 'text-yellow-700'}`}>{isEnglish ? 'Suboptimal Captain?' : 'קפטן לא אופטימלי?'}</span>
              <span className={`text-xs mt-1 ${textMuted}`}>
                {isEnglish 
                  ? `${_currentCap?.name} has ${_currentCap?.xp} xP, but ${highestXpPlayer?.name} is projected for ${highestXpPlayer?.xp} xP.` 
                  : `${_currentCap?.name} עם ${_currentCap?.xp} נק', אבל ל-${highestXpPlayer?.name} יש תוחלת של ${highestXpPlayer?.xp} נק'.`}
              </span>
            </li>
          )}
          {hardFixtures.length === 0 && lowXp.length === 0 && !capSuboptimal && (
            <div className="flex flex-col items-center justify-center p-6 text-center">
              <span className="text-4xl mb-2">🛡️</span>
              <span className="text-emerald-500 font-bold">{isEnglish ? 'Your squad looks rock solid! 💪' : 'הסגל שלך נראה חזק, יציב ומוכן למחזור! 💪'}</span>
            </div>
          )}
        </ul>
      </div>

      <div className={`p-5 rounded-xl border ${bgBox}`}>
        <h4 className={`text-lg font-bold mb-4 flex items-center gap-2 ${textHighlight}`}>
          <span>🏗️</span> {isEnglish ? 'Squad Structure & Budget' : 'מבנה הסגל וניהול תקציב'}
        </h4>
        <div className="space-y-6">
          <div className="flex gap-4">
            <div className={`flex-1 p-3 rounded-lg border ${innerBoxBg}`}>
              <span className={`block text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Squad Value' : 'שווי הסגל (ללא בנק)'}</span>
              <span className={`text-lg font-black ${textHighlight}`}>£{data.squad.reduce((s:any,p:any)=>s+p.cost,0).toFixed(1)}M</span>
            </div>
            <div className={`flex-1 p-3 rounded-lg border ${innerBoxBg}`}>
              <span className={`block text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Bench Value' : 'שווי הספסל'}</span>
              <span className={`text-lg font-black ${textHighlight}`}>£{_bench.reduce((sum:number, p:any) => sum + p.cost, 0).toFixed(1)}M</span>
            </div>
          </div>
          <div>
            <span className="font-bold text-sm block mb-0 sm:mb-1">{isEnglish ? 'Bench Budget Efficiency' : 'ניצולת תקציב הספסל:'}</span>
            <div className={`w-full rounded-full h-2.5 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'} mb-0 sm:mb-1`}>
              <div className={`${_bench.reduce((sum:number, p:any) => sum + p.cost, 0) > 19.0 ? 'bg-red-500' : 'bg-blue-500'} h-2.5 rounded-full transition-all`} style={{ width: `${Math.min(100, (_bench.reduce((sum:number, p:any) => sum + p.cost, 0) / 20) * 100)}%` }}></div>
            </div>
            <p className={`text-xs mt-2 ${textMuted}`}>
              {isEnglish 
                 ? 'An optimal (cheapest) bench costs £17.0M. The colored bar shows how much you spent up to a £20M benchmark. Over £19.0M is inefficient (turns red).' 
                 : 'ספסל אופטימלי (הכי זול שאפשר) עולה £17.0M. הפס המלא מציג חריגה של עד £20.0M. אם עברת את ה-£19.0M הפס יצבע באדום (בזבוז תקציב על שחקנים שלא פותחים).'}
            </p>
          </div>
          
          <div className={`pt-4 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <span className="font-bold text-sm block mb-3">{isEnglish ? 'Positional Spending:' : 'פיזור התקציב שלך לפי עמדות:'}</span>
            <div className="flex gap-1 h-6 rounded-lg overflow-hidden text-xs text-white font-bold text-center">
              <div style={{width: `${(data.squad.filter((p:any) => p.pos_code === 1).reduce((s:number,p:any)=>s+p.cost,0)/100)*100}%`}} className="bg-yellow-500 flex items-center justify-center" title="GK">GK</div>
              <div style={{width: `${(data.squad.filter((p:any) => p.pos_code === 2).reduce((s:number,p:any)=>s+p.cost,0)/100)*100}%`}} className="bg-blue-500 flex items-center justify-center" title="DEF">DEF</div>
              <div style={{width: `${(data.squad.filter((p:any) => p.pos_code === 3).reduce((s:number,p:any)=>s+p.cost,0)/100)*100}%`}} className="bg-green-500 flex items-center justify-center" title="MID">MID</div>
              <div style={{width: `${(data.squad.filter((p:any) => p.pos_code === 4).reduce((s:number,p:any)=>s+p.cost,0)/100)*100}%`}} className="bg-red-500 flex items-center justify-center" title="FWD">FWD</div>
            </div>
          </div>

          {maxedTeams.length > 0 && (
            <div className={`pt-4 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
              <span className="font-bold text-sm block mb-2">{isEnglish ? 'Maxed Teams (3 players):' : 'קבוצות במקסימום (חוסמות העברות):'}</span>
              <div className="flex gap-2 flex-wrap">
                {maxedTeams.map(t => (
                  <span key={t} className={`px-3 py-1 rounded-full text-xs font-bold border shadow-sm ${isDarkMode ? 'bg-purple-900/50 text-purple-200 border-purple-800' : 'bg-purple-100 text-purple-800 border-purple-200'}`}>{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className={`col-span-1 md:col-span-2 p-5 rounded-xl border ${bgBox} overflow-x-auto`}>
        <h4 className={`text-lg font-bold mb-4 flex items-center gap-2 ${textHighlight}`}>
          <span>📈</span> {isEnglish ? 'Underlying Stats (Season)' : 'נתוני עומק של השחקנים שלך (העונה)'}
        </h4>
        <table className="w-full text-sm text-left rtl:text-right">
          <thead className={`text-xs uppercase ${tableHeaderBg} ${textMuted}`}>
            <tr>
              <th className="px-4 py-3">{isEnglish ? 'Player' : 'שחקן'}</th>
              <th className="px-4 py-3 text-center">Form</th>
              <th className="px-4 py-3 text-center" title="Expected Goals">xG</th>
              <th className="px-4 py-3 text-center" title="Expected Assists">xA</th>
              <th className="px-4 py-3 text-center" title="Expected Goals Conceded">xGC</th>
              <th className="px-4 py-3 text-center" title="Clean Sheets">CS</th>
              <th className="px-4 py-3 text-center" title="Goals Conceded">GC</th>
              <th className="px-4 py-3 text-center" title="Defensive Contribution">DEFCON</th>
            </tr>
          </thead>
          <tbody>
            {[...data.squad].sort((a:any, b:any) => b.form - a.form).map((p: any) => (
              <tr key={p.id} className={`border-b transition-colors ${isDarkMode ? 'border-gray-700 hover:bg-gray-800' : 'border-gray-200 hover:bg-gray-50'}`}>
                <td className="px-4 py-3 font-bold flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${p.position <= 11 ? 'bg-emerald-500' : 'bg-gray-400'}`}></span>
                  {p.name}
                </td>
                <td className="px-4 py-3 text-center font-bold text-orange-500">{p.form}</td>
                <td className="px-4 py-3 text-center font-bold text-blue-500">{p.xg}</td>
                <td className="px-4 py-3 text-center font-bold text-purple-500">{p.xa}</td>
                <td className="px-4 py-3 text-center font-bold text-red-500">{p.xgc}</td>
                <td className="px-4 py-3 text-center font-bold text-emerald-500">{p.cs}</td>
                <td className="px-4 py-3 text-center font-bold text-red-700">{p.gc}</td>
                <td className="px-4 py-3 text-center font-bold text-blue-400">{p.defcon?.toFixed(1) || '0.0'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}


// קומפוננטת כרטיס שחקן מותאמת לעיצוב החדש
function PlayerCard({ 
  player, 
  isBench = false, 
  activeId, 
  onActionClick,
  transferMode = false
}: { 
  player: any, 
  isBench?: boolean, 
  activeId: number | null,
  onActionClick: (id: number) => void,
  transferMode?: boolean
}) {
  const shirtImg = `https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${player.team_code}-66.webp`;
  
  const getDiffColor = (diff: number) => {
    switch(diff) {
      case 1: return 'bg-green-800 text-white';
      case 2: return 'bg-green-500 text-white';
      case 3: return 'bg-gray-200 text-gray-800';
      case 4: return 'bg-red-500 text-white';
      case 5: return 'bg-red-800 text-white';
      default: return 'bg-gray-200 text-gray-800';
    }
  };

  const isSelected = activeId === player.id;
  const isActionMode = activeId !== null;

  return (
    <div className={`relative flex flex-col items-center w-[46px] min-[400px]:w-[56px] sm:w-[95px] transition-all duration-300 ${isBench && !isActionMode ? 'opacity-90 hover:opacity-100' : ''} ${isSelected ? 'scale-110 z-30' : ''}`}>
      
      {/* Swap/Cancel Button */}
      <button 
        onClick={() => onActionClick(player.id)}
        className={`absolute -top-3 -left-3 z-40 w-6 h-6 sm:w-7 sm:h-7 flex items-center justify-center rounded-full font-bold shadow-sm transition-transform hover:scale-110 ${
          isSelected ? 'bg-red-500 text-white text-[10px]' : 'bg-white text-gray-600 text-[10px] border border-gray-300'
        }`}
      >
        {isSelected ? '❌' : '🔄'}
      </button>

      {/* Shirt */}
      <img src={shirtImg} alt={player.name} className={`w-10 sm:w-14 h-auto drop-shadow-md transition-transform ${isSelected ? 'brightness-110 drop-shadow-xl' : ''}`} />
      
      {/* Name */}
      <div 
        className={`text-white text-[10px] sm:text-[11px] font-bold px-1 sm:px-2 py-0.5 rounded shadow w-full text-center truncate mt-[-3px] z-10 
        ${isSelected ? 'bg-blue-600' : 
          (player.chance_of_playing === 0 ? 'bg-red-600' : 
          (player.chance_of_playing !== null && player.chance_of_playing !== undefined && player.chance_of_playing < 100 ? 'bg-orange-500' : 'bg-[#2c3e50]'))}`}
        title={player.news || ''}
      >
        {player.name}
      </div>
      
      {/* Fixture */}
      <div className={`w-full text-center text-[7px] sm:text-[10px] font-bold py-0.5 shadow-sm ${getDiffColor(player.fixture_diff)}`}>
        {player.fixture || 'Blank'}
      </div>

      {/* Data Row */}
      <div className="bg-white text-gray-900 text-[9px] sm:text-[11px] font-bold px-1 w-full text-center rounded-b shadow-sm flex justify-between items-center border-b border-x border-gray-200">
        <span>£{player.cost.toFixed(1)}</span>
        <span className="text-[#126b3f]">{player.xp?.toFixed(1) || '0.0'}</span>
      </div>

      {/* C/V Badges */}
      {player.is_captain && !isSelected && (
        <div className="absolute -top-2 -right-2 bg-[#2c3e50] text-white text-[9px] w-4 h-4 flex items-center justify-center rounded-full font-bold z-20 shadow">C</div>
      )}
      {player.is_vice_captain && !isSelected && (
        <div className="absolute -top-2 -right-2 bg-gray-100 text-gray-800 text-[9px] w-4 h-4 flex items-center justify-center rounded-full font-bold z-20 shadow border border-gray-300">V</div>
      )}
    </div>
  );
}


function EliteRadarTab({ isEnglish, isDarkMode, textMuted, textHighlight, bgBox }: any) {
  const [radarData, setRadarData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/radar`)
      .then(res => res.json())
      .then(data => {
        setRadarData(data);
        setLoading(false);
      })
      .catch(err => {
        setError("Failed to fetch radar data");
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-center p-10 font-bold">{isEnglish ? 'Loading Elite Radar...' : 'טוען רדאר עילית...'} 📡</div>;
  if (error) return <div className="text-center p-10 font-bold text-red-500">{isEnglish ? error : 'שגיאה בטעינת הנתונים'}</div>;

  const renderPlayerList = (players: any[], colorClass: string, icon: string, titleStr: string, descStr: string) => (
    <div className={`p-4 rounded-xl border ${isDarkMode ? 'border-gray-700 bg-gray-800/50' : 'border-gray-200 bg-gray-50'} mb-6`}>
      <h4 className={`text-lg font-bold mb-2 flex items-center gap-2 ${colorClass}`}>
        <span>{icon}</span> {titleStr}
      </h4>
      <p className={`text-xs mb-4 ${textMuted}`}>{descStr}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left rtl:text-right">
          <thead className={`text-xs uppercase ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'} ${textMuted}`}>
            <tr>
              <th className="px-3 py-2">{isEnglish ? 'Player' : 'שחקן'}</th>
              <th className="px-3 py-2 text-center">{isEnglish ? 'Team' : 'קבוצה'}</th>
              <th className="px-3 py-2 text-center">{isEnglish ? 'Cost' : 'מחיר'}</th>
              <th className="px-3 py-2 text-center">xP</th>
              <th className="px-3 py-2 text-center">{isEnglish ? 'Form' : 'כושר'}</th>
              <th className="px-3 py-2 text-center" title="Teams Selected By (אחוזי בעלות)">{isEnglish ? 'Ownership' : 'אחוזי בעלות'}</th>
            </tr>
          </thead>
          <tbody>
            {players.map((p: any) => (
              <tr key={p.id} className={`border-b transition-colors ${isDarkMode ? 'border-gray-700 hover:bg-gray-700' : 'border-gray-200 hover:bg-white'}`}>
                <td className="px-3 py-2 font-bold">{p.name}</td>
                <td className="px-3 py-2 text-center font-bold">{p.team}</td>
                <td className="px-3 py-2 text-center text-emerald-600">£{p.cost.toFixed(1)}M</td>
                <td className="px-3 py-2 text-center font-bold text-blue-500">{p.xp.toFixed(1)}</td>
                <td className="px-3 py-2 text-center font-bold text-orange-500">{p.form.toFixed(1)}</td>
                <td className="px-3 py-2 text-center font-bold text-purple-500">{p.selected_by_percent}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div>
      <p className={`mb-6 text-sm ${textMuted}`}>
        {isEnglish 
          ? 'General market recommendations based on global data (MUST HAVE, BUY, DIFFERENTIALS). Not specific to your current squad.' 
          : 'המלצות שוק כלליות על בסיס נתונים גלובליים (שחקני חובה, שחקנים בכושר שיא, ושחקנים דיפרנציאלים). מתעדכן שבועית ולא קשור ספציפית לסגל שלך.'}
      </p>

      {renderPlayerList(
        radarData.hot_form, 
        'text-orange-500', 
        '🔥', 
        isEnglish ? 'MUST HAVE / BUY (Hot Form)' : 'שחקני חובה / קנייה (בכושר שיא)', 
        isEnglish ? 'Players with the highest Form right now. Proven point scorers over the last 30 days.' : 'השחקנים בכושר הכי טוב בליגה כרגע. מוכיחים את עצמם בעקביות ב-30 הימים האחרונים.'
      )}

      {renderPlayerList(
        radarData.scout_picks, 
        'text-blue-500', 
        '🎯', 
        isEnglish ? 'SCOUT PICKS (Top xP)' : 'בחירות הסקאוט (תוחלת הנקודות הגבוהה ביותר)', 
        isEnglish ? 'Players with the highest expected points (xP) for the upcoming gameweek based on AI models and fixture difficulty.' : 'שחקנים עם תוחלת הנקודות (xP) הגבוהה ביותר למחזור הקרוב, על בסיס מודלי AI וקושי משחקים.'
      )}

      {renderPlayerList(
        radarData.differentials, 
        'text-purple-500', 
        '💎', 
        isEnglish ? 'DIFFERENTIALS (Hidden Gems)' : 'שחקנים דיפרנציאליים (פנינים נסתרות)', 
        isEnglish ? 'High potential players owned by less than 10% of managers. Great for jumping up the ranks.' : 'שחקנים עם פוטנציאל גבוה שאחוזי הבעלות עליהם נמוכים מ-10%. מצוינים כדי לעקוף מתחרים בליגות.'
      )}
    </div>
  );
}

function BudgetScenariosTab({ teamId, isEnglish, isDarkMode, textMuted, textHighlight, bgBox, onTransfer }: any) {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/budget-scenarios/${teamId}`)
      .then(res => res.json())
      .then(data => {
        setScenarios(data);
        setLoading(false);
      })
      .catch(err => {
        setError(isEnglish ? "Failed to load budget scenarios." : "שגיאה בטעינת תרחישי התקציב.");
        setLoading(false);
      });
  }, [teamId]);

  if (loading) return <div className="text-center p-10 font-bold">{isEnglish ? 'Analyzing weak links and calculating replacements...' : 'מנתח חוליות חלשות ומחשב חלופות אידיאליות...'} 🤖</div>;
  if (error) return <div className="text-center p-10 font-bold text-red-500">{error}</div>;

  if (scenarios.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-10 text-center">
        <span className="text-4xl mb-4">🛡️</span>
        <h4 className="text-xl font-bold text-emerald-500 mb-2">{isEnglish ? 'No urgent transfers needed!' : 'הסגל שלך חסין כרגע! אין חילופים דחופים.'}</h4>
        <p className={textMuted}>{isEnglish ? 'Your squad looks solid based on FDR, form, and xP.' : 'על סמך נתוני פציעות, קושי משחקים וכושר, כל השחקנים שלך נראים כמו בחירות בטוחות כרגע.'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <p className={`mb-4 text-sm ${textMuted}`}>
        {isEnglish 
          ? 'The AI has identified the following weak links in your squad based on tough fixtures, poor form, or injury risks. Here are the top affordable replacements.' 
          : 'המערכת איתרה את החוליות החלשות בסגל שלך על בסיס משחקים קשים, פציעות או תוחלת נקודות נמוכה. אלו המחליפים הטובים ביותר שתוכל להרשות לעצמך בתקציב הנוכחי.'}
      </p>

      {scenarios.map((scenario: any, index: number) => (
        <div key={index} className={`p-4 rounded-xl border ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'} shadow-sm flex flex-col md:flex-row gap-6 items-center`}>
          
          {/* Sell Section */}
          <div className={`flex-1 text-center md:text-start flex flex-col items-center md:items-start border-b md:border-b-0 md:border-e pb-4 md:pb-0 md:pe-6 ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <span className="bg-red-100 text-red-700 text-xs font-bold px-2 py-1 rounded mb-3">{isEnglish ? 'SELL' : 'למכור'}</span>
            <div className="flex items-center gap-4">
              <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${scenario.sell.team_code}-66.webp`} className="w-16 h-auto drop-shadow-md" />
              <div>
                <h4 className={`text-xl font-black ${textHighlight}`}>{scenario.sell.name}</h4>
                <p className={`text-sm font-bold ${textMuted}`}>{scenario.sell.team}</p>
                <p className="text-red-500 font-bold text-sm mt-1">⚠️ {scenario.reason}</p>
                <p className={`text-xs mt-1 ${textHighlight}`}>£{scenario.sell.cost.toFixed(1)}M | {scenario.sell.xp.toFixed(1)} xP</p>
              </div>
            </div>
          </div>

          {/* Buy Section */}
          <div className="flex-[2] w-full">
            <span className="bg-emerald-100 text-emerald-700 text-xs font-bold px-2 py-1 rounded mb-3 inline-block">{isEnglish ? 'RECOMMENDED BUYS' : 'מחליפים מומלצים'}</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {scenario.buys.map((buy: any) => (
                <div key={buy.id} className={`p-3 rounded-lg border ${isDarkMode ? 'bg-gray-750 border-gray-600' : 'bg-gray-50 border-gray-200'} flex flex-col items-center text-center relative`}>
                  <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${buy.team_code}-66.webp`} className="w-10 mb-2 drop-shadow-sm" />
                  <p className={`font-black text-sm truncate w-full ${textHighlight}`}>{buy.name}</p>
                  <p className={`text-[10px] font-bold ${textMuted}`}>{buy.team}</p>
                  
                  <div className={`flex justify-center w-full mt-2 text-xs border-t pt-2 ${isDarkMode ? 'border-gray-600' : 'border-gray-200'}`}>
                    <span className="font-bold text-emerald-500">{buy.xp.toFixed(1)} xP</span>
                  </div>
                  <div className={`mt-1 text-[10px] w-full text-center font-bold px-1 py-0.5 rounded ${isDarkMode ? 'bg-gray-900 text-gray-300' : 'bg-gray-200 text-gray-700'}`}>
                    £{buy.cost.toFixed(1)}M
                  </div>
                  <button 
                    onClick={() => onTransfer && onTransfer(scenario.sell.id, buy)} 
                    className="mt-2 w-full text-[10px] py-1 bg-emerald-500 hover:bg-emerald-600 text-white rounded font-bold transition-colors"
                  >
                    {isEnglish ? 'Execute Transfer' : 'בצע חילוף'}
                  </button>
                </div>
              ))}
            </div>
          </div>

        </div>
      ))}
    </div>
  );
}

function GWPlannerTab({ data, isEnglish, isDarkMode, textMuted, textHighlight, bgBox, onSwap, swapSourceId, onSell, onCaptain, onVice, onReset, originalData, onRestorePlayer }: any) {
  const [selectedGwOffset, setSelectedGwOffset] = useState(0);
  const [ftAvailable, setFtAvailable] = useState(1);
  const [activeChip, setActiveChip] = useState<string | null>(null);

  const isChipAvailable = (chipId: string) => {
    const usedCount = (data.chips_used || []).filter((c: string) => c === chipId).length;
    if (chipId === 'wildcard') {
      // Second WC available from GW20 onwards
      if (data.next_gw < 20) return usedCount === 0;
      return usedCount < 2;
    }
    return usedCount === 0;
  };

  const getFDRColor = (diff: number) => {
    if (diff <= 2) return 'bg-[#01fc7a] text-green-900 border-green-500';
    if (diff === 3) return isDarkMode ? 'bg-gray-600 text-white border-gray-500' : 'bg-[#ebebe4] text-gray-900 border-gray-300';
    if (diff === 4) return 'bg-[#ff005a] text-white border-red-700';
    return 'bg-[#80072d] text-white border-red-900';
  };

  const getFdrBadgeColor = (diff: number) => {
    if (diff <= 2) return 'bg-green-500 text-white';
    if (diff === 3) return 'bg-gray-300 text-gray-800';
    if (diff === 4) return 'bg-red-500 text-white';
    return 'bg-red-900 text-white';
  };

  const starters = data.squad.filter((p: any) => p.position <= 11);
  const bench = data.squad.filter((p: any) => p.position > 11).sort((a: any, b: any) => a.position - b.position);
  const totalXP = starters.reduce((acc: number, p: any) => acc + (p.xp * (p.multiplier || 1)), 0);

  const selectedGwNumber = data.next_gw + selectedGwOffset;
  const scheduleForGw = data.schedule?.[selectedGwNumber] || [];

  const originalSquadIds = originalData?.squad.map((p: any) => p.id) || [];
  const transfersMade = data.squad.filter((p: any) => !originalSquadIds.includes(p.id)).length;
  // Dynamic FT calculation based on base ftAvailable + offset
  const simulatedFt = Math.min(5, ftAvailable + selectedGwOffset);
  const transfersRemaining = simulatedFt - transfersMade;
  const hitPoints = (activeChip === 'wildcard' || activeChip === 'freehit') ? 0 : (transfersRemaining < 0 ? transfersRemaining * 4 : 0);

  const renderPlayer = (p: any, isBench: boolean = false) => {
    const fix0 = p.upcoming_fixtures?.[selectedGwOffset];
    const isSelected = swapSourceId === p.id;
    const isTransfer = !originalSquadIds.includes(p.id);

    return (
      <div key={p.id} className={`flex flex-col items-center w-12 sm:w-24 transition-transform hover:scale-105 ${isBench ? 'opacity-90 hover:opacity-100' : ''}`}>
        <div className="relative mb-0 sm:mb-1">
          <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${p.team_code}-66.webp`} className="w-7 sm:w-12 h-14 sm:h-16 object-contain drop-shadow-md" />
          {p.is_captain && <div className="absolute -bottom-1 -right-2 bg-black text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center border border-yellow-400 shadow z-10">C</div>}
          {p.is_vice_captain && <div className="absolute -bottom-1 -right-2 bg-white text-black text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center border border-black shadow z-10">V</div>}
        </div>
        
        <div className={`text-[10px] sm:text-[11px] font-black px-1.5 py-0.5 rounded shadow-sm whitespace-nowrap overflow-hidden text-ellipsis w-[110%] text-center border ${
            isSelected ? 'bg-blue-600 text-white border-blue-700' :
            p.chance_of_playing === 0 ? 'bg-red-600 text-white border-red-700' :
            (p.chance_of_playing !== null && p.chance_of_playing !== undefined && p.chance_of_playing < 100) ? 'bg-orange-500 text-white border-orange-600' :
            (isDarkMode ? 'bg-white text-gray-900 border-gray-300' : 'bg-white text-gray-900 border-gray-200')
          }`}
          title={p.news || ''}>
          {p.name}
        </div>
        
        <div className="flex flex-col w-[110%] mt-1 gap-[1px]">
          {fix0 ? (
            <div className={`text-[9.5px] font-bold py-[3px] w-full text-center rounded shadow-sm border ${getFDRColor(fix0.difficulty)}`}>{fix0.opponent}</div>
          ) : (
            <div className={`text-[9.5px] font-bold py-[3px] w-full text-center rounded shadow-sm border bg-gray-500 text-white border-gray-600`}>Blank</div>
          )}
        </div>
        
        <div className={`mt-1 text-[7px] sm:text-[10px] font-bold w-full text-center drop-shadow-sm ${isBench ? (isDarkMode ? 'text-gray-300' : 'text-gray-700') : 'text-white'}`}>
          £{p.cost.toFixed(1)}m | xP {p.xp.toFixed(1)}
        </div>
        
        <div className="flex flex-wrap justify-center gap-1 mt-1 w-[110%]">
          <button 
            onClick={() => onSwap(p.id)}
            title={isEnglish ? 'Swap Player' : 'חילוף (ספסל/הרכב)'}
            className={`w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center rounded shadow cursor-pointer transition-colors ${isSelected ? 'bg-yellow-500 hover:bg-yellow-600 text-black' : 'bg-blue-500 hover:bg-blue-600 text-white'}`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </button>
          
          <button 
            onClick={() => onSell(p.id)}
            disabled={swapSourceId !== null}
            title={isEnglish ? 'Transfer Out (Buy new player)' : 'מכור שחקן (העברה)'}
            className={`w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center rounded shadow transition-colors ${swapSourceId !== null ? 'opacity-50 cursor-not-allowed bg-red-400 text-white' : 'cursor-pointer bg-red-500 hover:bg-red-600 text-white'}`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </button>

          {isTransfer && (
            <button 
              onClick={() => onRestorePlayer(p.position)}
              disabled={swapSourceId !== null}
              title={isEnglish ? 'Undo Transfer' : 'בטל חילוף זה'}
              className={`w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center rounded shadow transition-colors ${swapSourceId !== null ? 'opacity-50 cursor-not-allowed bg-purple-400 text-white' : 'cursor-pointer bg-purple-500 hover:bg-purple-600 text-white'}`}
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>
            </button>
          )}

          {!isBench && (
            <>
              <button 
                onClick={() => onCaptain(p.id)}
                disabled={swapSourceId !== null}
                title={isEnglish ? 'Set Captain' : 'בחר קפטן'}
                className={`w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center rounded shadow transition-colors ${swapSourceId !== null ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${p.is_captain ? 'bg-black text-yellow-400 border border-yellow-400' : isDarkMode ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'}`}
              >
                <span className="text-[8px] sm:text-xs font-black">C</span>
              </button>
              <button 
                onClick={() => onVice(p.id)}
                disabled={swapSourceId !== null}
                title={isEnglish ? 'Set Vice Captain' : 'בחר סגן קפטן'}
                className={`w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center rounded shadow transition-colors ${swapSourceId !== null ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${p.is_vice_captain ? 'bg-white text-black border border-black' : isDarkMode ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'}`}
              >
                <span className="text-[8px] sm:text-xs font-black">V</span>
              </button>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col w-full">
      <div className={`p-4 sm:p-6 rounded-xl shadow-sm border mb-6 ${bgBox}`}>
        <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
          <div className="flex flex-col sm:flex-row items-center gap-2 w-full sm:w-auto">
            <button 
              onClick={onReset}
              className="bg-gray-500 hover:bg-gray-600 text-white font-black py-2.5 px-4 rounded-lg shadow-sm text-sm transition-colors w-full sm:w-auto"
            >
              {isEnglish ? 'Reset Squad' : 'אפס סגל'}
            </button>
            <div className="flex gap-2">
              {[
                { id: 'wildcard', label: 'WC' },
                { id: 'freehit', label: 'FH' },
                { id: 'bboost', label: 'BB' },
                { id: '3xc', label: 'TC' }
              ].map(chip => {
                const available = isChipAvailable(chip.id);
                const isActive = activeChip === chip.id;
                return (
                  <button
                    key={chip.id}
                    disabled={!available}
                    onClick={() => setActiveChip(isActive ? null : chip.id)}
                    className={`font-black text-xs py-2 px-3 rounded-lg shadow-sm transition-colors border-2 ${
                      !available ? (isDarkMode ? 'bg-gray-700 border-gray-700 text-gray-500 cursor-not-allowed opacity-50' : 'bg-gray-200 text-gray-400 border-gray-200 cursor-not-allowed opacity-50') 
                      : isActive ? 'bg-purple-600 border-purple-600 text-white' 
                      : isDarkMode ? 'bg-gray-800 border-purple-500 text-purple-400 hover:bg-gray-700' : 'bg-white border-purple-500 text-purple-600 hover:bg-purple-50'
                    }`}
                    title={!available ? (isEnglish ? 'Already used' : 'כבר שומש') : ''}
                  >
                    {chip.label}
                  </button>
                );
              })}
            </div>
          </div>
          
          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <span className={`text-sm font-bold ${textMuted}`}>{isEnglish ? 'Select Gameweek:' : 'בחר מחזור:'}</span>
            <div className="flex items-center gap-1">
              <button 
                onClick={() => setSelectedGwOffset(Math.max(0, selectedGwOffset - 1))}
                disabled={selectedGwOffset === 0}
                className={`w-8 h-8 flex items-center justify-center rounded-lg border font-bold text-lg shadow-sm transition-colors ${selectedGwOffset === 0 ? (isDarkMode ? 'opacity-50 cursor-not-allowed bg-gray-800 text-gray-500 border-gray-700' : 'opacity-50 cursor-not-allowed bg-gray-100 text-gray-400 border-gray-200') : (isDarkMode ? 'hover:bg-gray-600 bg-gray-700 text-white border-gray-600' : 'hover:bg-purple-100 hover:text-purple-700 bg-white border-gray-300 text-gray-800')}`}
              >
                &lt;
              </button>
              <select 
                value={selectedGwOffset}
                onChange={(e) => setSelectedGwOffset(Number(e.target.value))}
                className={`border rounded-lg px-3 py-1.5 text-sm font-black shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 ${isDarkMode ? 'bg-gray-800 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
              >
                {Array.from({length: Math.max(1, 38 - data.next_gw + 1)}, (_, i) => i).map(offset => (
                  <option key={offset} value={offset}>GW {data.next_gw + offset} {offset === 0 ? (isEnglish ? '(Current)' : '(נוכחי)') : ''}</option>
                ))}
              </select>
              <button 
                onClick={() => setSelectedGwOffset(Math.min(38 - data.next_gw, selectedGwOffset + 1))}
                disabled={selectedGwOffset === Math.max(0, 38 - data.next_gw)}
                className={`w-8 h-8 flex items-center justify-center rounded-lg border font-bold text-lg shadow-sm transition-colors ${selectedGwOffset === Math.max(0, 38 - data.next_gw) ? (isDarkMode ? 'opacity-50 cursor-not-allowed bg-gray-800 text-gray-500 border-gray-700' : 'opacity-50 cursor-not-allowed bg-gray-100 text-gray-400 border-gray-200') : (isDarkMode ? 'hover:bg-gray-600 bg-gray-700 text-white border-gray-600' : 'hover:bg-purple-100 hover:text-purple-700 bg-white border-gray-300 text-gray-800')}`}
              >
                &gt;
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className={`border rounded-xl p-4 flex flex-col justify-center items-center shadow-sm ${isDarkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'}`}>
            <span className={`text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Expected Points (xP)' : 'תוחלת נקודות (xP)'}</span>
            <span className="text-2xl font-black">{totalXP.toFixed(1)}</span>
          </div>
          <div className={`border rounded-xl p-4 flex flex-col justify-center items-center shadow-sm ${isDarkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'}`}>
            <span className={`text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Bank Balance' : 'יתרה בבנק'}</span>
            <span className={`text-2xl font-black ${data.bank < 0 ? 'text-red-500' : ''}`}>£{data.bank.toFixed(1)}m</span>
          </div>
          <div className={`border rounded-xl p-4 flex flex-col justify-center items-center shadow-sm ${isDarkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'}`}>
            <span className={`text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Hit Points' : 'קנס נקודות (Hits)'}</span>
            <span className={`text-2xl font-black ${hitPoints < 0 ? 'text-red-500' : 'text-gray-500'}`}>{hitPoints}</span>
          </div>
          <div className={`border rounded-xl p-4 flex flex-col justify-center items-center shadow-sm ${isDarkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'}`}>
            <span className={`text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Available Transfers' : 'חילופים זמינים'}</span>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setFtAvailable(Math.max(0, ftAvailable - 1))}
                className={`w-6 h-6 flex items-center justify-center rounded-full font-bold transition-colors ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-800'}`}
              >-</button>
              <span className={`text-2xl font-black ${(activeChip === 'wildcard' || activeChip === 'freehit') ? 'text-purple-500' : (transfersRemaining < 0 ? 'text-red-500' : 'text-emerald-500')}`} title={`Base: ${ftAvailable} + Offset: ${selectedGwOffset}`}>
                {(activeChip === 'wildcard' || activeChip === 'freehit') ? '∞' : `FT ${transfersRemaining}`}
              </span>
              <button 
                onClick={() => setFtAvailable(Math.min(5, ftAvailable + 1))}
                className={`w-6 h-6 flex items-center justify-center rounded-full font-bold transition-colors ${isDarkMode ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-800'}`}
              >+</button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col-reverse lg:flex-row gap-6 items-start">
        {/* Schedule Sidebar */}
        <div className={`w-full lg:w-1/4 rounded-xl border p-4 shadow-sm flex flex-col h-fit ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <h4 className={`text-lg font-black mb-4 ${textHighlight}`}>{isEnglish ? `GW ${selectedGwNumber} Fixtures` : `משחקי מחזור ${selectedGwNumber}`}</h4>
          <div className="flex flex-col gap-2 overflow-y-auto max-h-[600px] pr-1">
            {scheduleForGw.map((match: any, idx: number) => (
              <div key={idx} className={`flex items-center justify-between p-2 rounded border ${isDarkMode ? 'bg-gray-900 border-gray-700' : 'bg-gray-50 border-gray-100'} text-xs font-bold`}>
                <div className="flex items-center gap-1.5 w-2/5 justify-end">
                  <span className={isDarkMode ? 'text-gray-200' : 'text-gray-800'}>{match.home_team}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[9px] ${getFdrBadgeColor(match.home_diff)}`}>{match.home_diff}</span>
                </div>
                <div className={`text-[10px] px-1 ${textMuted}`}>vs</div>
                <div className="flex items-center gap-1.5 w-2/5 justify-start">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] ${getFdrBadgeColor(match.away_diff)}`}>{match.away_diff}</span>
                  <span className={isDarkMode ? 'text-gray-200' : 'text-gray-800'}>{match.away_team}</span>
                </div>
              </div>
            ))}
            {scheduleForGw.length === 0 && <p className={`text-center text-sm ${textMuted}`}>{isEnglish ? 'No fixtures' : 'אין משחקים'}</p>}
          </div>
        </div>

        {/* Pitch Container */}
        <div className={`w-full lg:w-3/4 max-w-5xl mx-auto rounded-3xl shadow-xl overflow-hidden border-4 flex flex-col ${isDarkMode ? 'border-gray-800' : 'border-gray-300'}`}>
          <div className="bg-[#126b3f] p-1 sm:p-6 md:p-8 relative flex flex-col justify-around min-h-[400px] md:min-h-[600px] flex-grow">
            <div className="absolute inset-0 opacity-20 pointer-events-none overflow-hidden">
              <div className="absolute top-1/2 left-0 right-0 h-1 bg-white"></div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 md:w-48 h-32 md:h-48 border-4 border-white rounded-full"></div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full"></div>
              
              <div className="absolute top-0 left-1/4 right-1/4 h-32 md:h-40 border-4 border-t-0 border-white"></div>
              <div className="absolute top-0 left-[38%] right-[38%] h-12 md:h-16 border-4 border-t-0 border-white"></div>
              <div className="absolute top-[8rem] md:top-[10rem] left-1/2 -translate-x-1/2 w-24 h-12 border-4 border-transparent border-b-white rounded-full"></div>
              
              <div className="absolute bottom-0 left-1/4 right-1/4 h-32 md:h-40 border-4 border-b-0 border-white"></div>
              <div className="absolute bottom-0 left-[38%] right-[38%] h-12 md:h-16 border-4 border-b-0 border-white"></div>
              <div className="absolute bottom-[8rem] md:bottom-[10rem] left-1/2 -translate-x-1/2 w-24 h-12 border-4 border-transparent border-t-white rounded-full"></div>
            </div>
            
            <div className="flex justify-center z-10 gap-0 sm:gap-6 md:gap-8">
              {starters.filter((p: any) => p.pos_code === 1).map((p: any) => renderPlayer(p, false))}
            </div>
            <div className="flex justify-center z-10 gap-0 sm:gap-6 md:gap-8 mt-3 sm:mt-8">
              {starters.filter((p: any) => p.pos_code === 2).map((p: any) => renderPlayer(p, false))}
            </div>
            <div className="flex justify-center z-10 gap-0 sm:gap-6 md:gap-8 mt-3 sm:mt-8">
              {starters.filter((p: any) => p.pos_code === 3).map((p: any) => renderPlayer(p, false))}
            </div>
            <div className="flex justify-center z-10 gap-0 sm:gap-6 md:gap-8 mt-3 sm:mt-8">
              {starters.filter((p: any) => p.pos_code === 4).map((p: any) => renderPlayer(p, false))}
            </div>
          </div>
          
          <div className={`p-2 sm:p-6 md:p-8 flex justify-center gap-0 sm:gap-6 md:gap-8 border-t-2 border-white/20 border-dashed z-20 bg-[#0e5230]`}>
            {bench.map((p: any) => renderPlayer(p, true))}
          </div>
        </div>
      </div>
    </div>
  );
}

function LeaguesTab({ data, isEnglish, isDarkMode, textMuted, textHighlight, bgBox }: any) {
  const [selectedLeague, setSelectedLeague] = useState<any>(null);
  const [standings, setStandings] = useState<any[]>([]);
  const [loadingLeague, setLoadingLeague] = useState(false);
  const [leagueSearch, setLeagueSearch] = useState('');
  
  const [compareTeamId, setCompareTeamId] = useState<number | null>(null);
  const [compareData, setCompareData] = useState<any>(null);
  const [loadingCompare, setLoadingCompare] = useState(false);
  const [compareError, setCompareError] = useState("");

  const allLeagues = [...(data.leagues?.classic || []).map((l: any) => ({...l, _type: 'classic'})), ...(data.leagues?.h2h || []).map((l: any) => ({...l, _type: 'h2h'}))];

  const fetchLeagueStandings = async (league: any) => {
    setSelectedLeague(league);
    setStandings([]);
    setLoadingLeague(true);
    setCompareData(null);
    setCompareTeamId(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/league/${league.id}?type=${league._type}`);
      if (res.ok) {
        const json = await res.json();
        setStandings(json.standings?.results || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingLeague(false);
    }
  };

  const fetchExternalLeague = async () => {
    if (!leagueSearch) return;
    const fake = { id: parseInt(leagueSearch), name: `League #${leagueSearch}`, _type: 'classic', entry_rank: '?' };
    await fetchLeagueStandings(fake);
  };

  const fetchCompare = async (rivalId: number) => {
    setCompareTeamId(rivalId);
    setLoadingCompare(true);
    setCompareError("");
    setCompareData(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/compare/${data.team_id}/${rivalId}?gw=${Math.max(1, data.next_gw - 1)}`);
      if (!res.ok) throw new Error(isEnglish ? "Could not fetch rival team." : "לא ניתן לטעון את הסגל של היריב.");
      const json = await res.json();
      setCompareData(json);
    } catch (err: any) {
      setCompareError(err.message);
    } finally {
      setLoadingCompare(false);
    }
  };

  const leaderTeam = standings.length > 0 ? standings[0] : null;
  const myStanding = standings.find((s: any) => s.entry === data.team_id);
  const bgCard = isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200';

  return (
    <div className="flex flex-col gap-6">
      {/* Description */}
      <p className={`text-sm ${textMuted} text-center`}>
        {isEnglish 
          ? 'Track your rivals in mini-leagues: see which players they own, who picked which captain, and find the differentials that will make or break your rank.'
          : 'עקוב אחרי יריביך במיני-ליגה: זהה באילו שחקנים הם מחזיקים, מי בחר איזה קפטן, ואתר דיפרנשיאלים שיקפיצו אותך בדירוג.'}
      </p>

      {/* League Selector Row */}
      <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-end">
        <div className="flex-1">
          <label className={`block text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Select from your leagues:' : 'בחר מתוך המיני-ליגות של הקבוצה שלך:'}</label>
          <select 
            value={selectedLeague?.id || ''}
            onChange={(e) => {
              const league = allLeagues.find((l: any) => l.id === parseInt(e.target.value));
              if (league) fetchLeagueStandings(league);
            }}
            className={`w-full p-3 rounded-lg border font-bold ${isDarkMode ? 'bg-gray-800 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
          >
            <option value="">{isEnglish ? '-- Choose a League --' : '-- בחר ליגה --'}</option>
            {allLeagues.map((l: any) => (
              <option key={l.id} value={l.id}>{l.name} ({l._type === 'h2h' ? 'H2H' : 'Classic'})</option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className={`block text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Or search by league ID:' : 'או חפש לפי קוד ליגה אחר:'}</label>
          <div className="flex gap-2">
            <input 
              type="number"
              value={leagueSearch}
              onChange={(e) => setLeagueSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchExternalLeague()}
              placeholder={isEnglish ? 'League ID...' : 'קוד ליגה...'}
              className={`flex-1 p-3 rounded-lg border font-bold ${isDarkMode ? 'bg-gray-800 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
            />
            <button onClick={fetchExternalLeague} className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-5 py-3 rounded-lg transition-colors">
              {isEnglish ? 'Search' : 'חפש'}
            </button>
          </div>
        </div>
      </div>

      {/* Stat Cards */}
      {selectedLeague && !loadingLeague && standings.length > 0 && (
        <>
          <h3 className={`text-xl font-black ${textHighlight}`}>
            {isEnglish ? `League Table: ${selectedLeague.name}` : `טבלת ליגה: ${selectedLeague.name}`}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className={`p-5 rounded-xl border text-center ${bgCard}`}>
              <div className={`text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'League Leader' : 'מוביל הליגה'}</div>
              <div className={`text-2xl font-black ${textHighlight} truncate`}>{leaderTeam?.entry_name || '-'}</div>
              <div className="text-emerald-500 font-bold text-sm mt-1">{leaderTeam?.total || 0} {isEnglish ? 'pts' : "נק'"} ⬆</div>
            </div>
            <div className={`p-5 rounded-xl border text-center ${bgCard}`}>
              <div className={`text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Your Rank in League' : 'הדירוג שלך בליגה'}</div>
              <div className={`text-4xl font-black ${textHighlight}`}>{isEnglish ? `#${myStanding?.rank || selectedLeague.entry_rank || '?'}` : `מקום ${myStanding?.rank || selectedLeague.entry_rank || '?'}`}</div>
              {myStanding && <div className="text-blue-500 font-bold text-xs mt-1">{myStanding.total} {isEnglish ? 'pts' : "נק'"}</div>}
            </div>
            <div className={`p-5 rounded-xl border text-center ${bgCard}`}>
              <div className={`text-xs font-bold mb-0 sm:mb-1 ${textMuted}`}>{isEnglish ? 'Members' : 'משתתפים בליגה'}</div>
              <div className={`text-4xl font-black ${textHighlight}`}>+{standings.length}</div>
            </div>
          </div>
        </>
      )}

      {loadingLeague && <div className="p-8 text-center font-bold animate-pulse">{isEnglish ? 'Loading standings...' : 'טוען טבלת דירוג...'}</div>}

      {/* Standings Table */}
      {selectedLeague && !loadingLeague && standings.length > 0 && (
        <div>
          <div className={`text-xs font-bold mb-2 ${textMuted} ${isEnglish ? 'text-left' : 'text-right'}`}>
            {isEnglish ? `Showing top ${standings.length} in league` : `מציג את ${standings.length} המובילים בליגה`}
          </div>
          <div className={`rounded-xl border shadow-sm overflow-hidden ${bgCard}`}>
            <div className="max-h-[500px] overflow-y-auto">
              <table className={`w-full text-sm ${isEnglish ? 'text-left' : 'text-right'}`}>
                <thead className={`sticky top-0 z-10 text-xs uppercase font-bold ${isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-500'}`}>
                  <tr>
                    <th className="px-4 py-3">{isEnglish ? '#' : 'דירוג'}</th>
                    <th className="px-4 py-3">{isEnglish ? 'Team Name' : 'שם הקבוצה'}</th>
                    <th className="px-4 py-3">{isEnglish ? 'Manager' : "מנג'ר"}</th>
                    <th className="px-4 py-3 text-center">{isEnglish ? 'Total Points' : 'סה"כ נקודות'}</th>
                    <th className="px-4 py-3 text-center">{isEnglish ? 'Team ID' : 'קבוצה ID'}</th>
                    <th className="px-4 py-3 text-center">{isEnglish ? 'Compare' : 'השווה'}</th>
                  </tr>
                </thead>
                <tbody>
                  {standings.map((team: any) => (
                    <tr 
                      key={team.entry} 
                      className={`border-b last:border-0 transition-colors ${team.entry === data.team_id ? (isDarkMode ? 'bg-blue-900/30 font-black' : 'bg-blue-50 font-black') : (isDarkMode ? 'border-gray-700 hover:bg-gray-700/50' : 'border-gray-100 hover:bg-gray-50')}`}
                    >
                      <td className="px-4 py-3 font-black">#{team.rank}</td>
                      <td className={`px-4 py-3 font-bold ${textHighlight}`}>{team.entry_name}</td>
                      <td className={`px-4 py-3 ${textMuted}`}>{team.player_name}</td>
                      <td className="px-4 py-3 text-center font-bold">{team.total} {isEnglish ? 'pts' : "נק'"}</td>
                      <td className={`px-4 py-3 text-center text-xs ${textMuted}`}>#{team.entry}</td>
                      <td className="px-4 py-3 text-center">
                        {team.entry !== data.team_id ? (
                          <button 
                            onClick={() => fetchCompare(team.entry)}
                            className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-colors ${compareTeamId === team.entry ? 'bg-purple-600 text-white' : `bg-purple-100 text-purple-700 ${isDarkMode ? 'bg-purple-900/30 text-purple-400' : 'hover:bg-purple-200'}`}`}
                          >
                            {isEnglish ? 'H2H' : 'ראש בראש'}
                          </button>
                        ) : (
                          <span className="text-xs font-bold text-emerald-500">{isEnglish ? 'You' : 'אתה 👈'}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* H2H Comparison */}
      {compareData && (
        <div className={`p-6 rounded-2xl border shadow-lg ${bgCard} relative mt-2`}>
          <button onClick={() => { setCompareData(null); setCompareTeamId(null); }} className={`absolute top-4 ${isEnglish ? 'right-4' : 'left-4'} font-bold text-gray-400 hover:text-red-500 text-lg`}>✕</button>
          
          <h4 className={`text-xl font-black mb-5 ${textHighlight}`}>
            {isEnglish ? '⚔️ Head-to-Head Comparison' : '⚔️ השוואת ראש בראש'}
          </h4>
          
          {loadingCompare && <p className="animate-pulse font-bold text-center p-8">{isEnglish ? 'Loading rivalry...' : 'טוען השוואה...'}</p>}
          {compareError && <p className="text-red-500 font-bold p-8 text-center">{compareError}</p>}
          
          {!loadingCompare && !compareError && compareData && (
            <div className="flex flex-col gap-5">
              {/* VS Header */}
              <div className={`flex items-center justify-between p-4 rounded-xl ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
                <div className="text-center w-5/12 overflow-hidden">
                  <div className={`font-black truncate text-lg ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`}>{compareData.team_a.name}</div>
                  <div className={`text-xs ${textMuted} truncate`}>{compareData.team_a.manager}</div>
                  {compareData.team_a.active_chip && <div className="mt-1 text-[10px] bg-blue-200 text-blue-800 px-2 py-0.5 rounded-full inline-block font-bold">{compareData.team_a.active_chip.toUpperCase()}</div>}
                </div>
                <div className="text-center w-2/12 font-black text-2xl text-gray-400">VS</div>
                <div className="text-center w-5/12 overflow-hidden">
                  <div className={`font-black truncate text-lg ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>{compareData.team_b.name}</div>
                  <div className={`text-xs ${textMuted} truncate`}>{compareData.team_b.manager}</div>
                  {compareData.team_b.active_chip && <div className="mt-1 text-[10px] bg-red-200 text-red-800 px-2 py-0.5 rounded-full inline-block font-bold">{compareData.team_b.active_chip.toUpperCase()}</div>}
                </div>
              </div>

              {/* Shared Players */}
              <div>
                <h5 className={`font-bold text-sm mb-3 ${textHighlight}`}>
                  🤝 {isEnglish ? `Shared Players (${compareData.shared.length})` : `שחקנים זהים (${compareData.shared.length})`}
                </h5>
                <div className="flex flex-wrap gap-2">
                  {compareData.shared.map((p: any) => (
                    <div key={p.id} className={`flex items-center gap-2 text-xs font-bold px-3 py-2 rounded-lg border ${isDarkMode ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'}`}>
                      <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${p.team_code}-66.webp`} className="w-4" />
                      <span>{p.name}</span>
                      {p.a_captain && <span className="bg-blue-600 text-white text-[9px] px-1 rounded">C</span>}
                      {p.b_captain && <span className="bg-red-600 text-white text-[9px] px-1 rounded">C</span>}
                    </div>
                  ))}
                </div>
              </div>

              {/* Differentials */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-bold text-sm mb-3 text-blue-500">
                    🔵 {isEnglish ? `Your Differentials (${compareData.team_a.unique.length})` : `הדיפרנשיאלים שלך (${compareData.team_a.unique.length})`}
                  </h5>
                  <div className="flex flex-col gap-2">
                    {compareData.team_a.unique.map((p: any) => (
                      <div key={p.id} className={`flex items-center gap-3 p-3 rounded-lg border ${isDarkMode ? 'bg-blue-900/20 border-blue-800/30' : 'bg-blue-50 border-blue-100'}`}>
                        <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${p.team_code}-66.webp`} className="w-6" />
                        <span className="font-bold text-sm truncate">{p.name}</span>
                        {p.is_captain && <span className="bg-black text-yellow-400 text-[10px] px-1.5 py-0.5 rounded font-bold">C</span>}
                      </div>
                    ))}
                    {compareData.team_a.unique.length === 0 && <p className={`text-xs ${textMuted}`}>{isEnglish ? 'No differentials' : 'אין דיפרנשיאלים'}</p>}
                  </div>
                </div>
                <div>
                  <h5 className="font-bold text-sm mb-3 text-red-500">
                    🔴 {isEnglish ? `Rival Differentials (${compareData.team_b.unique.length})` : `הדיפרנשיאלים של היריב (${compareData.team_b.unique.length})`}
                  </h5>
                  <div className="flex flex-col gap-2">
                    {compareData.team_b.unique.map((p: any) => (
                      <div key={p.id} className={`flex items-center gap-3 p-3 rounded-lg border ${isDarkMode ? 'bg-red-900/20 border-red-800/30' : 'bg-red-50 border-red-100'}`}>
                        <img src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${p.team_code}-66.webp`} className="w-6" />
                        <span className="font-bold text-sm truncate">{p.name}</span>
                        {p.is_captain && <span className="bg-black text-yellow-400 text-[10px] px-1.5 py-0.5 rounded font-bold">C</span>}
                      </div>
                    ))}
                    {compareData.team_b.unique.length === 0 && <p className={`text-xs ${textMuted}`}>{isEnglish ? 'No differentials' : 'אין דיפרנשיאלים'}</p>}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TipsTab({ isEnglish, isDarkMode, textMuted, textHighlight, bgBox }: any) {
  const bgCard = isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200';
  
  return (
    <div className="flex flex-col gap-8">
      {/* 60-Second Checklist Section */}
      <div className={`p-6 rounded-2xl border shadow-sm ${bgCard}`}>
        <h3 className={`text-xl font-black mb-4 flex items-center gap-2 ${textHighlight}`}>
          <span>⏱️</span> {isEnglish ? '60-Second Pre-Deadline Checklist:' : 'צ\'ק-ליסט 60 שניות לפני דדליין המחזור:'}
        </h3>
        <div className="flex flex-col gap-3">
          <label className="flex items-start gap-3 cursor-pointer group">
            <input type="checkbox" className="mt-1 w-5 h-5 text-green-600 rounded border-gray-300 focus:ring-green-500 cursor-pointer" />
            <span className={`text-base font-medium group-hover:text-green-600 transition-colors ${textHighlight}`}>
              {isEnglish ? 'Confirm Captain (C) and Vice-Captain (VC) safeguards' : 'אימות קפטן (C) וסגן (VC) מאובטח למקרה של אי-פתיחה מפתיעה'}
            </span>
          </label>
          <label className="flex items-start gap-3 cursor-pointer group">
            <input type="checkbox" className="mt-1 w-5 h-5 text-green-600 rounded border-gray-300 focus:ring-green-500 cursor-pointer" />
            <span className={`text-base font-medium group-hover:text-green-600 transition-colors ${textHighlight}`}>
              {isEnglish ? 'Check bench order (1-3) prioritized by return upside and minutes' : 'בדיקת סדר המחליפים בספסל (1-3) לפי סבירות דקות ופוטנציאל'}
            </span>
          </label>
          <label className="flex items-start gap-3 cursor-pointer group">
            <input type="checkbox" className="mt-1 w-5 h-5 text-green-600 rounded border-gray-300 focus:ring-green-500 cursor-pointer" />
            <span className={`text-base font-medium group-hover:text-green-600 transition-colors ${textHighlight}`}>
              {isEnglish ? 'Verify late-breaking press conference injury updates' : 'וידוא מסיבות עיתונאים ועדכוני פציעות של הרגע האחרון'}
            </span>
          </label>
          <label className="flex items-start gap-3 cursor-pointer group">
            <input type="checkbox" className="mt-1 w-5 h-5 text-green-600 rounded border-gray-300 focus:ring-green-500 cursor-pointer" />
            <span className={`text-base font-medium group-hover:text-green-600 transition-colors ${textHighlight}`}>
              {isEnglish ? 'Roll your free transfer if no critical surgery is required' : 'שמירת חילוף (Roll FT) אם אין צורך דחוף ומובהק בחילוף'}
            </span>
          </label>
        </div>
      </div>

      {/* 10 Tips Section */}
      <div>
        <div className="text-center mb-8">
          <h2 className={`text-3xl font-black mb-2 ${textHighlight}`}>
            {isEnglish ? '10 Pro Tips for FPL Success' : '10 טיפים להצלחה ב-FPL'}
          </h2>
          <p className={`text-lg ${textMuted}`}>
            {isEnglish ? 'Top 10k Strategic Golden Rules for Long-Term FPL Mastery' : 'עקרונות זהב אסטרטגיים של שחקני טופ 10k עולמי לניהול סגל מנצח לאורך העונה'}
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {FPL_SUCCESS_TIPS.map((tip) => (
            <div key={tip.num} className={`p-6 rounded-2xl border shadow-sm flex flex-col gap-3 ${bgCard} transition-transform hover:-translate-y-1 hover:shadow-md`}>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">{tip.icon}</span>
                <h4 className={`text-lg font-bold ${textHighlight}`}>
                  {tip.num}. {isEnglish ? tip.title_en : tip.title_he}
                </h4>
              </div>
              
              <div className="flex flex-wrap gap-2 mb-2">
                <span className={`text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider ${isDarkMode ? 'bg-blue-900/50 text-blue-300' : 'bg-blue-100 text-blue-700'}`}>
                  {isEnglish ? tip.tag_en : tip.tag_he}
                </span>
              </div>
              
              <p className={`text-sm flex-grow leading-relaxed ${textHighlight}`}>
                {isEnglish ? tip.desc_en : tip.desc_he}
              </p>
              
              <div className={`mt-3 p-3 rounded-lg text-sm font-bold border-l-4 border-yellow-400 ${isDarkMode ? 'bg-yellow-900/20 text-yellow-200' : 'bg-yellow-50 text-yellow-800'}`}>
                <span className="opacity-80 block text-xs uppercase mb-0 sm:mb-1">{isEnglish ? 'Golden Rule:' : 'כלל מפתח:'}</span>
                {isEnglish ? tip.rule_en : tip.rule_he}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
