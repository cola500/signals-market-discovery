---
title: Genomlysning av användbarhet på desktop
description: Visuell granskning av hur appen (byggd mobile-first) beter sig i en bred skrivbordsbläddrare, med konkreta fynd rangordnade efter påverkan.
category: ux
status: current
last_updated: 2026-08-18
sections:
  - Metod
  - Fynd
  - Vad som redan fungerar
  - Rekommendation
---

# Genomlysning av användbarhet på desktop

Appen är byggd mobile-first (se `CLAUDE.md`) och har aldrig testats eller
anpassats för bred skärm. Den här genomlysningen renderade fyra centrala
sidor (Flöde, Ny signal, Hypoteser, Översikt) och jämförde mobil (390px)
mot desktop (1440px) för att se konkret vad "mobile only" faktiskt
innebär i praktiken, inte bara i teorin.

Ingen kod ändrades för att göra genomlysningen.

## Metod

Sidorna renderades lokalt med verklig template-kod och dummy-data, och
skärmdumpades med Playwright i två viewportstorlekar — dels vid sidans
topp, dels efter scroll, för att undvika falska positiva/negativa (t.ex.
verifierade att bottennavigationen verkligen stannar fastnaglad vid
scroll och inte bara råkar synas rätt i en enda ruta).

Bekräftat: hela `STYLE`-blocket i `app.py` innehåller **noll
`@media`-queries**. Det finns en enda fast layout för alla
skärmstorlekar — det förklarar samtliga fynd nedan.

## Fynd

Rangordnade efter faktisk påverkan på användbarheten, inte efter hur
lätta de är att åtgärda.

1. **Formuläret "Ny signal" kräver ~2 fulla skärmhöjder av scroll på
   desktop.** Uppmätt: 1727px innehåll i en 900px-hög viewport, trots att
   ~800px bredd står helt oanvänd bredvid formuläret. Alla fält ligger i
   en enda kolumn (Datum, Person, Organisation, Signal-typ, Roll/
   möjlighet, Kanal, …) trots att flera par (Datum+Person,
   Signal-typ+Kanal) lätt skulle kunna stå två-och-två per rad på bred
   skärm. Det här är den mest konkreta kostnaden: appens eget löfte att
   fånga en signal "på under två minuter" tar onödigt många scroll på
   desktop.

2. **Översikt (dashboard-sidan) slösar mest potential av alla sidor.**
   Sex-sju korta listsektioner (Insikter, Roll-insikter, tagg-frekvens,
   kanal-frekvens, hypoteser med/utan ny evidens, obehandlade nästa steg)
   staplas rakt under varandra i en smal kolumn, trots att sidan
   konceptuellt redan är en dashboard — precis den sortens innehåll som
   naturligt passar ett rutnät av kort på bred skärm.

3. **Bottennavigationen sträcker ut sig över hela viewport-bredden.**
   `nav a{flex:1}` på fem objekt betyder att varje ikon+etikett blir en
   ~288px bred yta på en 1440px-skärm, med mycket dött utrymme runt en
   liten ikon. Fungerar tekniskt korrekt (verifierat fastnaglad vid
   scroll), men läser visuellt som en uttänjd mobilnav snarare än ett
   genuint desktop-mönster (top-nav eller sidopanel).

4. **Hela innehållet är en fast 640px-kolumn centrerad i viewporten**,
   oavsett skärmbredd (`body{max-width:640px;margin:0 auto}`). På en
   bred monitor blir resultatet mycket tomt utrymme på båda sidor —
   appen "ser ut som en mobilskärm inklistrad mitt på en stor bakgrund."

## Vad som redan fungerar

Värt att veta innan man planerar åtgärder — inget av detta behöver
röras:

- Hover-states finns redan på länkar och knappar.
- Autocomplete-dropdownarna (person, organisation, signal-typ, kanal,
  taggar, hypotes) fungerar felfritt med mus, inklusive redigera-/
  ta bort-ikonerna på varje förslag.
- Tangentbordsfokus-ringar syns korrekt på formulärfält.
- Inget överlappar eller går sönder på bred skärm — det är rent
  utrymmesslöseri och ett omoget navigationsmönster, inte trasig
  funktionalitet.

## Rekommendation

Prioritetsordning om åtgärder blir aktuella, efter mest nytta per insats:

1. **Formuläret** — en `@media`-brytpunkt (t.ex. över 768px) som lägger
   relaterade fältpar två-och-två per rad i varje `fieldset`. Störst
   konkret nytta (halverar scroll-höjden) för minst jobb.
2. **Översikt som rutnät** — samma brytpunkt, lägg sektionerna i ett
   2–3-kolumners rutnät istället för en lång stapel.
3. **Nav-bredd** — en `max-width` på `nav` som matchar `body`s 640px,
   centrerad, istället för att sträcka sig över hela viewporten.

En fullständig desktop-anpassning av allt (bredare `body`, omdesignad
navigation, etc.) är ett större jobb och inte genomfört eller planerat
här — det här dokumentet är avsiktligt bara genomlysningen, inte en
implementationsplan.
