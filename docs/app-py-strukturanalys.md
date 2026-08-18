---
title: Strukturanalys av app.py
description: Genomlysning av ansvarsområden och kopplingar i app.py (2772 rader) för att bedöma om en modulindelning är motiverad.
category: architecture
status: current
last_updated: 2026-08-18
sections:
  - Nuvarande ansvarsområden
  - Vad som förändras oberoende
  - Var kopplingarna är starka
  - Konkreta problem detta orsakar
  - Bedömning
---

# Strukturanalys av app.py (2772 rader)

Genomlysning gjord utan att röra kod. Syftet var att bedöma om den ökade
produktfunktionaliteten (papperskorg, röstdiktering, Role Insights,
Evidence-based Insights, vyfilter) har skapat tydliga naturliga moduler i
`app.py`, och om en uppdelning är motiverad just nu.

## Nuvarande ansvarsområden

| Område | Ungefärlig omfattning | Karaktär |
|---|---|---|
| Bootstrap/auth (`get_supabase`, `login_required`, Flask-config) | rad 1–100 | Infrastruktur, stabil, ändras nästan aldrig |
| Presentationsskal (`STYLE`, `NAV`, `HEAD_EXTRAS`, `SPLASH`, `page()`) | rad 103–368 | Delas av *alla* routes, stabil |
| Signal-formulär + CRUD (`SIGNAL_FORM_TEMPLATE`, `new_signal`, `edit_signal`, förslags-hantering) | rad 421–1909 (**~790 rader** för själva formulärblocket) | Det klart största och mest sammanflätade blocket |
| Insights/Role-insights-motor (`Insight`, `build_milestone_insights` … `build_role_insights`) | rad 647–1002 (~355 rader) | Ren aggregeringslogik, skriver aldrig data |
| Röst-AI (`VOICE_DRAFT_*`, `extract_voice_draft`) | rad 1003–1115 (~112 rader) | Anropar Claude, renderar sedan om signal-formuläret |
| Flöde/Papperskorg (`FEED_TEMPLATE`, `feed()`, delete/restore/klarmarkera) | rad 1911–2298 (~390 rader) | Nyligen omarbetad (vyfilter) |
| Hypoteser (templates + routes) | rad 2301–2492 (~190 rader) | Litet, självständigt |
| Översikt/Review (`REVIEW_TEMPLATE`, `review()`) | rad 2494–2640 (~145 rader) | Konsumerar insights-motorn |
| Idéer (`IDEA_TEMPLATE` + routes) | rad 2642–2772 (~130 rader) | Helt fristående — egen tabell, delar inga hjälpfunktioner |

## Vad som förändras oberoende

Titta man på de senaste commits (papperskorg, röstdiktering, Role Insights,
Evidence-based Insights, vyfilter) syns ett tydligt mönster: varje
feature-ändring har hållit sig inom **ett** av områdena ovan. Idéer,
Hypoteser, Insights-motorn och Röst-AI:t har inte behövt röras när
Flödet/Papperskorgen byggdes om, och tvärtom. Det är en stark signal om att
gränserna redan existerar konceptuellt — de är bara inte uttryckta som
filer.

## Var kopplingarna är starka

- **Signal-formuläret och Röst-AI:t är hopvävda, inte bara grannar.**
  `voice_draft()` renderar om exakt samma `SIGNAL_FORM_TEMPLATE` med samma
  ~25 context-variabler som `new_signal()`/`edit_signal()`. Ändrar man ett
  fält i formuläret måste tre routes hållas i synk. Själva AI-extraktionen
  (`extract_voice_draft(transcript, ctx)`) är däremot en ren funktion utan
  Flask-beroenden — den är lätt att lyfta ut, men *featuren* som helhet är
  det inte.
- **`build_signal_form_context()` är en delad autocomplete-motor** som
  används av `new_signal`, `edit_signal` och `voice_draft` — en genuin,
  rimlig koppling (inte ett problem i sig).
- **Insights-motorn kallar `url_for()` direkt inifrån
  aggregeringsfunktionerna** (t.ex. `build_milestone_insights`). Det
  betyder att den, trots att den bara läser data, kräver en aktiv Flask
  request-kontext — den är inte en renodlad "ren" modul idag.
- **`review()`-routen innehåller ~35 rader egen tagg-aggregering** innan
  den ens anropar `build_insights`/`build_role_insights`. Gränsen mellan
  "route" och "insights-logik" går alltså rakt genom funktionen, inte
  mellan filer.
- **`deleted_at`-filtret (`is_("deleted_at", "null")`) upprepas verbatim
  på ~15 ställen** över Insights, Hypoteser, Review, Flöde och
  autocomplete-hjälparna. Det är inte en modul-koppling utan
  copy-paste-koppling — ändras soft-delete-semantiken måste alla 15
  ställen hittas och uppdateras manuellt.

## Konkreta problem detta orsakar

- Att hitta "allt som rör papperskorgen" eller "allt som rör
  röstdiktering" kräver grep över hela filen — det märktes konkret under
  vyfilter-arbetet: flera greps krävdes för att lokalisera exakta
  radnummer innan varje edit.
- 790-radersblocket kring signal-formuläret blandar en stor Jinja-mall
  med tre routes' affärslogik i samma visuella yta — svårast att
  överblicka av alla delar.
- Ingen automatiserad testsvit (medvetet, enligt CLAUDE.md) betyder att
  korrekthet idag verifieras genom manuell läsning/grep av hela filen
  snarare än att öppna en avgränsad modul — kostnaden av storleken bärs
  helt av läsbarhet, inte av testkörningar.
- Risken vid ändring är låg för *isolerade* features (Idéer, Hypoteser)
  men högre för allt som rör signal-formuläret, eftersom tre routes måste
  hållas synkade manuellt.

## Bedömning

Filen har vuxit till en storlek och ett antal tydligt urskiljbara domäner
(5–6 stycken) där en lätt uppdelning skulle minska navigeringskostnaden
och göra kopplingarna (formulär↔röst-AI, insights↔route) synliga istället
för implicita. Samtidigt är CLAUDE.md för det här projektet explicit om
att enfils-arkitekturen är ett **medvetet** val ("Single file... No build
step, no client-side framework"), motiverat av att det är ett litet,
ensam-användar-verktyg utan CI/tester. Det talar mot en stor
uppsplittring.

**Rekommendation om refaktorering blir aktuell:** den minsta uppdelning
som faktiskt speglar var kopplingarna redan är svaga — inte ett generellt
lager-mönster — är att lyfta ut just de två bitar som är utpräglat
fristående:

1. **`insights.py`** — `Insight`-klassen + alla `build_*insights*`-
   funktioner och trösklar. Enda friktionen: `url_for()`-anropen måste
   antingen tas bort (returnera relativa path-strängar istället) eller så
   accepterar man att modulen fortfarande behöver Flask-appkontext.
2. **`voice_ai.py`** — `VOICE_DRAFT_*`-konstanterna +
   `extract_voice_draft`/`build_voice_draft_system_prompt`. Redan idag
   helt fri från Flask-beroenden — den enklaste och säkraste flytten av
   alla.

Routes (Flöde, Signaler, Hypoteser, Review, Idéer) och presentationsskalet
(`STYLE`/`NAV`/`page()`) bör **inte** delas upp nu — de delar
`page()`/`STYLE`/`SIGNAL_FORM_TEMPLATE` på sätt som gör en split till mer
bokföring (imports) än verklig riskminskning, och de är inte skenande i
storlek var för sig (130–390 rader).

**Slutsats:** vänta med även den minsta uppdelningen tills nästa feature
landar. Inget av problemen ovan har orsakat ett faktiskt fel hittills —
bara extra grep-tid. Två nya moduler innebär två filer att hålla reda på
i ett projekt utan tester som skulle fånga en trasig import, och vinsten
(isolering av insights/röst-AI) realiseras först när någon av dem växer
igen eller får en egen bugg som kräver upprepad felsökning. Det vore
billigt och lågrisk att göra nu — men "vänta tills det gör ont igen"
väger tyngre givet hur uttryckligen enfils-valet är dokumenterat som
avsiktligt.
