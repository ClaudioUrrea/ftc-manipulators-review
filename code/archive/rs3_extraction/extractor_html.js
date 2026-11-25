// Extractor de texto completo para el panel del navegador (pegar en javascript_tool tras cargar el articulo).
// Convierte MathJax 3 (incluido el modo perezoso) y MathML a texto lineal; __full() arma window.__T; __sec(desde, hasta, tope) devuelve una seccion.
// Uso tipico: __full(); (__T.match(/\n## [^\n]{0,70}/g)||[]).slice(0,40)  -> lista de secciones; luego __sec('## 3\\. ', '## 4\\. ', 5000).
window.__mml=(n)=>{ if(n.nodeType===3) return n.textContent.trim(); const t=(n.localName||'').toLowerCase(); const ch=[...n.childNodes].filter(x=>x.nodeType===1||x.textContent.trim()); const r=ch.map(__mml);
 if(t==='msub') return r[0]+'_{'+r[1]+'}'; if(t==='msup') return r[0]+'^{'+r[1]+'}'; if(t==='msubsup') return r[0]+'_{'+r[1]+'}^{'+r[2]+'}';
 if(t==='mfrac') return '('+r[0]+')/('+r[1]+')'; if(t==='msqrt') return 'sqrt('+r.join('')+')'; if(t==='mover'||t==='munder') return r[0]+'['+r[1]+']';
 if(t==='mfenced') return (n.getAttribute('open')||'(')+r.join(n.getAttribute('separators')===''?' ':', ')+(n.getAttribute('close')||')');
 if(t==='annotation'||t==='annotation-xml') return ''; if(t==='mspace') return ' '; if(t==='mtr') return r.join(' & ')+' ;; '; return r.join(' '); };
window.__mjx=(c)=>{ try{ const lz=c.querySelector('mjx-lazy'); let src=null; if(lz){const it=MathJax.startup.document.lazyList.get(lz.getAttribute('data-mjx-lazy')); src=it&&it.math;} if(!src){const m=c.querySelector('mjx-assistive-mml math'); if(m) return __mml(m);} if(!src) return '[eq]'; if(src.trim().startsWith('<')) return __mml(new DOMParser().parseFromString(src.replace(/&nbsp;/g,' '),'text/xml').documentElement); return src; }catch(e){return '[eq]';} };
window.__full=(sel)=>{ const root=(sel&&document.querySelector(sel))||document.body; const live=[...root.querySelectorAll('mjx-container')]; const txt=live.map(__mjx);
 const clone=root.cloneNode(true); [...clone.querySelectorAll('mjx-container')].forEach((e,i)=>e.replaceWith(' $'+txt[i].replace(/\s+/g,' ')+'$ '));
 clone.querySelectorAll('math').forEach(m=>m.replaceWith(' $'+__mml(m).replace(/\s+/g,' ')+'$ ')); clone.querySelectorAll('script,style,nav,svg,button,header,footer').forEach(e=>e.remove());
 clone.querySelectorAll('h1,h2,h3,h4,h5').forEach(h=>h.prepend('\n\n## ')); clone.querySelectorAll('p,div,li,tr,figcaption').forEach(e=>e.append('\n'));
 window.__T=clone.textContent.replace(/[ \t]+/g,' ').replace(/\n\s*\n+/g,'\n'); return __T.length; };
window.__sec=(fromRe,toRe,cap=6000)=>{const a=__T.search(new RegExp(fromRe,'i')); if(a<0) return 'NOT FOUND'; const rest=__T.slice(a+5); const b=toRe? rest.search(new RegExp(toRe,'i')):-1; return __T.slice(a, b<0? a+cap : Math.min(a+5+b, a+cap));};
'extractor listo';
