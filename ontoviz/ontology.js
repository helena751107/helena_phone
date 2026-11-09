/* S21 PHONE — workstation ontology.
 *
 * One knowledge base behind the landing page: every glow on screen is a node
 * with a class, a weight, and a source (chapter + line from the webzine). The
 * graph, the dashboard, the inspector and the Web MCP tools all read this one
 * object. Copy is taken from index.html — nothing here invents a claim.
 */

export const COL = ['#f4efe6', '#e85d4c', '#d4a84b', '#3db8a8', '#8b7cf0', '#8fb3c9', '#f0c75e'];
export const CLASS = ['Hub', 'Track', 'Module', 'Agent', 'Stage', 'Channel', 'Install'];
export const SECTIONS = ['cover', 'tracks', 'system', 'agents', 'centers', 'funnel', 'economics', 'install', 'library', 'channels'];

/* Brand strings that panels.js and onto.js paint into the 3D scene. Keeping
   them here means the engine stays generic and the copy stays one place. */
export const BRAND = {
  kicker: 'S21 ontology',
  kickerDash: 'S21 ontology · WebGPU knowledge graph',
  kickerIntro: 'S21 ontology · interactive 3D · WebGPU',
  nameA: 'S21 ',
  nameB: 'Phone',
  lede: 'A 3D knowledge base standing on one phone. Every glow is a node — track, module, robot, workshop, door — every line is a relation, and each one traces back to a chapter.',
  introA: 'One phone.',
  introB: 'Two tracks.',
  introSub: 'Care that never breaks. Hope that reaches the world. An AI workstation running on one Galaxy S21. Drag to orbit, scroll to walk, click a glow to read its source.',
  note: 'EVERY KEY IS IN HER NAME · CARE TRACK STAYS PRIVATE',
  noteShort: 'EVERY KEY IS IN HER NAME',
  noteWrap: ['EVERY KEY IS IN HER NAME', 'CARE TRACK STAYS PRIVATE'],
  coverTitle: 'One phone.<br><em>Two tracks. Full stack.</em>',
  coverDeck: 'Care that never breaks. Hope that reaches the world. A ghostwriter-caregiver\'s AI workstation on one Galaxy S21 — this page is its blueprint.',
  startId: 'tracks',
  startLabel: 'Start with Tracks'
};

const N = [];
const L = [];
const add = (id, label, cls, s, val, ref, quote, desc, extra = {}) => {
  N.push({ id, label, cls, s, val, ref, quote, desc, ...extra });
};
const link = (source, target, rel) => L.push({ source, target, rel });

/* ── hub + chapters ─────────────────────────────────────────────── */
add('phone', 'S21 PHONE', 'Hub', 0, 14, 'Cover', 'The handoff is the success. Every key is in her name.',
  'One phone, two tracks. Care never breaks, and hope still reaches the world.', { chapter: 'cover', big: 1 });
add('ch.tracks', '01 · Tracks', 'Hub', 0, 7, '01 · Tracks', 'Protecting and building, at once',
  'One phone, two purposes. Track 1 is the safety net, Track 2 is the studio.', { chapter: 'tracks' });
add('ch.system', '02 · System', 'Hub', 0, 7, '02 · System', 'How it works',
  'The path data takes from the phone to the world: Termux, proot Ubuntu, MCP, Pages.', { chapter: 'system' });
add('ch.agents', '03 · Agents', 'Hub', 0, 7, '03 · Agents', 'Four robot friends',
  'A team, not a generalist. Writer, Fixer, Designer — with an Auditor in training.', { chapter: 'agents' });
add('ch.centers', '04 · Centers', 'Hub', 0, 7, '04 · Centers', 'Seven workshops',
  'Factory, gallery, broadcast tower, walkie-talkie, journal, webzine, lounge. Seven rooms.', { chapter: 'centers' });
add('ch.funnel', '05 · Funnel', 'Hub', 0, 7, '05 · Funnel', 'The content journey',
  'Seed, sprout, fruit. From a Designer Bot draft to my sister running it herself.', { chapter: 'funnel' });
add('ch.economics', '06 · Cost', 'Hub', 0, 7, '06 · Cost', 'How much per month',
  'About one streaming subscription. The core is ~$20; the Designer Bot is optional.', { chapter: 'economics' });
add('ch.install', '07 · Install', 'Hub', 0, 7, '07 · Setup', 'Three pastes and you are done',
  'Install two apps, paste the spell, check the browser. That is the whole setup.', { chapter: 'install' });
add('ch.library', '08 · Library', 'Hub', 0, 7, '08 · Library', 'The document shelf',
  'The repo read like a magazine shelf: rulebook, manual, guide, chronicle, textbook.', { chapter: 'library' });
add('ch.channels', '09 · Channels', 'Hub', 0, 7, '09 · Doors Outside', 'Doors open to the world',
  'GitHub, YouTube, Naver, Tistory, Discord — every key is in her name.', { chapter: 'channels' });
['ch.tracks', 'ch.system', 'ch.agents', 'ch.centers', 'ch.funnel', 'ch.economics', 'ch.install', 'ch.library', 'ch.channels']
  .forEach((c) => link('phone', c, 'chapter'));

/* ── 01 · two tracks ────────────────────────────────────────────── */
add('t.care', 'Track 1 · Care', 'Track', 1, 10, '01 · Tracks', 'Guardian Angel · 24/7 · location, battery, anomalies, escalation.',
  'The private safety net. Physically separate from the content stream. This track must never break.', { chapter: 'tracks', weight: 100, hot: 1 });
add('t.aspire', 'Track 2 · Hope', 'Track', 1, 9, '01 · Tracks', 'Dream Factory · mirroring the life she would have lived.',
  'A ghostwriter studio. GitHub factory, YouTube broadcast, Naver webzine, Discord lounge — one flow.', { chapter: 'tracks', weight: 85 });
add('t.separation', 'Clean split', 'Track', 1, 6, '01 · Tracks', 'The care stream never touches the content stream.',
  'Nothing from Track 1 leaves through any Track 2 channel. Ever.', { chapter: 'tracks' });
['t.care', 't.aspire', 't.separation'].forEach((c) => link('ch.tracks', c, 'contains'));

/* ── 02 · the stack ─────────────────────────────────────────────── */
add('m.phone', 'Galaxy S21', 'Module', 2, 10, '02 · System', 'Live on one phone.',
  'Everything runs on this one handset. There is no server room.', { chapter: 'system' });
add('m.termux', 'Termux', 'Module', 2, 8, '02 · System', 'The terminal on Android.',
  'Termux and Termux:API reach the phone sensors and files.', { chapter: 'system' });
add('m.ubuntu', 'proot Ubuntu', 'Module', 2, 7, '02 · System', 'Ubuntu without root.',
  'Full Linux tooling while the phone stays unrooted.', { chapter: 'system' });
add('m.daemon', 'care-daemon', 'Module', 2, 8, '02 · System', 'A care watcher on crontab.',
  'Zero AI dependency. Watches battery, location and anomalies, then escalates.', { chapter: 'system', hot: 1 });
add('m.mcp', 'phone-MCP', 'Module', 2, 7, '02 · System', 'The hands robots use to drive the phone.',
  'Two-way control: an agent sends a command, the phone returns the result.', { chapter: 'system' });
add('m.pages', 'GitHub Pages', 'Module', 2, 7, '02 · System', 'Where this webzine stands.',
  'The repo is the gallery. Auto-deployed, always current.', { chapter: 'system', href: 'https://helena751107.github.io/helena_phone/' });
['m.phone', 'm.termux', 'm.ubuntu', 'm.daemon', 'm.mcp', 'm.pages'].forEach((c) => link('ch.system', c, 'contains'));

/* ── 03 · four robot friends ────────────────────────────────────── */
add('a.cc', 'Writer Bot · cc', 'Agent', 3, 9, '03 · Agents', 'Lead · coach. Claude Code + DeepSeek. Main engine.',
  'Writes, organizes, codes, runs git and MCP — the one that directs the others. ~$0 / mo.', { chapter: 'agents' });
add('a.ds', 'Fixer Bot · ds', 'Agent', 3, 8, '03 · Agents', 'Mechanic. Aider + DeepSeek. No eyes.',
  'Short, cheap code repairs. The surgeon that keeps the Designer pool intact.', { chapter: 'agents' });
add('a.grok', 'Designer Bot · grok', 'Agent', 3, 9, '03 · Agents', 'Layout designer · PD. SuperGrok.',
  'Image, layout, video, research. Exactly two jobs, nothing more.', { chapter: 'agents' });
add('a.auditor', 'Auditor Bot', 'Agent', 3, 5, '03 · Agents', 'The fourth friend · referee. In training.',
  'Flags "that breaks the rules" and "that is dangerous". Arm\'s-length verification.', { chapter: 'agents' });
['a.cc', 'a.ds', 'a.grok', 'a.auditor'].forEach((c) => link('ch.agents', c, 'contains'));

/* ── 04 · seven workshops ───────────────────────────────────────── */
add('c.factory', '① Bread Factory', 'Module', 2, 8, '04 · Centers', 'Mixing room · GitHub · Live 100%.',
  'Where code, docs and scripts are made. Commits and pull requests are the flour.', { chapter: 'centers' });
add('c.showroom', '② Gallery', 'Module', 2, 7, '04 · Centers', 'Shop window · GitHub Pages · Live 100%.',
  'Where this webzine stands. The repo is the gallery.', { chapter: 'centers' });
add('c.tower', '③ Broadcast', 'Module', 2, 7, '04 · Centers', 'TV tower · YouTube · Prep 80%.',
  'The transmitter for finished courses and income.', { chapter: 'centers' });
add('c.intercom', '④ Walkie-Talkie', 'Module', 2, 7, '04 · Centers', 'Notes · Telegram · Live 100%.',
  'Robot reports, file drops, the meeting room. Radio between phone and human.', { chapter: 'centers' });
add('c.log', '⑤ Journal', 'Module', 2, 5, '04 · Centers', 'Records archive · Tistory · Manual 30%.',
  'Operating notes and retrospectives. The shelf that keeps the human touch.', { chapter: 'centers' });
add('c.webzine', '⑥ Webzine', 'Module', 2, 5, '04 · Centers', 'Bait · teaser · Naver Blog · Manual 25%.',
  'The mouth of the funnel. A Designer Bot draft pulls the traffic in.', { chapter: 'centers' });
add('c.lobby', '⑦ Lounge', 'Module', 2, 7, '04 · Centers', 'Living room · Discord · Live 100%.',
  'Real-time chat lounge. The front door the community walks in through.', { chapter: 'centers' });
['c.factory', 'c.showroom', 'c.tower', 'c.intercom', 'c.log', 'c.webzine', 'c.lobby'].forEach((c) => link('ch.centers', c, 'contains'));

/* ── 05 · the funnel ────────────────────────────────────────────── */
add('s.bait', '01 · Seed', 'Stage', 4, 7, '05 · Funnel', 'Naver webzine · Designer Bot draft 80%.',
  'Free, bait, teaser. The target is 80% finished — enough to grow.', { chapter: 'funnel' });
add('s.craft', '02 · Sprout', 'Stage', 4, 8, '05 · Funnel', 'YouTube course · Writer Bot finishes it.',
  'A grade that can be sold and turned into income. 100%.', { chapter: 'funnel' });
add('s.handoff', '03 · Fruit', 'Stage', 4, 9, '05 · Funnel', 'Handoff to my sister. Income, accounts, operations — all hers.',
  'Success = the handoff. When this stage ends, our job is done.', { chapter: 'funnel' });
['s.bait', 's.craft', 's.handoff'].forEach((c) => link('ch.funnel', c, 'contains'));
link('s.bait', 's.craft', 'flow');
link('s.craft', 's.handoff', 'flow');

/* ── 06 · economics ─────────────────────────────────────────────── */
add('e.core', 'Core ~$20', 'Module', 2, 7, '06 · Cost', 'Writer + Fixer · Claude Code + DeepSeek/Aider.',
  'Care and coding for about one streaming subscription. Nearly free.', { chapter: 'economics' });
add('e.grok', 'Designer · $30/mo', 'Module', 2, 6, '06 · Cost', 'Grok · layout design + documentary. Optional.',
  'The only meaningful fixed cost, and everything still runs without it.', { chapter: 'economics' });
add('e.gpu', 'No local GPU', 'Module', 2, 5, '06 · Cost', 'Zero local GPU. Multimodal lives in the cloud.',
  'No hardware investment. One phone finishes the job.', { chapter: 'economics' });
['e.core', 'e.grok', 'e.gpu'].forEach((c) => link('ch.economics', c, 'contains'));

/* ── 07 · install ───────────────────────────────────────────────── */
add('i.termux', 'Termux + API', 'Install', 6, 8, '07 · Setup', 'Two apps from F-Droid, battery set to unrestricted.',
  'Termux and Termux:API. Together they turn the phone into a terminal.', { chapter: 'install' });
add('i.oneliner', 'One-line spell', 'Install', 6, 9, '07 · Setup', 'Paste once.',
  'One curl line prepares proot Ubuntu and the working folder.', { chapter: 'install' });
add('i.manual', 'Picture guide', 'Install', 6, 7, '07 · Setup', 'App → paste → check the browser.',
  'Three pastes: GitHub user, GitHub token, DeepSeek token. Then it is automatic.', { chapter: 'install', href: 'https://helena751107.github.io/helena_phone/install-guide.html' });
add('i.manifest', 'manifest.json', 'Install', 6, 5, '07 · Setup', 'Add to home screen.',
  'The PWA manifest opens it like an app.', { chapter: 'install', href: 'https://helena751107.github.io/helena_phone/site-webmanifest.html' });
['i.termux', 'i.oneliner', 'i.manual', 'i.manifest'].forEach((c) => link('ch.install', c, 'contains'));

/* ── 08 · library ───────────────────────────────────────────────── */
add('l.constitution', 'CONSTITUTION', 'Channel', 5, 8, '08 · Library', '16 articles · who decides what.',
  'The law of this system. Handoff and ownership rules live here.', { chapter: 'library', href: 'https://helena751107.github.io/helena_phone/constitution.html' });
add('l.manual', 'Working Manual', 'Channel', 5, 7, '08 · Library', '4 robots · how the work gets done.',
  'The operating rules for the robot crew.', { chapter: 'library', href: 'https://helena751107.github.io/helena_phone/claude.html' });
add('l.guide', 'GUIDE', 'Channel', 5, 7, '08 · Library', '5-step guide · setup to broadcast.',
  'What to do after the install finishes.', { chapter: 'library', href: 'https://helena751107.github.io/helena_phone/guide.html' });
add('l.devlog', 'Devlog', 'Channel', 5, 6, '08 · Library', 'Journal · 99-devlog.',
  'Judgments and mistakes, written down while building.', { chapter: 'library', href: 'https://helena751107.github.io/helena_phone/notebook/99-devlog.html' });
add('l.textbook', 'Textbook', 'Channel', 5, 6, '08 · Library', 'The complete course.',
  'A learning path to follow from the beginning.', { chapter: 'library', href: 'https://helena751107.github.io/helena_phone/textbook.html' });
add('l.chronicle', 'Chronicle', 'Channel', 5, 6, '08 · Library', 'From birth to now.',
  'The record of this phone becoming a workstation.', { chapter: 'library', href: 'https://helena751107.github.io/helena_phone/chronicle.html' });
['l.constitution', 'l.manual', 'l.guide', 'l.devlog', 'l.textbook', 'l.chronicle'].forEach((c) => link('ch.library', c, 'contains'));

/* ── 09 · doors outside ─────────────────────────────────────────── */
add('x.github', 'GitHub', 'Channel', 5, 7, '09 · Channels', 'helena_phone · the main factory.',
  'Factory and gallery share one repo.', { chapter: 'channels', href: 'https://github.com/helena751107/helena_phone' });
add('x.youtube', 'YouTube', 'Channel', 5, 7, '09 · Channels', '@helena_phone · the TV station.',
  'Where courses and testimony are broadcast.', { chapter: 'channels', href: 'https://www.youtube.com/@helena_phone' });
add('x.naver', 'Naver', 'Channel', 5, 6, '09 · Channels', 'helena1975 · webzine bait.',
  'The mouth of the funnel. Free writing and teasers.', { chapter: 'channels', href: 'https://m.blog.naver.com/helena1975' });
add('x.tistory', 'Tistory', 'Channel', 5, 5, '09 · Channels', 'Journal.',
  'Where operating notes and retrospectives pile up.', { chapter: 'channels', href: 'https://galaxys21-pwuser.tistory.com' });
add('x.discord', 'Discord', 'Channel', 5, 6, '09 · Channels', 'Lounge.',
  'Real-time conversation. No sensitive records kept here.', { chapter: 'channels', href: 'https://discord.gg/JTYSZv2WQE' });
add('x.log', 'Helana Log', 'Channel', 5, 5, '09 · Channels', 'Study notes.',
  'The notebook shelf that grew beside the workshop.', { chapter: 'channels', href: 'https://helena751107.github.io/helana_log/' });
add('x.faith', 'Faith', 'Channel', 5, 5, '09 · Channels', 'Faith hub.',
  'The faith satellite of the S21 ecosystem.', { chapter: 'channels', href: 'https://helena751107.github.io/helana-faith/' });
add('x.piano', 'Piano', 'Channel', 5, 5, '09 · Channels', 'Practice room.',
  'Same name, another room.', { chapter: 'channels', href: 'https://helena751107.github.io/helena-piano/' });
add('x.metalcare', 'MetalCare', 'Channel', 5, 5, '09 · Channels', 'Care hub.',
  'Where the care documents and tools gather.', { chapter: 'channels', href: 'https://helena751107.github.io/helena-metalcare/' });
add('x.programming', 'Programming', 'Channel', 5, 5, '09 · Channels', 'Engineering room.',
  'The toolkit shelf for the robots.', { chapter: 'channels', href: 'https://helena751107.github.io/helena-programming/' });
['x.github', 'x.youtube', 'x.naver', 'x.tistory', 'x.discord', 'x.log', 'x.faith', 'x.piano', 'x.metalcare', 'x.programming'].forEach((c) => link('ch.channels', c, 'contains'));

/* ── cross-relations: the workstation logic ────────────────────── */
[['t.care', 'm.daemon'], ['t.care', 'm.phone'], ['t.care', 'c.intercom'],
 ['t.aspire', 'a.grok'], ['t.aspire', 'c.factory'], ['t.aspire', 's.bait'],
 ['t.separation', 't.care'], ['t.separation', 't.aspire'],
 ['m.phone', 'm.termux'], ['m.termux', 'm.ubuntu'], ['m.ubuntu', 'm.mcp'], ['m.mcp', 'a.cc'],
 ['m.pages', 'c.showroom'], ['m.daemon', 'c.intercom'],
 ['a.cc', 'c.factory'], ['a.cc', 'c.showroom'], ['a.cc', 's.craft'], ['a.cc', 'i.oneliner'],
 ['a.ds', 'c.factory'], ['a.ds', 'e.core'], ['a.cc', 'e.core'],
 ['a.grok', 'c.webzine'], ['a.grok', 'c.tower'], ['a.grok', 'e.grok'], ['a.grok', 's.bait'],
 ['a.auditor', 'c.intercom'], ['a.auditor', 'l.constitution'],
 ['c.factory', 'x.github'], ['c.showroom', 'x.github'], ['c.tower', 'x.youtube'],
 ['c.webzine', 'x.naver'], ['c.log', 'x.tistory'], ['c.lobby', 'x.discord'],
 ['s.bait', 'c.webzine'], ['s.craft', 'c.tower'], ['s.handoff', 'phone'], ['s.handoff', 'l.constitution'],
 ['e.core', 'm.phone'], ['e.grok', 'a.grok'], ['e.gpu', 'a.grok'],
 ['i.termux', 'm.termux'], ['i.oneliner', 'm.ubuntu'], ['i.manual', 'l.guide'], ['i.manifest', 'm.pages'],
 ['l.constitution', 't.care'], ['l.manual', 'a.cc'], ['l.guide', 'i.manual'], ['l.devlog', 'c.log'], ['l.chronicle', 'phone'],
 ['x.faith', 'phone'], ['x.metalcare', 't.care'], ['x.piano', 'phone'], ['x.log', 'l.devlog'], ['x.programming', 'c.factory']
].forEach(([a, b]) => link(a, b, 'support'));

/* ── deterministic layout: chapter ring, entities orbiting their chapter ── */
const chapterOf = {};
SECTIONS.forEach((ch, i) => { chapterOf[ch] = i; });
const chapters = SECTIONS.slice(1).map((s) => 'ch.' + s);
const byId = new Map(N.map((n) => [n.id, n]));
const chapterPos = {};
N.forEach((n) => {
  if (n.id === 'phone') { n.pos = [0, 46, 0]; return; }
  if (n.id.startsWith('ch.')) {
    const k = chapters.indexOf(n.id), a = (k / chapters.length) * Math.PI * 2 - Math.PI / 2;
    n.pos = [Math.cos(a) * 330, 36 + Math.sin(k * 1.7) * 38, Math.sin(a) * 330];
    chapterPos[n.chapter] = n.pos;
  }
});
const counts = {};
N.forEach((n) => { if (!n.id.startsWith('ch.') && n.id !== 'phone') counts[n.chapter] = (counts[n.chapter] || 0) + 1; });
const seen = {};
N.forEach((n) => {
  if (n.id === 'phone' || n.id.startsWith('ch.')) return;
  const base = chapterPos[n.chapter] || [0, 0, 0];
  const k = (seen[n.chapter] = (seen[n.chapter] || 0) + 1) - 1;
  const a = k * 2.399963 + chapterOf[n.chapter] * 0.7;
  const r = 74 + (k % 3) * 26;
  const y = Math.sin(k * 1.3 + 0.6) * 46 + (k % 2 ? 16 : -12);
  n.pos = [base[0] + Math.cos(a) * r, base[1] + y, base[2] + Math.sin(a) * r];
});

export const NODES = N;
export const LINKS = L.filter((l) => byId.has(l.source) && byId.has(l.target));
export const CHAPTER_IDS = chapters;
export const chapterIndex = (id) => SECTIONS.indexOf(String(id || '').replace(/^ch\./, ''));
export const stats = {
  nodes: NODES.length,
  relations: LINKS.length,
  chapters: chapters.length,
  sources: new Set(NODES.map((n) => n.ref)).size
};
