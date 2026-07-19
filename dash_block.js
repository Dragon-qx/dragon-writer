function escHtml(s){return s;}
const MD={parseInline:function(s){return s;}};
function draw(){}
const nodes=[{name:'a',func:'f',desire:'d',fear:'x',state:'s',arc:'r',secrets:'y',tier:'主要'}];
const edges=[{s:0,t:0,label:'test'}];
const info={innerHTML:""};
function setSelect(i){
  selected=i; draw();
  const info=info;
  if(i<0){ info.innerHTML='<div class="empty">提示</div>'; return; }
  const n=nodes[i];
  const fields=[["故事功能",n.func],["欲望",n.desire],["恐惧",n.fear],["当前状态",n.state],["弧线",n.arc],["秘密",n.secrets]].filter(([_,v])=>v);
  const rels=edges.filter(e=>e.s===i||e.t===i).map(e=>{ const o=nodes[e.s===i?e.t:e.s]; return `<div style="margin-bottom:6px"><span class="rname">${escHtml(o.name)}</span>${e.label?' - '+MD.parseInline(e.label):''}</div>`; });
  info.innerHTML=`<div class="name">${escHtml(n.name)}</div><div class="tier">${escHtml(n.tier)}</div>` +
    (fields.length?`<dl>${fields.map(([k,v])=>`<dt>${escHtml(k)}</dt><dd>${MD.parseInline(v)}</dd>`).join("")}</dl>`:'') +
    (rels.length?`<div class="rels" style="font-size:13px">${rels.join("")}</div>`:'');
}
