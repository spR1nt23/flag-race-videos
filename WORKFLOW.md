# Flag Marble Race: daily production and upload

Channel: **Flag Marble Race** · Channel ID: `CHANNEL_ID` (fill in after the channel is created)
Google account: **selinarica.2007** (same account as Secret Spawn and Mühürlü Tarih). Language: English. Time zone: Europe/Istanbul (Studio GMT+03:00).

## Every day: 3 Shorts (vertical, about 45–50 s)

| Video | Publish time (Istanbul) | Why |
|---|---|---|
| race1_world | 3:00 PM | US morning, Europe afternoon |
| race2_<region> | 8:00 PM | US midday, Europe evening |
| race3_world | 11:30 PM | US afternoon |

The task runs every evening at 21:13 (Istanbul). It makes **the next day's** videos and schedules them for the next day. Make sure to pick the right date in the date picker.

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
- Writes `videos/<DATE>/race*.mp4` and `content/<DATE>/metadata.json` (title, description, time, music used).
- Music: one track from `music/` per video (YouTube Audio Library tracks, attribution not required). If `music/` is empty the videos are silent: report that.
- Seeds come from the date, so re-running a date gives the same videos (safe to resume).
- Extract 2-3 frames from each video and look at them (`ffmpeg -ss 20 -i x.mp4 -frames:v 1 f.png`). Each video should be about 40-55 s.
- `git add videos content && git commit -m "<DATE>" && git push origin HEAD:main`

## 3. Upload in Studio (built-in browser), one video at a time
1. Open `https://studio.youtube.com/channel/CHANNEL_ID/videos/upload?d=ud`. If you see a 403, the browser is on another account: set the window to 1280, then Profile → Switch account → selinarica.2007 → Flag Marble Race. Studio should show "Your channel Flag Marble Race" on the left.
2. Provide the file with JS:
```js
const url='https://raw.githubusercontent.com/spR1nt23/flag-race-videos/main/videos/<DATE>/<FILE>.mp4';
const b=await (await fetch(url,{cache:'no-store'})).blob();
const inp=document.querySelector('ytcp-uploads-file-picker input[type=file]')||document.querySelector('input[type=file]');
const dt=new DataTransfer(); dt.items.add(new File([b],'<FILE>.mp4',{type:'video/mp4'}));
inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true}));
```
3. Title and description: focus the box with JS, then type with `computer type`:
```js
window.__mtFocus=(which)=>{const tb=[...document.querySelectorAll('ytcp-social-suggestions-textbox #textbox')].filter(e=>e.offsetParent); const el=which==='title'?tb[0]:tb[1]; el.focus(); const r=document.createRange(); r.selectNodeContents(el); const s=getSelection(); s.removeAllRanges(); s.addRange(r); return tb.length;};
window.__mtFocus('title')   // then type the title;  then __mtFocus('desc') and type the description
```
After typing, wait 2 s, read both boxes' `innerText` and check them (text can appear late; typing again enters it twice). Navigating clears `window` functions, so define them again for every video.
4. Audience + steps + time (TIME e.g. `'3:00 PM'`, DATE e.g. `'Nov 11, 2026'`):
```js
const W=ms=>new Promise(r=>setTimeout(r,ms)); const norm=s=>s.replace(/\s+/g,' ').trim(); const TIME='3:00 PM', DATE='Nov 11, 2026';
document.querySelector('tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]').click(); await W(500);
for(let i=0;i<3;i++){document.querySelector('#next-button').click(); await W(1500);}
await W(800); document.querySelector('#second-container-expand-button').click(); await W(1000);
let date=norm(document.querySelector('#datepicker-trigger').innerText);
// if the date is wrong: click #datepicker-trigger and pick the .calendar-day in the calendar
document.querySelector('#time-of-day-container input').click(); await W(800);
const it=[...document.querySelectorAll('tp-yt-paper-item')].filter(e=>e.offsetParent!==null).find(e=>norm(e.innerText)===TIME); it.scrollIntoView(); it.click(); await W(800);
const time=document.querySelector('#time-of-day-container input').value;
let m=null; if(date===DATE&&norm(time)===TIME){document.querySelector('#done-button').click(); for(let i=0;i<12&&!m;i++){await W(1000); m=document.body.innerText.replace(/\s+/g,' ').match(/Video scheduled.{0,80}|will be set to public on.{0,40}/);}}
({date,time,result:m&&m[0]})
```
   - If `result` is null, take a screenshot. If you are still on the Visibility step, click **Schedule** at the bottom right. A "Video processing … will be set to public on …" dialog also means success; close it with Close.
5. Repeat from step 1 for the next video. At the end, check under Content → Shorts that all 3 show **Scheduled**. If one stayed a "Draft", open it with "Edit draft" and repeat step 4.

## Warnings
- Do not press Escape (it closes the upload window). Do not leave the page before the upload finishes.
- The browser is shared with other channels' tasks (Español 14:55, Mühürlü Tarih 22:37): before every upload, check that the channel is Flag Marble Race.
- Unverified channels have a low daily upload limit. If you see a limit warning, stop and report it.
- Content is "not made for kids" (same as the other channels).
