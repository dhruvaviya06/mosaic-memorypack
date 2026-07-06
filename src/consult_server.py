"""
consult_server.py — the Mosaic dashboard (admin/demo console, not a chat app).

Per the access architecture: the primary path is MCP (an org's agent calls consult_pack
behind the scenes). This localhost page is the engineer's console to verify an installed
pack and to demo it — "pgAdmin, not the bank's mobile app". No history, sessions, or auth.

The answer is precedent-first and delivered as SHARED EXPERIENCE:
  step 1 — closest precedent + warning-sign chips + an invitation to map it.
  step 2 — on "Map onto my situation", the recommended playbook (the precedent's steps
           rewritten to reference the user's situation). The two-step is LOCAL UI STATE,
           independent of the MCP flow, so a misbehaving host agent can't break the demo.

On the map step the resolved case is DISTILLED and remembered into the Node's own case
memory (learn-and-forget). The single disclaimer lives in the install note banner, never
per answer.

It calls the SAME shared logic the MCP server uses (query.consult_with_citations).

Run:  .venv/bin/python src/consult_server.py     # then open http://localhost:8000
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import tarfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cognee
from config import PACK_DATASET, PACK_FILE, PACK_DISPLAY, INSTALL_NOTE
from query import consult_with_citations, bare_llm
from learn import capture_case

PORT = 8000
_lock = threading.Lock()


def pack_manifest() -> dict:
    if not PACK_FILE.exists():
        return {}
    with tarfile.open(PACK_FILE, "r:gz") as tar:
        return json.load(tar.extractfile("pack.json"))


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mosaic — Console</title>
<style>
 :root{--bg:#0b0f1a;--panel:#141a2b;--panel2:#1b2338;--line:#26304d;--ink:#e8ecf6;
   --muted:#93a0bd;--accent:#5b8cff;--green:#37d39b;--amber:#f5b74e;--chip:#20294180}
 *{box-sizing:border-box}
 body{margin:0;background:radial-gradient(1200px 600px at 70% -10%,#17203a 0,var(--bg) 55%);
   color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
 .wrap{max-width:940px;margin:0 auto;padding:30px 22px 60px}
 .brand{display:flex;align-items:center;gap:11px;margin-bottom:4px}
 .logo{width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,var(--accent),#8a5bff);
   display:grid;place-items:center;font-weight:800;color:#fff;font-size:14px}
 h1{font-size:18px;margin:0}
 .sub{color:var(--muted);font-size:12.5px;margin:2px 0 16px}
 /* install note — the one and only disclaimer, shown at install/console load */
 .note{background:#1b1706;border:1px solid #4a3d12;color:#f0dfa8;border-radius:12px;
   padding:11px 14px;font-size:12.8px;line-height:1.5;margin-bottom:16px}
 .note b{color:var(--amber)}
 /* pack identity strip */
 .strip{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:linear-gradient(180deg,var(--panel),var(--panel2));
   border:1px solid var(--line);border-radius:13px;padding:12px 15px;margin-bottom:18px}
 .strip .nm{font-weight:700}
 .badge{font-size:11px;font-weight:600;padding:4px 9px;border-radius:999px;background:#0f2a20;color:var(--green);border:1px solid #1e5c46}
 .pill{font-size:11.5px;color:var(--muted);background:var(--chip);border:1px solid var(--line);border-radius:8px;padding:4px 9px}
 .pill b{color:#fff}
 .grow{flex:1}
 .ghost{background:transparent;border:1px solid #5c2a2a;color:#ff9a9a;border-radius:9px;padding:7px 12px;font-size:12.5px;cursor:pointer}
 textarea{width:100%;min-height:96px;background:var(--panel);border:1px solid var(--line);color:var(--ink);
   border-radius:12px;padding:12px 14px;font-size:14.5px;resize:vertical;line-height:1.5}
 .row{display:flex;align-items:center;gap:14px;margin:11px 0 2px;flex-wrap:wrap}
 button.go{background:linear-gradient(135deg,var(--accent),#8a5bff);color:#fff;border:0;padding:11px 20px;
   border-radius:11px;font-size:14.5px;font-weight:600;cursor:pointer}
 button:disabled{opacity:.55;cursor:default}
 label{color:var(--muted);font-size:13px;display:flex;align-items:center;gap:7px;cursor:pointer}
 .ex{color:var(--accent);cursor:pointer;font-size:12.5px}
 .ex.mh{color:var(--amber)}
 .cols{display:grid;gap:14px;margin-top:18px}
 .cols.two{grid-template-columns:1fr 1fr}
 @media(max-width:720px){.cols.two{grid-template-columns:1fr}}
 .card{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--line);border-radius:14px;padding:15px 17px}
 .card.pack{border-color:#2f6bff44}
 .card h3{margin:0 0 9px;font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
 .card.pack h3{color:var(--green)}
 .ans{white-space:pre-wrap;font-size:14.5px}
 .muted{color:var(--muted)}
 .prec{font-size:15px;margin:2px 0 2px}
 .why{color:#c7d0e6;font-size:13.5px;margin:0 0 12px}
 .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:12px 0 7px}
 .chips{display:flex;flex-wrap:wrap;gap:7px}
 .rchip{display:inline-flex;align-items:center;font-size:12px;background:#241a08;border:1px solid #5a4718;
   color:#f0d79a;border-radius:999px;padding:5px 11px}
 .invite{margin:14px 0 10px;font-size:14px;color:#dbe4f7}
 ol.play{margin:6px 0 2px;padding-left:20px}
 ol.play li{margin:0 0 8px;font-size:14px;line-height:1.5}
 .learned{margin-top:12px;font-size:12.5px;color:var(--green)}
 .learned.fail{color:var(--amber)}
 .cite{margin-top:13px;padding-top:12px;border-top:1px dashed var(--line)}
 .cite .clbl{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:7px}
 .case{font-size:13px;margin:0 0 6px}
 .cchip{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;text-decoration:none;
   background:#0f1b34;border:1px solid #274a86;color:#bcd0ff;border-radius:999px;padding:5px 10px;margin:0 6px 6px 0}
 .cchip:hover{background:#16264a}
 .cchip::before{content:"§";color:#6f8fd6}
 .spin{display:inline-block;width:15px;height:15px;border:2px solid #ffffff55;border-top-color:#fff;border-radius:50%;
   animation:sp .7s linear infinite;vertical-align:-2px;margin-right:7px}
 @keyframes sp{to{transform:rotate(360deg)}}
</style></head><body><div class="wrap">
 <div class="brand"><div class="logo">M</div><div><h1>Mosaic — Console</h1></div></div>
 <p class="sub">Self-hosted Node console. In production an org's agent consults this pack via MCP;
   this page verifies and demos the installed pack.</p>

 <div class="note" id="note">loading…</div>

 <div class="strip" id="strip"><span class="muted">loading pack…</span></div>

 <textarea id="q" placeholder="Describe a situation — a counterparty, a bank, a transaction pattern…"></textarea>
 <div class="row">
   <button class="go" id="go" onclick="ask()">Find precedent</button>
   <label><input type="checkbox" id="cmp"> compare with a plain LLM (contrast view)</label>
 </div>
 <div class="row" style="margin-top:2px">
   <span class="muted" style="font-size:12.5px">try:</span>
   <span class="ex" onclick="fill(this)">concentrated leveraged total-return swaps across brokers, persistent margin breaches</span>
   <span class="ex" onclick="fill(this)">short-term wholesale funding financing long-term infrastructure loans</span>
   <span class="ex mh" onclick="fill(this)">which risk factors recur across multiple failures?</span>
 </div>
 <div id="out" class="cols"></div>
</div>
<script>
 const esc=s=>{const d=document.createElement('div');d.textContent=s||'';return d.innerHTML;};
 let situation='';
 function fill(el){document.getElementById('q').value=el.textContent;}

 async function loadNote(){
   try{const n=await (await fetch('/note')).json();
     document.getElementById('note').innerHTML='<b>Before you consult:</b> '+esc(n.note);
   }catch(e){document.getElementById('note').style.display='none';}
 }

 async function loadPack(){
   try{const m=await (await fetch('/pack')).json(); const s=document.getElementById('strip');
     if(!m.label){s.innerHTML='<span class="muted">no pack installed</span>';return;}
     const c=m.counts||{}; const h=(m.content_hash||'').slice(0,12);
     s.innerHTML=`<span class="nm">${esc(m.name)} <span class="muted">${esc(m.version)}</span></span>
       <span class="badge">● ${esc(m.verification_tier||'verified')}</span>
       <span class="pill">graph <b>${c.nodes_total||'?'}</b>·<b>${c.edges_total||'?'}</b></span>
       <span class="pill">embeddings <b>${m.embeddings_included?'yes':'none'}</b></span>
       <span class="pill">sha256 <b>${esc(h)}…</b></span>
       <span class="grow"></span>
       <button class="ghost" onclick="uninstall()">Uninstall pack</button>`;
   }catch(e){document.getElementById('strip').innerHTML='<span class="muted">pack info unavailable</span>';}
 }

 function citeHtml(cites){
   if(!cites||!cites.length) return '';
   let h='<div class="cite"><div class="clbl">Evidence · primary sources</div>';
   for(const c of cites){
     h+=`<div class="case"><b>${esc(c.institution)}</b> ${c.year?'('+c.year+')':''}</div><div>`;
     for(const s of c.sources){
       h+= s.url ? `<a class="cchip" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.label)}</a>`
                 : `<span class="cchip">${esc(s.label)}</span>`;
     }
     h+='</div>';
   }
   return h+'</div>';
 }

 function packCard(d){
   const p=d.precedent;
   if(!p){
     return `<div class="card pack"><h3>${TESSERA} · consult_pack</h3>
       <div class="ans muted">${esc(d.answer)}</div>${citeHtml(d.citations)}</div>`;
   }
   let chips='';
   for(const r of (d.risk_factors||[])) chips+=`<span class="rchip">${esc(r)}</span>`;
   return `<div class="card pack" id="packcard"><h3>${TESSERA} · consult_pack</h3>
     <div class="prec"><b>Closest precedent:</b> ${esc(p.institution)} ${p.year?'('+p.year+')':''}</div>
     <div class="why">${esc(p.why||'')}</div>
     <div class="lbl">Shared warning signs</div>
     <div class="chips">${chips||'<span class="muted">—</span>'}</div>
     <div class="invite">${esc(d.invitation)}</div>
     <button class="go" id="mapbtn" onclick="mapIt()">Map onto my situation →</button>
     <div id="mapslot"></div>
     ${citeHtml(d.citations)}</div>`;
 }
 const TESSERA=__PACK_DISPLAY__;

 async function ask(){
   const q=document.getElementById('q').value.trim(); if(!q)return;
   situation=q;
   const cmp=document.getElementById('cmp').checked;
   const btn=document.getElementById('go'), out=document.getElementById('out');
   out.className='cols'; out.innerHTML='<div class="card"><span class="spin"></span>Recalling the closest precedent…</div>';
   btn.disabled=true;
   try{
     const d=await (await fetch('/consult',{method:'POST',headers:{'Content-Type':'application/json'},
       body:JSON.stringify({situation:q,compare:cmp})})).json();
     if(d.error){out.innerHTML='<div class="card">Error: '+esc(d.error)+'</div>';}
     else{
       const pack=packCard(d);
       if(d.bare!==undefined){
         out.className='cols two';
         out.innerHTML=`<div class="card"><h3>Plain LLM · no pack</h3><div class="ans muted">${esc(d.bare)}</div>
           <div class="cite"><div class="clbl muted">no citations — generic knowledge</div></div></div>`+pack;
       }else{out.className='cols'; out.innerHTML=pack;}
     }
   }catch(e){out.innerHTML='<div class="card">Request failed: '+esc(''+e)+'</div>';}
   btn.disabled=false;
 }

 async function mapIt(){
   const btn=document.getElementById('mapbtn'), slot=document.getElementById('mapslot');
   if(!btn||!slot)return;
   btn.disabled=true; slot.innerHTML='<div class="lbl"><span class="spin"></span>Mapping the precedent onto your situation…</div>';
   try{
     const d=await (await fetch('/map',{method:'POST',headers:{'Content-Type':'application/json'},
       body:JSON.stringify({situation})})).json();
     if(d.error){slot.innerHTML='<div class="muted">Error: '+esc(d.error)+'</div>'; btn.disabled=false; return;}
     let steps='';
     for(const s of (d.playbook||[])) steps+=`<li>${esc(s)}</li>`;
     const learned = d.captured
       ? '<div class="learned">✓ distilled case added to this Node\'s memory</div>'
       : '<div class="learned fail">· case not stored this run</div>';
     slot.innerHTML=`<div class="lbl">How analysts in matching cases investigated it, applied to your situation</div>
       <ol class="play">${steps}</ol>${learned}`;
     btn.style.display='none';
   }catch(e){slot.innerHTML='<div class="muted">Request failed: '+esc(''+e)+'</div>'; btn.disabled=false;}
 }

 async function uninstall(){
   if(!confirm('Uninstall the pack? This runs forget(dataset) and removes it from this Node.'))return;
   try{const d=await (await fetch('/uninstall',{method:'POST'})).json();
     document.getElementById('out').innerHTML='<div class="card">Pack uninstalled — '+esc(JSON.stringify(d))+
       '<br><span class="muted">One forget() call. Re-run <code>mesh install</code> to bring it back.</span></div>';
     loadPack();
   }catch(e){alert('uninstall failed: '+e);}
 }
 document.getElementById('q').addEventListener('keydown',e=>{if(e.metaKey&&e.key==='Enter')ask();});
 loadNote(); loadPack();
</script></body></html>"""

# Inject the display name into the page JS as a JSON string literal.
PAGE = PAGE.replace("__PACK_DISPLAY__", json.dumps(PACK_DISPLAY))


def _run(coro):
    return asyncio.run(coro)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif self.path == "/pack":
            self._send(200, json.dumps(pack_manifest()))
        elif self.path == "/note":
            self._send(200, json.dumps({"note": INSTALL_NOTE}))
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path == "/consult":
            body = self._read_json()
            situation = (body.get("situation") or "").strip()
            if not situation:
                self._send(400, json.dumps({"error": "empty situation"}))
                return
            try:
                with _lock:
                    result = _run(consult_with_citations(situation, PACK_DATASET))
                    if body.get("compare"):
                        result["bare"] = _run(bare_llm(situation))
                self._send(200, json.dumps(result))
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)[:400]}))
        elif self.path == "/map":
            body = self._read_json()
            situation = (body.get("situation") or "").strip()
            if not situation:
                self._send(400, json.dumps({"error": "empty situation"}))
                return
            try:
                with _lock:
                    # step 2: rewrite the precedent's playbook onto the FULL situation …
                    result = _run(consult_with_citations(situation, PACK_DATASET,
                                                         map_to_situation=True))
                    # … then learn-and-forget: distil + remember into the Node's memory.
                    cap = _run(capture_case(situation, result))
                    result["captured"] = cap.get("stored", False)
                self._send(200, json.dumps(result))
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)[:400]}))
        elif self.path == "/uninstall":
            try:
                with _lock:
                    result = _run(cognee.forget(dataset=PACK_DATASET))
                self._send(200, json.dumps(result))
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)[:400]}))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    m = pack_manifest()
    print(f"Mosaic console ({m.get('label','no pack')}) -> http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
