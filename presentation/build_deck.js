// Builds nachalniki_logistics.pptx next to this script (Ukrainian draft deck).
// Running it overwrites the PPTX, so manual edits made in PowerPoint are lost.
// Build: see README.md in this folder.
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));

const OUT = path.join(__dirname, "nachalniki_logistics.pptx");
const IMG_DIR = path.join(__dirname, "..", "docs", "slides", "img");
const REPO_URL = "https://github.com/Badabuba/nachalniki-logistics";

const K = {
  navy: "1B2A41", card: "24364F", teal: "0F7C80", tealLight: "6CC5C9",
  amber: "E8A33D", amberDark: "8A5A12", amberFill: "FDF3E1",
  green: "2E7D4F", grey: "F3F5F7", line: "D5DBE1", muted: "5B6573", soft: "C9D3DE", white: "FFFFFF",
};
const THEME = {
  name: "Nachalniki Logistics",
  headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: {
    dk1: K.navy, lt1: K.white, dk2: K.card, lt2: K.grey,
    accent1: K.teal, accent2: K.amber, accent3: K.green, accent4: K.amberDark,
    accent5: K.muted, accent6: K.tealLight, hlink: K.teal, folHlink: K.muted,
  },
};
const HEAD = "Cambria", BODY = "Calibri", CODE = "Courier New";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.title = "Logistics Lakehouse — «начальніки»";
pres.author = "Команда «начальніки»";
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: K.navy },
  objects: [],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: K.white },
  margin: [0.5, 0.5, 0.5, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 7.25, h: 0.7, fontFace: HEAD, fontSize: 26, bold: true, color: K.navy, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "«начальніки» · Logistics · TPC-H Lakehouse", options: { x: 0.5, y: 5.2, w: 5, h: 0.25, fontFace: BODY, fontSize: 10, color: K.muted, margin: 0 } } },
  ],
  slideNumber: { x: 9.1, y: 5.2, w: 0.4, h: 0.25, fontFace: BODY, fontSize: 10, color: K.muted, align: "right" },
});

// ---------- helpers ----------
const STATUS = {
  done: { text: "Реалізовано · 07.10.2026", fill: K.green, color: K.white },
  partial: { text: "Частково реалізовано", fill: K.teal, color: K.white },
  planned: { text: "Заплановано", fill: K.amber, color: K.navy },
  waiting: { text: "Очікує реалізації", fill: K.amber, color: K.navy },
};
function pill(slide, kind, x = 7.85, y = 0.47, w = 1.65) {
  const s = STATUS[kind];
  slide.addText(s.text, {
    shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.16, x, y, w, h: 0.34,
    fill: { color: s.fill }, color: s.color, fontFace: BODY, fontSize: 10, bold: true,
    align: "center", valign: "middle", margin: 0, objectName: "status",
  });
}
function placeholder(slide, { x, y, w, h, owner, text, size = 12 }) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.08, fill: { color: K.amberFill },
    line: { color: K.amber, width: 1.25, dashType: "dash" }, objectName: "placeholder",
  });
  slide.addText([
    { text: "ЗАПОВНИТИ · " + owner, options: { bold: true, color: K.amberDark, fontSize: 11, breakLine: true } },
    { text, options: { color: K.navy, fontSize: size } },
  ], { x: x + 0.12, y: y + 0.08, w: w - 0.24, h: h - 0.16, fontFace: BODY, valign: "middle", align: "left", margin: 0, isTextBox: true, paraSpaceAfter: 3 });
}
function card(slide, { x, y, w, h, title, body, titleColor = K.navy, fill = K.grey, bodySize = 12 }) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill } });
  slide.addText([
    { text: title, options: { bold: true, fontSize: 14, color: titleColor, breakLine: true } },
    { text: body, options: { fontSize: bodySize, color: K.navy } },
  ], { x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h - 0.2, fontFace: BODY, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 4 });
}
function contentSlide(title, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}

// ---------- 1. Title + team + repo ----------
pres.addSection({ title: "Вступ" });
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Вступ" });
  s.addText("UCU · Big Data · Group Assignment 1", { x: 0.5, y: 0.4, w: 9, h: 0.3, fontFace: BODY, fontSize: 12, color: K.tealLight, margin: 0, isTextBox: true });
  s.addText("Logistics Lakehouse на TPC-H", { x: 0.5, y: 0.72, w: 9, h: 0.7, fontFace: HEAD, fontSize: 36, bold: true, color: K.white, margin: 0, isTextBox: true });
  s.addText("Команда «начальніки» · профіль Logistics · Bronze → Silver → Gold у Databricks", { x: 0.5, y: 1.42, w: 9, h: 0.4, fontFace: BODY, fontSize: 15, color: K.soft, margin: 0, isTextBox: true });

  const team = [
    { name: "Назар", stage: "Етап 1 · основа і Bronze", scope: "Репозиторій і uv, 00_config, Bronze для 8 таблиць, профілювання, дозволені значення", status: "done" },
    { name: "Ярополк", stage: "Етап 2 · Silver і якість даних", scope: "3NF, staging, валідація і dq_check_results, публікація Silver, ER-діаграма", status: "waiting" },
    { name: "Макс", stage: "Етап 3 · Gold, аналіз, інтеграція", scope: "Gold, run_pipeline, відповіді Q1–Q4, моніторинг, фінальний README і презентація", status: "waiting" },
  ];
  team.forEach((m, i) => {
    const x = 0.5 + i * 3.075, y = 2.1, w = 2.85, h = 2.35;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.1, fill: { color: K.card }, line: { color: K.card }, objectName: "team-card-" + (i + 1) });
    s.addText([
      { text: m.name, options: { fontFace: HEAD, fontSize: 20, bold: true, color: K.white, breakLine: true } },
      { text: m.stage, options: { fontSize: 12, bold: true, color: K.tealLight, breakLine: true } },
      { text: m.scope, options: { fontSize: 12, color: K.soft } },
    ], { x: x + 0.18, y: y + 0.14, w: w - 0.36, h: 1.6, fontFace: BODY, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 4 });
    pill(s, m.status, x + 0.18, y + h - 0.5, 2.0);
  });
  s.addText([
    { text: "Репозиторій: ", options: { color: K.soft } },
    { text: "github.com/Badabuba/nachalniki-logistics", options: { color: K.tealLight, bold: true, hyperlink: { url: REPO_URL } } },
  ], { x: 0.5, y: 4.75, w: 9, h: 0.35, fontFace: BODY, fontSize: 14, margin: 0, isTextBox: true });

  s.addNotes(
`Доповідає: Назар · ≈0:30

Що сказати: Ми команда «начальніки», профіль Logistics. Переносимо TPC-H із samples.tpch у lakehouse Bronze → Silver → Gold у Databricks і відповідаємо на чотири питання логістики про терміни доставки. Робота розбита на три послідовні етапи: я відповідаю за основу і Bronze, Ярополк — за Silver і якість даних, Макс — за Gold, аналіз та інтеграцію. Кожен презентує свою частину. Код і презентація — у публічному репозиторії, посилання на слайді.

Стан на 07.10.2026: етап 1 реалізовано і запущено в Databricks; етапи 2 і 3 ще не реалізовані. Перед виступом Макс оновлює статуси на картках за фактичним станом (з доказами).

План часу (≈6:00): 1 — 0:30 · 2 — 0:20 · 3 — 0:45 · 4 — 0:40 · 5 — 0:30 · 6 (демо) — 1:00 · 7 — 0:45 · 8 — 0:30 · 9 — 0:40 · 10 — 0:20. Слайди 11–12 (додаток) не презентуються.`);
}

// ---------- 2. Architecture ----------
{
  const s = contentSlide("Архітектура: від samples.tpch до Gold", "Вступ");
  pill(s, "partial");
  const steps = [
    { name: "Джерело", nb: "samples.tpch", st: "done" },
    { name: "Bronze", nb: "01_bronze_ingest", st: "done" },
    { name: "Staging", nb: "02_silver_stage", st: "planned" },
    { name: "Валідація", nb: "03_validate", st: "planned" },
    { name: "Silver", nb: "04_silver_publish", st: "planned" },
    { name: "Gold", nb: "05_gold_build", st: "planned" },
  ];
  const w = 1.38, gap = 0.144, y = 1.3;
  steps.forEach((p, i) => {
    const x = 0.5 + i * (w + gap);
    const done = p.st === "done";
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.05, rectRadius: 0.08, fill: { color: done ? K.navy : K.white }, line: { color: done ? K.navy : K.amber, width: 1.5, dashType: done ? "solid" : "dash" }, objectName: "flow-" + p.name });
    s.addText([
      { text: p.name, options: { fontSize: 15, bold: true, color: done ? K.white : K.navy, breakLine: true } },
      { text: p.nb, options: { fontSize: 8.5, fontFace: CODE, color: done ? K.soft : K.muted } },
    ], { x: x + 0.02, y: y + 0.08, w: w - 0.04, h: 0.89, fontFace: BODY, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(done ? "реалізовано" : "заплановано", { x, y: y + 1.12, w, h: 0.28, fontFace: BODY, fontSize: 11, bold: true, color: done ? K.green : K.amberDark, align: "center", margin: 0, isTextBox: true });
    if (i < steps.length - 1) {
      s.addShape(pres.shapes.RIGHT_ARROW, { x: x + w + 0.017, y: y + 0.42, w: 0.11, h: 0.2, fill: { color: K.muted }, line: { color: K.muted } });
    }
  });
  s.addText("Аналіз: 06_analysis читає лише Gold і журнал запусків; run_pipeline виконує кроки 01–05 по черзі", { x: 0.5, y: 2.78, w: 9, h: 0.3, fontFace: BODY, fontSize: 12, color: K.muted, margin: 0, isTextBox: true });

  card(s, { x: 0.5, y: 3.3, w: 2.85, h: 1.5, title: "Один конфіг", titleColor: K.green,
    body: "00_config: параметри catalog, schema_prefix, source задають усі схеми {prefix}_bronze … _audit. Реалізовано." });
  card(s, { x: 3.575, y: 3.3, w: 2.85, h: 1.5, title: "Ніщо не губиться мовчки", titleColor: K.amberDark,
    body: "Staging зберігає всі рядки; блокуюче порушення зупиняє публікацію Silver і Gold. Заплановано." });
  card(s, { x: 6.65, y: 3.3, w: 2.85, h: 1.5, title: "Аудит лише дописується", titleColor: K.amberDark,
    body: "pipeline_runs і dq_check_results фіксують кожен запуск за run_id. Заплановано." });

  s.addNotes(
`Доповідає: Назар · ≈0:20

Що сказати: Конвеєр має п'ять кроків. Bronze — точна копія джерела. Staging — типізована копія без жодної фільтрації. Валідація перевіряє правила і пише результати в журнал якості. Silver публікується лише якщо всі блокуючі правила пройшли. Gold будується з Silver під питання логістики. Зараз реалізовано й запущено джерело → Bronze і спільний конфіг; решта — затверджений дизайн, який реалізують Ярополк і Макс.

Перед виступом (Макс): коли кроки буде реалізовано і запущено, змініть позначки «заплановано» на «реалізовано» (пунктирна рамка → суцільна темна) і статус угорі на «Реалізовано · <дата>». Не змінюйте позначку без успішного запуску.`);
}

// ---------- 3. Stage 1 ----------
pres.addSection({ title: "Етап 1" });
{
  const s = contentSlide("Етап 1: конфіг, Bronze і профілювання", "Етап 1");
  pill(s, "done");
  const stats = [
    { big: "8 / 8", label: "таблиць Bronze збігаються з samples.tpch: назви, типи колонок і кількість рядків" },
    { big: "+2", label: "колонки метаданих: _ingested_at і _source_table; решта — як у джерелі" },
    { big: "1–7", label: "рядків на замовлення (медіана 4); замовлень без рядків — 0" },
  ];
  stats.forEach((t, i) => {
    const x = 0.5 + i * 3.075;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.2, w: 2.85, h: 1.25, rectRadius: 0.08, fill: { color: K.grey }, line: { color: K.grey } });
    s.addText(t.big, { x: x + 0.15, y: 1.27, w: 2.55, h: 0.55, fontFace: HEAD, fontSize: 30, bold: true, color: K.teal, margin: 0, isTextBox: true });
    s.addText(t.label, { x: x + 0.15, y: 1.82, w: 2.55, h: 0.58, fontFace: BODY, fontSize: 11, color: K.navy, valign: "top", margin: 0, isTextBox: true });
  });

  s.addText("Дозволені значення: профілювання Bronze + звірка зі специфікацією TPC-H rev. 3.0.1", { x: 0.5, y: 2.65, w: 9, h: 0.32, fontFace: BODY, fontSize: 14, bold: true, color: K.navy, margin: 0, isTextBox: true });
  const lists = [
    ["l_shipmode", ["AIR", "FOB", "MAIL", "RAIL", "REG AIR", "SHIP", "TRUCK"]],
    ["l_returnflag", ["A", "N", "R"]],
    ["l_linestatus", ["F", "O"]],
  ];
  lists.forEach(([col, vals], r) => {
    const y = 3.08 + r * 0.44;
    s.addText(col, { x: 0.5, y, w: 1.55, h: 0.34, fontFace: CODE, fontSize: 12, color: K.navy, valign: "middle", margin: 0, isTextBox: true });
    let x = 2.1;
    vals.forEach((v) => {
      const w = 0.1 * v.length + 0.3;
      s.addText(v, { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.1, x, y, w, h: 0.34, fill: { color: K.white }, line: { color: K.teal, width: 1 }, fontFace: CODE, fontSize: 12, color: K.teal, align: "center", valign: "middle", margin: 0 });
      x += w + 0.1;
    });
  });
  s.addText("Кожне значення і спостерігається в даних, і задокументоване; NULL і зайвих пробілів немає. Нове значення не додається мовчки — валідація впаде, рядки не відкидаються. Пріоритет «терміново» = 1-URGENT.", { x: 0.5, y: 4.42, w: 9, h: 0.6, fontFace: BODY, fontSize: 12, color: K.navy, valign: "top", margin: 0, isTextBox: true });

  s.addNotes(
`Доповідає: Назар · ≈0:45

Що сказати: Усе починається з 00_config. Три параметри — catalog, schema_prefix і source — визначають, звідки читаємо і куди пишемо, тож той самий код можна запустити в іншому workspace або з іншим префіксом. Ніде інде немає жорстко заданих назв схем чи кількостей рядків. Кожен запуск отримує новий run_id, а дочірні кроки без нього не стартують.

Bronze — це SELECT * для всіх 8 таблиць плюс дві колонки метаданих. Ноутбук сам перевіряє, що колонки, типи й кількості рядків збігаються з джерелом, і падає, якщо ні. У запуску 07.10.2026 збіглися всі 8 таблиць, наприклад lineitem — 29 999 795 рядків.

Дозволені значення ми не вгадували: порахували всі значення разом з їхньою довжиною, щоб побачити приховані пробіли, і звірили зі специфікацією TPC-H rev. 3.0.1 (розділи 4.2.2.13 і 4.2.3). Неочікуваних значень немає, тож списки — рівно задокументовані значення.

Джерела чисел: вивід запусків 01_bronze_ingest і profile_source від 07.10.2026 (serverless-job у Databricks), збережений у репозиторії; візуалізації виводу — у додатку. Портативність (запуск з іншим schema_prefix) ще не перевірено — це частина етапу 3, тому не стверджуйте, що її доведено.`);
}

// ---------- 4. Validation approach ----------
pres.addSection({ title: "Якість і Silver" });
{
  const s = contentSlide("Валідація: чому даним можна вірити", "Якість і Silver");
  pill(s, "planned");
  const groups = [
    { t: "Дати", b: "відвантаження не раніше замовлення, отримання не раніше відвантаження; дати не NULL" },
    { t: "Категорії", b: "l_shipmode, l_returnflag, l_linestatus — лише з дозволених списків етапу 1" },
    { t: "Зв'язки", b: "кожен рядок має замовлення, кожне замовлення має рядки; PK і FK через anti-join, зокрема (l_partkey, l_suppkey) → partsupp" },
    { t: "Повнота", b: "кількість рядків джерело = Bronze = staging; Gold без втрат і дублів" },
  ];
  groups.forEach((g, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    card(s, { x: 0.5 + col * 2.6, y: 1.2 + row * 1.9, w: 2.45, h: 1.75, title: g.t, body: g.b, titleColor: K.teal });
  });
  // principles panel
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.85, y: 1.2, w: 3.65, h: 3.65, rectRadius: 0.08, fill: { color: K.navy }, line: { color: K.navy } });
  s.addText([
    { text: "Правила роботи", options: { fontFace: HEAD, fontSize: 16, bold: true, color: K.white, breakLine: true } },
    { text: "Усі правила блокуючі: одне порушення — запуск зупиняється, Silver і Gold не публікуються.", options: { bullet: { indent: 14 }, fontSize: 12, color: K.white, breakLine: true } },
    { text: "Невалідні рядки не відкидаються: кількість порушень і до 10 ключів-прикладів пишуться в dq_check_results.", options: { bullet: { indent: 14 }, fontSize: 12, color: K.white, breakLine: true } },
    { text: "Запізнення (receipt > commit) — валідні дані, а не помилка: саме їх ми аналізуємо.", options: { bullet: { indent: 14 }, fontSize: 12, color: K.tealLight, bold: true, breakLine: true } },
    { text: "PK/FK у Databricks інформаційні, тому цілісність доводять anti-join перевірки.", options: { bullet: { indent: 14 }, fontSize: 12, color: K.white } },
  ], { x: 6.05, y: 1.32, w: 3.3, h: 3.42, fontFace: BODY, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 6 });

  s.addNotes(
`Доповідає: Ярополк · ≈0:40

Що сказати: Правила взято з профілю Logistics. Дати мають бути послідовними, категорії — лише з дозволених списків, які ми отримали профілюванням, а кожен рядок має належати існуючому замовленню, і жодне замовлення не може бути без рядків. Додатково перевіряємо унікальність ключів, усі зовнішні ключі та повноту між шарами. Головний принцип: ми нічого не відкидаємо мовчки. Якщо правило не пройшло, запуск зупиняється і Silver не оновлюється, а в журналі видно, скільки порушень і які ключі. Запізнення — це не помилка даних, а саме те, що ми аналізуємо.

СТАН: це затверджений дизайн, валідацію ще не реалізовано. Статус «Заплановано» залишається, доки не буде успішного запуску.

ЩО ДОДАТИ (Ярополк): після реалізації 02_silver_stage, dq_helpers, 03_validate і 04_silver_publish — звірити формулювання груп правил з кодом (додати або прибрати правило, якщо фінальний набір інший), змінити статус на «Реалізовано · <дата запуску>». Правило «commit date не раніше дати замовлення» — наша інтерпретація вимоги «дати узгоджені з батьківським замовленням»; якщо воно лишиться в коді, сказати це одним реченням.`);
}

// ---------- 5. Silver 3NF + ER ----------
{
  const s = contentSlide("Silver: 8 таблиць у 3NF і ER-діаграма", "Якість і Silver");
  pill(s, "planned");
  s.addText([
    { text: "Що вже відомо", options: { fontSize: 14, bold: true, color: K.navy, breakLine: true } },
    { text: "Назви колонок як у TPC-H, типи — з DESCRIBE джерела.", options: { bullet: { indent: 14 }, fontSize: 12, color: K.navy, breakLine: true } },
    { text: "Перевірено на тестовій таблиці 07.10.2026: CHECK блокує некоректну вставку, PRIMARY KEY дублікат не блокує.", options: { bullet: { indent: 14 }, fontSize: 12, color: K.navy, breakLine: true } },
    { text: "Тому цілісність доводить валідація, а не оголошені ключі.", options: { bullet: { indent: 14 }, fontSize: 12, color: K.navy } },
  ], { x: 0.5, y: 1.2, w: 3.3, h: 2.15, fontFace: BODY, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 5 });
  placeholder(s, { x: 0.5, y: 3.5, w: 3.3, h: 1.5, owner: "Ярополк", size: 11,
    text: "Результат 3NF: які кандидати у функціональні залежності перевірено на даних і висновок (чи потрібна декомпозиція)." });
  placeholder(s, { x: 4.05, y: 1.2, w: 5.45, h: 3.8, owner: "Ярополк", size: 13,
    text: "Скриншот ER-діаграми опублікованих Silver-таблиць (8 таблиць, PK/FK, двоколонковий зв'язок lineitem → partsupp). Лише реальний скриншот із Databricks або рендер діаграми, звіреної з DESCRIBE опублікованих таблиць." });

  s.addNotes(
`Доповідає: Ярополк · ≈0:30

Що сказати: Silver містить усі 8 таблиць TPC-H з оригінальними назвами колонок. Ми показуємо 3NF не копіюванням джерела, а перевіркою кандидатів у функціональні залежності на даних. NOT NULL і CHECK у Databricks реально блокують дані, а PK/FK лише інформаційні — це ми перевірили на тестовій таблиці, тому цілісність доводимо правилами валідації. [Далі — коротко про ER-діаграму і висновок 3NF.]

СТАН: Silver ще не реалізовано. Факт про CHECK і PK перевірено 07.10.2026 на тимчасовій тестовій таблиці, а не на Silver.

ЩО ДОДАТИ (Ярополк):
1. Великий плейсхолдер — замінити скриншотом ER-діаграми саме опублікованих Silver-таблиць (Catalog Explorer або рендер діаграми, звіреної з DESCRIBE). Не вставляти чернеткову діаграму з дизайну як результат. Підпис: джерело і дата.
2. Малий плейсхолдер — підсумок 3NF: перевірені кандидати FD (наприклад p_brand → p_mfgr), результат кожного і чи була декомпозиція.
3. Після публікації Silver змінити статус на «Реалізовано · <дата>».`);
}

// ---------- 6. Demo ----------
pres.addSection({ title: "Демо" });
{
  const s = contentSlide("Демо: готовий запуск і збій", "Демо");
  pill(s, "planned");
  const steps = [
    ["0:15", "Завершений запуск run_pipeline: рядок succeeded у pipeline_runs"],
    ["0:15", "dq_check_results для того ж run_id: усі правила passed"],
    ["0:20", "Підготовлений збій: некоректний рядок → правило не пройшло, Silver і Gold не оновлено"],
    ["0:10", "06_analysis відмовляється показувати результати застарілого запуску"],
  ];
  steps.forEach(([t, txt], i) => {
    const y = 1.2 + i * 0.95;
    s.addText(String(i + 1), { shape: pres.shapes.OVAL, x: 0.5, y, w: 0.5, h: 0.5, fill: { color: K.teal }, color: K.white, fontFace: HEAD, fontSize: 16, bold: true, align: "center", valign: "middle", margin: 0 });
    s.addText([
      { text: t + "  ", options: { bold: true, color: K.teal } },
      { text: txt, options: { color: K.navy } },
    ], { x: 1.15, y: y - 0.05, w: 3.15, h: 0.8, fontFace: BODY, fontSize: 12, valign: "top", margin: 0, isTextBox: true });
  });
  placeholder(s, { x: 4.5, y: 1.2, w: 5.0, h: 1.8, owner: "Макс", size: 12,
    text: "Скриншот завершеного запуску: pipeline_runs (started → succeeded) і dq_check_results цього run_id, усі passed = true." });
  placeholder(s, { x: 4.5, y: 3.2, w: 5.0, h: 1.8, owner: "Ярополк + Макс", size: 12,
    text: "Скриншот підготовленого збою: правило з passed = false, ключі-приклади, відсутній succeeded; повідомлення 06_analysis про відмову." });

  s.addNotes(
`Доповідають: Макс (кроки 1, 2, 4) і Ярополк (крок 3) · ≈1:00

Як проводити: НЕ запускайте повний конвеєр під час виступу — він займає кілька хвилин. Заздалегідь відкрийте вкладки Databricks з уже завершеним успішним запуском і з уже виконаним прикладом збою. Якщо інтернет чи workspace недоступні — показуйте скриншоти з цього слайда.

Що сказати:
1. (Макс) Ось останній запуск run_pipeline: у pipeline_runs для його run_id є started і succeeded.
2. (Макс) У dq_check_results для того самого run_id усі правила мають passed = true.
3. (Ярополк) А це підготовлений приклад: ми додали некоректний рядок (наприклад, отримання раніше відвантаження). Правило не пройшло, видно кількість порушень і ключі, запуск зупинився, Silver і Gold не змінилися.
4. (Макс) Після такого запуску 06_analysis не показує результати, бо останній запуск не succeeded.

СТАН: run_pipeline, журнали аудиту, валідацію і 06_analysis ще не реалізовано.

ЩО ДОДАТИ:
- Макс: скриншот успішного запуску (pipeline_runs + dq_check_results, з run_id і датою); скриншот відмови 06_analysis.
- Ярополк: підготовлений приклад збою (окремий schema_prefix, щоб не зіпсувати основні таблиці) і його скриншот.
- Обидва: прогнати демо з таймером; разом не більше 1:00.`);
}

// ---------- 7. Q1 + Q3 ----------
pres.addSection({ title: "Відповіді" });
function questionColumn(s, { x, w, q, chart, answer, code, owner = "Макс", chartH = 1.85 }) {
  s.addText(q, { x, y: 1.12, w, h: 0.62, fontFace: BODY, fontSize: 12, bold: true, color: K.navy, valign: "top", margin: 0, isTextBox: true });
  placeholder(s, { x, y: 1.8, w, h: chartH, owner, text: chart, size: 11 });
  placeholder(s, { x, y: 1.8 + chartH + 0.12, w, h: 0.78, owner, text: answer, size: 11 });
  s.addText([
    { text: "Код: ", options: { bold: true, color: K.muted, fontFace: BODY } },
    { text: code, options: { color: K.muted, fontFace: CODE } },
  ], { x, y: 1.8 + chartH + 0.98, w, h: 0.3, fontSize: 10, valign: "middle", margin: 0, isTextBox: true });
}
{
  const s = contentSlide("Q1 і Q3: доставка за ship mode", "Відповіді");
  pill(s, "planned");
  questionColumn(s, { x: 0.5, w: 4.35,
    q: "Q1. Медіана і p90 часу доставки (ship → receipt) за ship mode. Який найшвидший, а який найпередбачуваніший?",
    chart: "Графік: стовпці p50 і p90 transit_days за ship mode + таблиця розкиду (p90 − p50).",
    answer: "Відповідь: найшвидший = найменша медіана; найпередбачуваніший = найменший p90 − p50.",
    code: "06_analysis · agg_ship_mode_performance" });
  questionColumn(s, { x: 5.15, w: 4.35,
    q: "Q3. Яка частка рядків отримана після commit date для кожного ship mode? Який найгірший?",
    chart: "Графік: стовпці delay_rate за ship mode з кількістю рядків.",
    answer: "Відповідь: ship mode з найбільшою часткою запізнень і її значення.",
    code: "06_analysis · agg_ship_mode_performance" });

  s.addNotes(
`Доповідає: Макс · ≈0:45

Що сказати (після заповнення): Q1 — швидкість і передбачуваність різні питання: швидкість — це медіана, тобто типова доставка, а передбачуваність — розкид, наскільки далеко хвіст p90 від медіани. Режим може мати низьку медіану, але довгий хвіст. [Назвати найшвидший і найпередбачуваніший режими з числами.] Q3 — частка рядків, отриманих пізніше commit date. [Назвати найгірший режим і його частку, з кількістю рядків.] Якщо різниця між режимами мала, так і сказати, без переінтерпретації.

СТАН: Gold і 06_analysis ще не реалізовано; чисел немає. Не вигадувати й не оцінювати числа заздалегідь.

ЩО ДОДАТИ (Макс):
1. Два скриншоти графіків з 06_analysis (графіки 1 і 3 з дизайну) з успішного запуску; підписати run_id і дату.
2. Короткі відповіді з фактичними числами, як у README «Results».
3. Рядок «Код»: залишити посилання на ноутбук і таблицю або замінити 2–3 рядками ключового SQL (percentile_cont для p50/p90; delay_rate = late / lines).
4. Визначення: transit_days = datediff(receipt, ship); рядок запізнився, якщо receipt > commit (receipt у день commit — вчасно).`);
}

// ---------- 8. Q2 ----------
{
  const s = contentSlide("Q2: замовлення проти рядків", "Відповіді");
  pill(s, "planned");
  s.addText("Q2. Замовлення повністю вчасне, лише якщо всі його рядки прибули до commit date. Яка частка таких замовлень і як вона відрізняється від частки вчасних рядків?", { x: 0.5, y: 1.12, w: 9, h: 0.6, fontFace: BODY, fontSize: 12, bold: true, color: K.navy, valign: "top", margin: 0, isTextBox: true });
  placeholder(s, { x: 0.5, y: 1.85, w: 5.4, h: 2.75, owner: "Макс", size: 12,
    text: "Графіки: (1) стовпці — частка вчасних рядків і частка повністю вчасних замовлень; (2) лінія — частка вчасних замовлень за кількістю рядків у замовленні (1–7)." });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.15, y: 1.85, w: 3.35, h: 1.3, rectRadius: 0.08, fill: { color: K.grey }, line: { color: K.grey } });
  s.addText([
    { text: "Чому є розрив", options: { bold: true, fontSize: 13, color: K.teal, breakLine: true } },
    { text: "Одне запізнення робить невчасним усе замовлення, тож що більше рядків, то менший шанс бути повністю вчасним. У даних 1–7 рядків на замовлення (медіана 4).", options: { fontSize: 11, color: K.navy } },
  ], { x: 6.3, y: 1.92, w: 3.05, h: 1.18, fontFace: BODY, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 3 });
  placeholder(s, { x: 6.15, y: 3.3, w: 3.35, h: 1.3, owner: "Макс", size: 11,
    text: "Відповідь: частка вчасних замовлень, частка вчасних рядків і різниця." });
  s.addText([
    { text: "Код: ", options: { bold: true, fontFace: BODY } },
    { text: "06_analysis · agg_on_time_summary, agg_on_time_by_line_count", options: { fontFace: CODE } },
  ], { x: 0.5, y: 4.75, w: 9, h: 0.3, fontSize: 10, color: K.muted, valign: "middle", margin: 0, isTextBox: true });

  s.addNotes(
`Доповідає: Макс · ≈0:30

Що сказати (після заповнення): Замовлення вчасне, лише коли вчасні всі його рядки, тож одне запізнення псує все замовлення. [Назвати обидві частки і різницю.] Не стверджуйте, що частка замовлень завжди менша: це залежить від того, як запізнення розподілені між замовленнями — показуйте фактичні числа. Розрив росте з кількістю рядків: [описати фактичну лінію за кількістю рядків 1–7]. Формулу p^n можна згадати лише як ілюстрацію за припущення незалежних рядків, а не як результат.

Уже перевірено (профілювання 07.10.2026): кожне замовлення має від 1 до 7 рядків, медіана 4, замовлень без рядків немає.

СТАН: Gold і 06_analysis ще не реалізовано.

ЩО ДОДАТИ (Макс):
1. Скриншот графіка 2 з 06_analysis (частки + розбивка за кількістю рядків), run_id і дата.
2. Відповідь з фактичними частками з agg_on_time_summary.
3. За бажанням — 2–3 рядки SQL визначення «повністю вчасне»: line_count ≥ 1 і late_line_count = 0.`);
}

// ---------- 9. Q4 + monitoring ----------
{
  const s = contentSlide("Q4 і моніторинг запізнень", "Відповіді");
  pill(s, "planned");
  questionColumn(s, { x: 0.5, w: 4.35,
    q: "Q4. Чи виконуються замовлення з пріоритетом 1-URGENT швидше за інші? Підтвердити числами.",
    chart: "Графік: медіана і p90 order_to_complete_days за пріоритетом, 1-URGENT виділено + таблиця n, медіана, p90, середнє.",
    answer: "Відповідь: так / ні / різниця несуттєва — з числами для urgent і решти.",
    code: "06_analysis · agg_urgency_fulfillment" });
  questionColumn(s, { x: 5.15, w: 4.35,
    q: "Моніторинг. Частка рядків, отриманих після commit date, за місяцями (commit month).",
    chart: "Графік: лінія delay_rate за місяцями з line_count; крайні місяці позначені як потенційно неповні.",
    answer: "Спостереження: стабільність тренду і помітні відхилення (з даних).",
    code: "06_analysis · agg_delay_rate_monthly" });

  s.addNotes(
`Доповідає: Макс · ≈0:40

Що сказати (після заповнення): Q4 — «виконано» для нас означає від дати замовлення до отримання останнього рядка. Терміновим вважається пріоритет 1-URGENT — це значення ми підтвердили профілюванням. [Порівняти urgent з рештою: n, медіана, p90, середнє; сказати, чи різниця суттєва.] Щоб показати, звідки різниця, окремо дивимося час до відвантаження і час доставки. Моніторинг: частку запізнень рахуємо за місяцем commit date, бо саме тоді настає термін обіцянки. Крайні місяці можуть бути неповними, ми їх позначаємо. [Одне речення про тренд.]

Уже перевірено (профілювання 07.10.2026): пріоритетів 5, терміновий — 1-URGENT.

СТАН: Gold, 06_analysis і моніторинг ще не реалізовано. Алерт — необов'язковий; згадувати лише якщо його зроблено.

ЩО ДОДАТИ (Макс):
1. Скриншот графіка 4 (Q4) і графіка 5 (моніторинг) з 06_analysis, run_id і дата.
2. Відповідь Q4 з числами з agg_urgency_fulfillment / agg_priority_fulfillment.
3. Одне речення про тренд, назвати крайні місяці з малою кількістю рядків за фактичними даними.`);
}

// ---------- 10. Challenges + summary ----------
pres.addSection({ title: "Підсумок" });
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Підсумок" });
  s.addText("Виклики і підсумок", { x: 0.5, y: 0.35, w: 9, h: 0.7, fontFace: HEAD, fontSize: 30, bold: true, color: K.white, margin: 0, isTextBox: true });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 1.3, w: 2.85, h: 2.4, rectRadius: 0.1, fill: { color: K.card }, line: { color: K.card } });
  s.addText([
    { text: "Назар · доступ", options: { fontFace: HEAD, fontSize: 15, bold: true, color: K.white, breakLine: true } },
    { text: "Перша спроба CREATE SCHEMA у каталозі workspace завершилась PERMISSION_DENIED. Після надання прав перевірки пройшли; право CREATE SCHEMA тепер — передумова в README.", options: { fontSize: 12, color: K.soft } },
  ], { x: 0.68, y: 1.45, w: 2.5, h: 2.1, fontFace: BODY, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 5 });

  [["Ярополк", 3.575], ["Макс", 6.65]].forEach(([who, x]) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.3, w: 2.85, h: 2.4, rectRadius: 0.1, fill: { color: K.card }, line: { color: K.amber, width: 1.25, dashType: "dash" } });
    s.addText([
      { text: "ЗАПОВНИТИ · " + who, options: { fontSize: 11, bold: true, color: K.amber, breakLine: true } },
      { text: "Реальний виклик етапу і як його вирішили (1–2 речення).", options: { fontSize: 12, color: K.soft } },
    ], { x: x + 0.18, y: 1.45, w: 2.5, h: 2.1, fontFace: BODY, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 5 });
  });

  s.addText([
    { text: "Репозиторій: ", options: { color: K.soft } },
    { text: "github.com/Badabuba/nachalniki-logistics", options: { color: K.tealLight, bold: true, hyperlink: { url: REPO_URL } } },
    { text: "   ·   код, README і ця презентація", options: { color: K.soft } },
  ], { x: 0.5, y: 4.15, w: 9, h: 0.35, fontFace: BODY, fontSize: 14, margin: 0, isTextBox: true });

  s.addNotes(
`Доповідають: усі, по одному реченню · ≈0:20

Що сказати: Назар — наша перша перешкода була доступ: створення схеми в каталозі workspace спершу заборонили, і запрацювало лише після надання прав, тож тепер це вказано як передумова в README. [Ярополк і Макс — по одному реченню про свій реальний виклик.] Завершення (Макс): одне речення з головною відповіддю для логістики і посилання на репозиторій.

ЩО ДОДАТИ:
- Ярополк: один реальний виклик етапу 2 (наприклад, з валідації або 3NF), лише якщо він справді був; без вигаданих історій.
- Макс: один реальний виклик етапу 3; фінальне речення-висновок з фактичних відповідей.
- Макс: перед здачею перевірити, що репозиторій публічний і README має посилання на презентацію.`);
}

// ---------- 11-12. Appendix ----------
pres.addSection({ title: "Додаток" });
const APPENDIX_CAPTION = "Рендер збереженого експорту запуску Databricks (jobs export-run) від 07.10.2026, обрізаний до таблиці результатів. Не знімок живого робочого простору.";
const APPENDIX_NOTES = `Додатковий слайд, не презентується в межах 6 хвилин — лише для запитань.

Зображення: рендер HTML-експорту запуску Databricks (jobs export-run) від 07.10.2026, обрізаний до таблиці результатів (оригінали в репозиторії: docs/slides/img/, експорт — checks/p2/outputs/). Це не скриншот живого workspace — так і казати, якщо запитають.`;
{
  const s = contentSlide("Додаток: перевірка Bronze", "Додаток");
  pill(s, "done");
  s.addText("01_bronze_ingest: кожна таблиця Bronze порівняна з samples.tpch", { x: 0.5, y: 1.1, w: 9, h: 0.3, fontFace: BODY, fontSize: 13, bold: true, color: K.navy, margin: 0, isTextBox: true });
  const bw = 9, bh = bw * 360 / 1480;
  // Crop the empty right side of the 1830 x 360 px render to its first 1480 px.
  s.addImage({ path: path.join(IMG_DIR, "bronze_check_20261007.png"), x: 0.5, y: 1.55, w: bw * 1830 / 1480, h: bh, sizing: { type: "crop", x: 0, y: 0, w: bw, h: bh }, altText: "Таблиця перевірки Bronze: 8 таблиць, ok = true" });
  s.addText(APPENDIX_CAPTION, { x: 0.5, y: 1.55 + bh + 0.15, w: 9, h: 0.45, fontFace: BODY, fontSize: 11, color: K.muted, valign: "top", margin: 0, isTextBox: true });
  s.addNotes(APPENDIX_NOTES);
}
{
  const s = contentSlide("Додаток: профілювання категорій", "Додаток");
  pill(s, "done");
  s.addText("profile_source: значення, довжина і кількість рядків", { x: 0.5, y: 1.1, w: 9, h: 0.3, fontFace: BODY, fontSize: 13, bold: true, color: K.navy, margin: 0, isTextBox: true });
  const ph = 3.5, pw = ph * 640 / 422;
  // Crop the empty right side of the 915 x 422 px render to its first 640 px.
  s.addImage({ path: path.join(IMG_DIR, "profiling_categorical_20261007.png"), x: 0.5, y: 1.55, w: pw * 915 / 640, h: ph, sizing: { type: "crop", x: 0, y: 0, w: pw, h: ph }, altText: "Значення l_linestatus, l_returnflag, l_shipmode з кількістю рядків" });
  s.addText(APPENDIX_CAPTION, { x: 0.8 + pw, y: 1.55, w: 9.5 - (0.8 + pw), h: 1.6, fontFace: BODY, fontSize: 11, color: K.muted, valign: "top", margin: 0, isTextBox: true });
  s.addNotes(APPENDIX_NOTES);
}

// pptxgenjs writes Office's default palette into the theme; replace it with ours so
// colors picked from the theme in PowerPoint match the deck.
async function applyThemeColors(file, theme) {
  const fs = require("fs");
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const part = "ppt/theme/theme1.xml";
  let xml = await zip.file(part).async("string");
  // Slot order in theme.colors follows the schema: dk1, lt1, dk2, lt2, accent1-6, hlink, folHlink.
  const body = Object.entries(theme.colors).map(([k, v]) => `<a:${k}><a:srgbClr val="${v}"/></a:${k}>`).join("");
  xml = xml.replace(/<a:clrScheme name="[^"]*">[\s\S]*?<\/a:clrScheme>/, `<a:clrScheme name="${theme.name}">${body}</a:clrScheme>`);
  zip.file(part, xml);
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyThemeColors(OUT, THEME);
  console.log("written", OUT);
})();
