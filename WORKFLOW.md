# Flag Marble Race: daily production and upload

Channel: **Flag Marble Race** (@FlagMarbleRaces) · Channel ID: `UCqfqnXk1Ipcd9lopex3m9Jg`
Video language: English. **The Studio interface is in Turkish** (dates like `10 Kas 2026`, times like `15:00`). Time zone: Europe/Istanbul.

## Every day: 3 Shorts (vertical, about 45–50 s)

| Video | Publish time (Istanbul) | Why |
|---|---|---|
| race1_world | 15:00 | US morning, Europe afternoon |
| race2_<region> | 20:00 | US midday, Europe evening |
| race3_world | 23:30 | US afternoon |

The task runs every evening at 21:13 (Istanbul). It makes **the next day's** videos and schedules them for the next day.

## 1. Setup (every session)
```bash
git clone --depth 1 https://github.com/spR1nt23/flag-race-videos /home/claude/flag-race-videos
bash /home/claude/flag-race-videos/tools/setup.sh
```

## 2. Render
```bash
cd /home/claude/flag-race-videos
python3 tools/make_day.py <DATE>      # e.g. 2026-11-11, about 1-2 minutes
```
- Writes `videos/<DATE>/race*.mp4` (silent) and `content/<DATE>/metadata.json` (title, description, time, `studio_track`).
- Seeds come from the date, so re-running a date gives the same videos (safe to resume).
- Extract 2-3 frames from each video and look at them (`ffmpeg -ss 20 -i x.mp4 -frames:v 1 f.png`). Each video should be about 40-55 s.
- `git add videos content && git commit -m "<DATE>" && git push origin HEAD:main`

## 3. Upload in Studio (built-in browser), one video at a time
1. Open `https://studio.youtube.com/channel/UCqfqnXk1Ipcd9lopex3m9Jg/videos/upload?d=ud`. If you get a 403 ("Oops"), the browser is on another account: click "Switch account" (Hesap değiştir) and pick **Flag Marble Race**. The browser is shared with other channels (Secret Spawn, Mühürlü Tarih, Español, İman Işığı…), so always check.
2. Provide the file with JS (wait ~3 s after the page loads):
```js
const url='https://raw.githubusercontent.com/spR1nt23/flag-race-videos/main/videos/<DATE>/<FILE>.mp4';
const b=await (await fetch(url,{cache:'no-store'})).blob();
const inp=document.querySelector('ytcp-uploads-file-picker input[type=file]')||document.querySelector('input[type=file]');
const dt=new DataTransfer(); dt.items.add(new File([b],'<FILE>.mp4',{type:'video/mp4'}));
inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true}));
await new Promise(r=>setTimeout(r,5000));
window.__mtFocus=(which)=>{const tb=[...document.querySelectorAll('ytcp-social-suggestions-textbox #textbox')].filter(e=>e.offsetParent); const el=which==='title'?tb[0]:tb[1]; el.focus(); const r=document.createRange(); r.selectNodeContents(el); const s=getSelection(); s.removeAllRanges(); s.addRange(r); return tb.length;};
window.__mtFocus('title')
```
3. If `__mtFocus` throws ("reading 'focus'"), the upload dialog was not ready yet: wait 3 s and call `window.__mtFocus('title')` again before typing. Otherwise the title stays as the file name (e.g. `race2 asia`); the step-4 check catches that, then re-focus the title and type again.
   `computer type` the title → JS `window.__mtFocus('desc')` → `computer type` the description (one line, ends with `#shorts `).
4. Check the boxes and schedule (this checks the title first; TIME `'15:00'`, DATE `'11 Kas 2026'` format: day, Turkish month abbreviation (Oca Şub Mar Nis May Haz Tem Ağu Eyl Eki Kas Ara), year):
```js
const W=ms=>new Promise(r=>setTimeout(r,ms)); const norm=s=>s.replace(/\s+/g,' ').trim(); const TIME='15:00', DATE='11 Kas 2026', TITLE='<TITLE>';
await W(2000);
const tb=[...document.querySelectorAll('ytcp-social-suggestions-textbox #textbox')].filter(e=>e.offsetParent);
if(tb[0].innerText!==TITLE) throw new Error('title mismatch: '+tb[0].innerText);
document.querySelector('tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]').click(); await W(500);
for(let i=0;i<3;i++){document.querySelector('#next-button').click(); await W(1500);}
await W(800); document.querySelector('#second-container-expand-button').click(); await W(1000);
const date=norm(document.querySelector('#datepicker-trigger').innerText);
// if date !== DATE: click #datepicker-trigger and pick the right .calendar-day, then run the rest again
document.querySelector('#time-of-day-container input').click(); await W(800);
const it=[...document.querySelectorAll('tp-yt-paper-item')].filter(e=>e.offsetParent!==null).find(e=>norm(e.innerText)===TIME); it.scrollIntoView(); it.click(); await W(800);
const time=document.querySelector('#time-of-day-container input').value;
let m=null; if(date===DATE&&norm(time)===TIME){document.querySelector('#done-button').click(); for(let i=0;i<12&&!m;i++){await W(1000); m=norm(document.body.innerText).match(/Video planlandı.{0,80}|herkese açık olacak|herkese açık olarak ayarlanacak/i);}}
({date,time,result:m&&m[0]})
```
   - `result` not null = scheduled. A "Video işleniyor … herkese açık olacak" dialog is also success.
   - Close the dialog (`Kapat` button) and go back to step 1 for the next video.
   - If the time list is 12-hour (`3:00 PM`), the UI language changed: use that format.

## 4. Add music in the Studio editor (after all 3 are scheduled)
1. Content → Shorts: `https://studio.youtube.com/channel/UCqfqnXk1Ipcd9lopex3m9Jg/videos/short`. Get the video IDs:
```js
await new Promise(r=>setTimeout(r,4000));
[...document.querySelectorAll('ytcp-video-row')].map(r=>({t:r.querySelector('#video-title')?.innerText, href:r.querySelector('a[href*="/video/"]')?.getAttribute('href'), vis:r.querySelector('.tablecell-visibility')?.innerText.trim()}))
```
2. For each video: `resize_window` 1400x900, open `https://studio.youtube.com/video/<ID>/editor`. If you see the "Başla" intro, click it (`find` "Başla").
3. Click the **Ses** row's `+` (screenshot first). The audio library opens. Add the track named in `metadata.json` → `studio_track`:
```js
const W=ms=>new Promise(r=>setTimeout(r,ms)); await W(3000);
window.__addTrack=async(name)=>{const row=[...document.querySelectorAll('[role=row]')].find(r=>r.offsetParent&&r.innerText.trim().startsWith(name));
if(!row) return 'not found';
const lic=[...row.querySelectorAll('[aria-label],[title]')].map(i=>i.getAttribute('aria-label')||i.getAttribute('title')).join(',');
if(!/YouTube Ses Kitaplığı Lisansı|YouTube Audio Library License/.test(lic)) return 'needs attribution';
row.scrollIntoView(); row.dispatchEvent(new MouseEvent('mouseover',{bubbles:true})); await W(500);
const btn=[...row.querySelectorAll('[aria-label]')].find(b=>/^(Ekle|Add)$/.test(b.getAttribute('aria-label')));
btn.click(); await W(2500); return 'added';};
await window.__addTrack('<TRACK>')
```
   - `not found`: type the name into the search box ("Kitaplığı arayın…") and try again, or pick another track with the "YouTube Ses Kitaplığı Lisansı" license.
   - **Never use "Creative Commons Atıf 4.0" tracks** (they need a credit in the description).
4. Click **Kaydet** (top right) → tick "Bu değişikliklerin kalıcı olduğunu kabul ediyorum" → **Değişiklikleri onayla**. The page then shows "Video düzenleme işlemi devam ediyor…" = success (processing takes a while, that's fine).
5. At the end, `resize_window` preset desktop.

## 5. Check and report
Content → Shorts: all 3 new videos must show **Planlandı**. If one is "Taslak" (draft), open it and redo step 3.4.
Send the user a short summary: date, 3 titles, times, music used, and anything that failed.

## Notes
- When the browser pane is hidden, `offsetParent` is null for every element: select the upload text boxes with `ytcp-uploads-dialog ytcp-social-suggestions-textbox #textbox` (no visibility filter) and the time items without an `offsetParent` filter.
- In the editor, the audio button can be found with `find` "Ses ekle" (a stable ref) instead of coordinates.
- Titles must not repeat the previous day's titles; if `make_day.py` picks the same title as yesterday, change it in metadata.json before uploading.

## Warnings
- Do not press Escape during upload (it closes the upload window). Do not leave the page before the upload finishes.
- The browser is shared with other channels' tasks (Español 14:55, Mühürlü Tarih 22:37). Before every upload, check the channel is Flag Marble Race.
- Unverified channels have a low daily upload limit. If you see a limit warning, stop and report it.
- Content is "not made for kids".
