"""由 repo 的單檔查詢版 index.html 產生可編輯版：
   out/index.html（boot 改用 artifact db）、out/seed.json（228 筆，img 改成相對路徑）、out/img/<id>.jpg
用法：python3 -I build_editable.py <repo>/index.html <out_dir>
"""
import base64, json, os, sys

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
lines = s.split("\n")
di = next(i for i, x in enumerate(lines) if x.startswith("const DATA="))
data = json.loads(lines[di][len("const DATA="):].rstrip().rstrip(";"))
assert lines[di + 1].startswith("S.items=DATA"), lines[di + 1][:80]

os.makedirs(os.path.join(out, "img"), exist_ok=True)
for it in data:
    img = it.get("img")
    if img and img.startswith("data:image/jpeg;base64,"):
        open(os.path.join(out, "img", it["id"] + ".jpg"), "wb").write(base64.b64decode(img.split(",", 1)[1]))
        it["img"] = "img/" + it["id"] + ".jpg"
json.dump(data, open(os.path.join(out, "seed.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

BOOT = r'''/* boot：可編輯版。資料存在 artifact 資料庫 collection「items」；
   無法連線資料庫時（例如 GitHub Pages）改讀 seed.json 快照，唯讀。 */
{
const SNAP="2026-11-12";
let seed=null;
const loadSeed=async()=>{if(!seed){const r=await fetch("seed.json");if(!r.ok)throw new Error("seed");seed=await r.json()}return seed};
async function readOnly(msg){
  S.db=null;S.canWrite=false;
  try{S.items=await loadSeed();S.loaded=true;$("#exportBtn").hidden=false;$("#addBtn").hidden=true;$("#mode").textContent=msg;render();renderSheet()}
  catch(e){S.loaded=true;S.items=[];render();const em=$("#empty");em.hidden=false;em.textContent="無法載入資料。"}
}
/* 首次匯入：資料庫是空的、且目前使用者可寫入時，出現「匯入快照」按鈕 */
S.importing=false;
function renderImport(){
  const box=$("#importBox");
  const show=S.db&&S.canWrite&&S.loaded&&(S.importing||(S.dbEmpty&&!S.items.length));
  box.hidden=!show;if(!show)return;
  if(S.importing)return;
  box.innerHTML=`<div>資料庫目前是空的。要匯入 ${SNAP} 快照的品項（含產品圖）嗎？匯入一次即可，之後的修改都直接存在資料庫。</div><div class="row" style="margin-top:6px"><button class="btn primary" id="impBtn">匯入快照資料</button><span class="small" id="impMsg"></span></div>`;
  $("#impBtn").onclick=runImport;
}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function runImport(){
  const btn=$("#impBtn"),msg=$("#impMsg");btn.disabled=true;S.importing=true;
  let list;try{list=await loadSeed()}catch(e){msg.textContent="讀不到快照檔，請稍後再試";btn.disabled=false;S.importing=false;return}
  const have=new Set(S.items.map(x=>x.id));let done=0,skip=0;
  for(const it of list){
    if(have.has(it.id)){skip++;continue}
    const {id,...doc}=it;let tries=0;
    for(;;){
      try{await S.db.doc("items/"+id).set(doc);break}
      catch(e){
        if((e?.code==="resource_exhausted"||e?.code==="unavailable")&&tries<6){tries++;msg.textContent=`伺服器忙碌，稍候重試…（${done}/${list.length}）`;await sleep(1500*tries);continue}
        S.importing=false;btn.disabled=false;
        msg.textContent=e?.code==="invalid_argument"?"你沒有寫入權限，無法匯入":e?.code==="quota_exceeded"?"資料庫容量已滿":`匯入中斷（已完成 ${done} 筆），再按一次會從中斷處繼續`;return}
    }
    done++;msg.textContent=`匯入中… ${done+skip}/${list.length}`;
  }
  S.importing=false;S.dbEmpty=false;toast(`匯入完成：新增 ${done} 筆`);renderImport();
}
(async()=>{
  const em=$("#empty");
  const slow=setTimeout(()=>{if(!S.loaded)em.textContent="資料庫連線較慢，仍在嘗試…"},10000);
  let db=null;try{db=window.claude?.use?await window.claude.use("db"):null}catch(e){}
  if(!db){clearTimeout(slow);return readOnly(`無法連線資料庫，顯示 ${SNAP} 快照（唯讀）`)}
  S.db=db;
  let user=null;try{user=await window.claude.use("user")}catch(e){}
  let w=null;try{w=user?await user.can("data.write"):null}catch(e){}
  S.canWrite=w!==false;   /* null＝平台未告知：先保留編輯，寫入被拒時 fail() 會改成唯讀 */
  db.collection("items").onSnapshot(snap=>{
    if(!snap.metadata.fromCache)clearTimeout(slow);
    S.items=snap.docs.map(d=>({...d.data(),id:d.id}));
    S.dbEmpty=snap.empty&&!snap.metadata.fromCache;
    S.loaded=true;$("#exportBtn").hidden=false;$("#addBtn").hidden=!S.canWrite;
    $("#mode").textContent=S.canWrite?"資料存在雲端資料庫，修改後所有使用者即時可見。":"你目前只有檢視權限。";
    render();if(S.mode==="view")renderSheet();renderImport();
  },err=>{clearTimeout(slow);readOnly(`資料庫連線中斷，改顯示 ${SNAP} 快照（唯讀）`)});
})();
/* 檢視權限被拒時（fail→refreshWrite）一併收起匯入按鈕 */
const _rw=refreshWrite;refreshWrite=function(){_rw();renderImport()};
}'''

head = lines[:di]
# 標題、說明文字改為可編輯版
html = "\n".join(head)
html = html.replace("<title>代謝營養主資料庫（查詢版）</title>", "<title>代謝營養主資料庫</title>", 1)
old_disc = "資料更新：2026-11-12（查詢版，不提供編輯）。</div>"
assert old_disc in html
html = html.replace(old_disc, '<span id="mode">連線資料庫中…</span></div>\n  <div class="note plain" id="importBox" hidden></div>', 1)
# refreshWrite 需可被覆寫（function 宣告本來就可重新指定）
assert "function refreshWrite()" in html
html = html.replace("/* boot：唯讀版，資料內嵌 */", "")
page = ('<!DOCTYPE html>\n<html lang="zh-Hant"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        + html + "\n" + BOOT + "\n</script>\n")
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
print(len(data), "items;", sum(1 for x in data if x.get("img")), "images;", len(page), "bytes page")
