"""JS-извлекатель кандидатов из живой страницы.

Запускается через page.evaluate(...). Обходит DOM, эмитит дескрипторы интерактивных
(и явно адресуемых) элементов: tag, attrs, text, role, accessible-name (приближённо),
относительный xpath, цепочку ролей предков, сигнатуру соседей, bbox, видимость.

Намеренно фильтрует на «вероятно интерактивные», чтобы не возвращать тысячи узлов.
Тонкая фильтрация волатильных атрибутов делается на стороне Python (attr_filter.py).
"""

EXTRACTOR_JS = r"""
() => {
  const INTERACTIVE = new Set(['A','BUTTON','INPUT','SELECT','TEXTAREA','LABEL','SUMMARY']);
  const ROLE_LANDMARKS = ['main','navigation','form','search','banner','contentinfo','dialog','region'];

  function roleOf(el){
    const r = el.getAttribute('role');
    if (r) return r;
    const t = el.tagName.toLowerCase();
    if (t==='a' && el.hasAttribute('href')) return 'link';
    if (t==='button') return 'button';
    if (t==='input'){ const ty=(el.getAttribute('type')||'text').toLowerCase();
      if (['button','submit','reset'].includes(ty)) return 'button';
      if (ty==='checkbox') return 'checkbox';
      if (ty==='radio') return 'radio';
      return 'textbox'; }
    if (t==='select') return 'combobox';
    if (t==='textarea') return 'textbox';
    return '';
  }
  function accName(el){
    const al = el.getAttribute('aria-label'); if (al) return al.trim();
    const lb = el.getAttribute('aria-labelledby');
    if (lb){ const n=document.getElementById(lb); if(n) return (n.textContent||'').trim(); }
    if (el.tagName==='INPUT'){
      const id=el.id; if(id){ const l=document.querySelector(`label[for="${id}"]`);
        if(l) return (l.textContent||'').trim(); }
      const ph=el.getAttribute('placeholder'); if(ph) return ph.trim();
    }
    return (el.textContent||'').trim().slice(0,120);
  }
  function ancestorRoles(el){
    const out=[]; let n=el.parentElement;
    while(n && out.length<8){
      const r=n.getAttribute('role')||'';
      const t=n.tagName.toLowerCase();
      if (ROLE_LANDMARKS.includes(r)) out.push(r);
      else if (['main','nav','form','header','footer','section','dialog'].includes(t)) out.push(t);
      n=n.parentElement;
    }
    return out.reverse();
  }
  function siblingSig(el){
    const p=el.parentElement; if(!p) return '';
    return Array.from(p.children).map(c => c.tagName.toLowerCase()+':'+(roleOf(c)||'')).join('|');
  }
  function relXPath(el){
    const parts=[]; let n=el;
    while(n && n.nodeType===1 && parts.length<6){
      let i=1, s=n.previousElementSibling;
      while(s){ if(s.tagName===n.tagName) i++; s=s.previousElementSibling; }
      parts.unshift(n.tagName.toLowerCase()+'['+i+']');
      n=n.parentElement;
    }
    return '/'+parts.join('/');
  }
  function isVisible(el){
    const r=el.getBoundingClientRect();
    const st=getComputedStyle(el);
    return r.width>0 && r.height>0 && st.visibility!=='hidden' && st.display!=='none';
  }

  const all = Array.from(document.querySelectorAll('*'));
  const out=[]; let hid=0;
  for(const el of all){
    const interactive = INTERACTIVE.has(el.tagName) || el.hasAttribute('role')
      || el.hasAttribute('data-testid') || el.hasAttribute('onclick')
      || getComputedStyle(el).cursor==='pointer';
    if(!interactive) continue;
    const attrs={};
    for(const a of el.attributes){ attrs[a.name]=a.value; }
    const r=el.getBoundingClientRect();
    out.push({
      handle_id: hid++,
      tag: el.tagName.toLowerCase(),
      attrs,
      text: (el.textContent||'').trim().slice(0,120),
      role: roleOf(el),
      accessible_name: accName(el),
      rel_xpath: relXPath(el),
      ancestor_roles: ancestorRoles(el),
      sibling_signature: siblingSig(el),
      bbox: [r.x/innerWidth, r.y/innerHeight, r.width/innerWidth, r.height/innerHeight],
      visible: isVisible(el),
      enabled: !el.disabled,
    });
  }
  return out;
}
"""
