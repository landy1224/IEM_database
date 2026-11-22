"""在 editable/index.html 加入產品照片新增／更換／移除（artifact assets）。用法：python3 -I patch_photos.py <editable/index.html>"""
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:80])
    s = s.replace(old, new)

# CSS
rep(".pic{display:block;",
    ".photo{display:flex;gap:10px;align-items:flex-start;flex-wrap:wrap}\n"
    ".photo .prev{width:96px;height:96px;object-fit:contain;background:#fff;border:1px solid var(--line);border-radius:6px;flex:none}\n"
    ".photo .none{width:96px;height:96px;border:1px dashed var(--line);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11.5px;color:var(--muted);flex:none;text-align:center}\n"
    ".photo .ctl{display:flex;flex-direction:column;gap:6px;min-width:0;flex:1}\n"
    ".pic{display:block;")

# 圖片來源：上傳的照片存 asset id（imgAsset），內建照片為 img 相對路徑
rep('const esc=s=>',
    'const imgSrc=it=>it.imgAsset?"/_blob/"+it.imgAsset:(it.img||"");\nconst esc=s=>')
rep('${it.img?`<img class="th" loading="lazy" src="${esc(it.img)}"', '${imgSrc(it)?`<img class="th" loading="lazy" src="${esc(imgSrc(it))}"')
rep('${it.img?`<img class="pic" src="${esc(it.img)}"', '${imgSrc(it)?`<img class="pic" src="${esc(imgSrc(it))}"')

# 表單：照片欄位
rep('''   <div class="g2"><label>類別<select name="category">''',
    '''   <fieldset><legend>產品照片</legend><div class="photo"><span id="phBox"></span><div class="ctl">
     ${S.assets?`<div class="row"><label class="btn" style="display:inline-block">選擇照片<input type="file" id="phFile" accept="image/jpeg,image/png,image/webp,image/gif,image/heic,image/heif" hidden></label><button class="btn" type="button" id="phDel">移除照片</button><button class="btn" type="button" id="phUndo" hidden>復原</button></div>
     <div class="small" id="phMsg">可選擇檔案，或在此表單中直接貼上（Ctrl+V）截圖。照片會縮到長邊 1000 px 後上傳。</div>`:'<div class="small">你沒有上傳照片的權限（需為擁有者或編輯者）。</div>'}
   </div></div></fieldset>
   <div class="g2"><label>類別<select name="category">''')

# 表單：照片狀態與事件（接在取消按鈕設定之前）
rep('''  $("#cancel").onclick=()=>{S.mode="view";S.asVersion=false;renderSheet()};''',
    '''  const ph={mode:"keep",blob:null,url:null};
  const showPh=()=>{const src=ph.mode==="new"?ph.url:ph.mode==="remove"?"":imgSrc(it);
    $("#phBox").innerHTML=src?`<img class="prev" src="${esc(src)}" alt="照片預覽" onerror="this.outerHTML='<div class=none>照片無法顯示</div>'">`:'<div class="none">尚無照片</div>';
    if($("#phDel"))$("#phDel").hidden=!src;if($("#phUndo"))$("#phUndo").hidden=ph.mode==="keep"};
  const takePh=async file=>{const m=$("#phMsg");if(!file)return;m.textContent="處理照片中…";
    try{const b=await shrinkImg(file);if(ph.url)URL.revokeObjectURL(ph.url);ph.mode="new";ph.blob=b;ph.url=URL.createObjectURL(b);m.textContent=`已選擇新照片（${Math.round(b.size/1024)} KB），按「儲存」後上傳。`;showPh()}
    catch(e){m.textContent=e.message==="size"?"檔案超過 20 MB，請換一張。":"無法讀取這個格式，請改用 JPG 或 PNG。"}};
  showPh();
  if(S.assets){
    $("#phFile").onchange=e=>takePh(e.target.files[0]);
    $("#phDel").onclick=()=>{ph.mode="remove";ph.blob=null;$("#phFile").value="";$("#phMsg").textContent="儲存後會移除照片。";showPh()};
    $("#phUndo").onclick=()=>{ph.mode="keep";ph.blob=null;$("#phFile").value="";$("#phMsg").textContent="已復原為原本的照片。";showPh()};
    $("#ed").addEventListener("paste",e=>{const f=[...(e.clipboardData?.files||[])].find(x=>x.type.startsWith("image/"));if(f){e.preventDefault();takePh(f)}});
  }
  $("#cancel").onclick=()=>{if(ph.url)URL.revokeObjectURL(ph.url);S.mode="view";S.asVersion=false;renderSheet()};''')

# 儲存：處理照片
rep('''    if(it.img)doc.img=it.img;
''', '''    const oldAsset=it.imgAsset||null;
    if(ph.mode==="keep"){if(it.img)doc.img=it.img;if(it.imgAsset)doc.imgAsset=it.imgAsset}
    else if(ph.mode==="new"){
      const sb=e.target.querySelector("button[type=submit]");sb.disabled=true;$("#phMsg").textContent="上傳照片中…";
      try{doc.imgAsset=(await uploadImg(ph.blob)).id}
      catch(err){sb.disabled=false;$("#phMsg").textContent=assetErr(err);toast("照片上傳失敗，資料尚未儲存");return}
    }
''')
rep('''      S.mode="view";S.asVersion=false;renderSheet();
    }catch(err){fail(err)}};''',
    '''      /* 更換或移除照片後，舊照片若已沒有任何品項使用就刪除（建立新版本時舊版仍保留照片，不刪） */
      if(!isNew&&!asVer&&oldAsset&&doc.imgAsset!==oldAsset)dropAsset(oldAsset,it.id);
      if(ph.url)URL.revokeObjectURL(ph.url);
      S.mode="view";S.asVersion=false;renderSheet();
    }catch(err){fail(err)}};''')
rep('''    try{await S.db.doc("items/"+it.id).delete();S.sel=null;''',
    '''    try{await S.db.doc("items/"+it.id).delete();if(it.imgAsset)dropAsset(it.imgAsset,it.id);S.sel=null;''')

# 共用函式：縮圖、上傳、刪除、錯誤訊息
rep('''function fail(e){''', '''/* 照片：縮到長邊 1000 px、轉 JPEG；瀏覽器無法解碼時，可接受的格式直接上傳原檔 */
const OK_TYPES=["image/jpeg","image/png","image/webp","image/gif"];
async function shrinkImg(file){
  if(file.size>20*1024*1024)throw new Error("size");
  try{
    const bmp=await createImageBitmap(file);const k=Math.min(1,1000/Math.max(bmp.width,bmp.height));
    const c=document.createElement("canvas");c.width=Math.max(1,Math.round(bmp.width*k));c.height=Math.max(1,Math.round(bmp.height*k));
    const g=c.getContext("2d");g.fillStyle="#fff";g.fillRect(0,0,c.width,c.height);g.drawImage(bmp,0,0,c.width,c.height);bmp.close?.();
    const b=await new Promise(r=>c.toBlob(r,"image/jpeg",0.85));if(b&&b.size)return b;
  }catch(e){}
  if(OK_TYPES.includes(file.type))return file;
  throw new Error("fmt");
}
async function uploadImg(blob){
  const t=OK_TYPES.includes(blob.type)?blob.type:"image/jpeg";
  try{return await S.assets.upload(blob,{type:t})}
  catch(e){if(e?.code==="store_unavailable"){await new Promise(r=>setTimeout(r,1200));return await S.assets.upload(blob,{type:t})}throw e}
}
function assetErr(e){const c=e?.code;return c==="too_large"?"照片太大，請換一張較小的。":c==="unsupported_type"?"不支援這個格式，請改用 JPG 或 PNG。":c==="quota_or_state"?"照片儲存空間已滿。":c==="rate_limited"?"操作太頻繁，請稍候再試。":c==="not_granted"||c==="capability_disabled"?"目前無法上傳照片。":"照片上傳失敗，請稍後再試。"}
function dropAsset(id,exceptItem){if(!S.assets||S.items.some(x=>x.id!==exceptItem&&x.imgAsset===id))return;S.assets.delete(id).catch(()=>{})}
function fail(e){''')

# boot：取得 assets（只有擁有者／編輯者會拿到，其餘為 null）
rep('''  S.canWrite=w!==false;''', '''  try{S.assets=await window.claude.use("assets")}catch(e){S.assets=null}
  S.canWrite=w!==false;''')
rep('''  S.db=null;S.canWrite=false;''', '''  S.db=null;S.canWrite=false;S.assets=null;''')

open(p, "w", encoding="utf-8").write(s)
print("patched", len(s))
