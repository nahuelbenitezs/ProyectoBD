export const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fmtDate = (str, opts={day:'2-digit',month:'short',year:'numeric'}) => str ? new Date(`${str.slice(0,10)}T12:00:00`).toLocaleDateString('es-UY',opts) : '—';
export const fmtDay = (str) => fmtDate(str,{day:'2-digit',month:'short'});
export const timeHM = (s) => (s || '').slice(0,5);
export const collator = new Intl.Collator('es',{sensitivity:'base'});
export const nextId = (arr,key) => Math.max(0,...arr.map(x=>Number(x[key])||0)) + 1;
export const initials = (value) => String(value||'?').split(/\s+/).filter(Boolean).map(x=>x[0]).slice(0,2).join('').toUpperCase();
export const unique = (a) => [...new Set(a)];
export const normalize = (v) => String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
export const icons = {
  dashboard:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  fixture:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
  team:'<circle cx="12" cy="7" r="4"/><path d="M5 21v-2a7 7 0 0 1 14 0v2M20 8h2M1 8h2"/>',
  players:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  trophy:'<path d="M8 21h8M12 17v4M7 4h10v6a5 5 0 0 1-10 0V4zM7 6H4v2a4 4 0 0 0 4 4M17 6h3v2a4 4 0 0 1-4 4"/>',
  venue:'<path d="M3 21V9l9-6 9 6v12H3zM9 21v-8h6v8M3 10h18"/>',
  shield:'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
  chart:'<path d="M3 3v18h18M7 16l4-5 3 3 6-7"/>',
  chevron:'<path d="m9 18 6-6-6-6"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  pencil:'<path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L9 17l-4 1 1-4z"/>',
  trash:'<path d="M3 6h18M8 6V4h8v2M5 6l1 15h12l1-15M10 10v7M14 10v7"/>',
  close:'<path d="M18 6 6 18M6 6l12 12"/>',
  download:'<path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4"/>',
  check:'<path d="m5 12 4 4L19 6"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  alert:'<path d="m12 3 10 18H2L12 3zM12 9v4M12 17h.01"/>',
  menu:'<path d="M3 6h18M3 12h18M3 18h18"/>',
  arrow:'<path d="M5 12h14m-7-7 7 7-7 7"/>',
  refresh:'<path d="M20 11a8 8 0 1 0-2 6M20 4v7h-7"/>',
  filter:'<path d="M4 7h16M7 12h10M10 17h4"/>',
  football:'<circle cx="12" cy="12" r="9"/><path d="m12 7 4 3-1.5 4.5h-5L8 10zm-4 3-4-1m5.5 5.5L7 18m7.5-3.5L17 18m-1-8 4-1M12 7V3"/>',
  lock:'<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/>',
  moon:'<path d="M20.9 13A9 9 0 0 1 11 3.1 9 9 0 1 0 20.9 13z"/>'
};
export const ico = (name,size=19) => `<svg aria-hidden="true" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${icons[name]||icons.football}</svg>`;
export const badge = (status) => `<span class="status status-${normalize(status).replace(/\s/g,'-')}"><span class="status-dot"></span>${esc(status)}</span>`;
export const button = (label,act,id='',variant='outline',extra='') => `<button class="btn btn-${variant}" data-action="${esc(act)}" ${id!==''?`data-id="${esc(id)}"`:''} ${extra}>${label}</button>`;
export const emptyState = (heading,description='Probá cambiando los filtros.') => `<div class="empty"><div class="empty-graphic">${ico('search',26)}</div><h3>${esc(heading)}</h3><p>${esc(description)}</p></div>`;
