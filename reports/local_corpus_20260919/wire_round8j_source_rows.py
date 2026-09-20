"""Round 8j: source references as dense rows (was large serif cards). CSS only. Idempotent."""
P = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/styles.css'
css = open(P, encoding='utf-8').read()
if '/* source rows */' not in css:
    css += """
/* source rows */
.source-card-grid{display:flex!important;flex-direction:column;gap:0!important;border:1px solid var(--line);border-radius:10px;background:var(--surface,#fff);overflow:hidden}
.source-card-grid .source-card{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"context actions" "title actions" "host actions" "flags actions" "note actions";column-gap:18px;row-gap:1px;padding:10px 14px!important;border:0!important;border-bottom:1px solid var(--line)!important;border-radius:0!important;box-shadow:none!important;background:none!important;margin:0!important}
.source-card-grid .source-card:last-child{border-bottom:0!important}.source-card-grid .source-card:hover{background:rgba(15,76,68,.035)!important}
.source-card-grid .source-card-context{grid-area:context;font-size:10.5px;letter-spacing:.3px;color:var(--muted);margin:0;text-transform:none}
.source-card-grid .source-card-title{grid-area:title;font-family:inherit!important;font-size:14px!important;font-weight:600;line-height:1.35!important;color:var(--ink);text-decoration:none;margin:0;min-height:0;display:block}
.source-card-grid .source-card-title:hover{color:var(--teal-dark);text-decoration:underline}
.source-card-grid .source-host{grid-area:host;margin:0!important;font-size:12px;color:var(--muted)}
.source-card-grid .source-card-flags{grid-area:flags;display:flex;flex-wrap:wrap;gap:4px;margin:4px 0 0}
.source-card-grid .source-status{display:none}
.source-card-grid .source-note-preview{grid-area:note;margin:4px 0 0;font-size:12px;line-height:1.5;color:var(--muted);display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.source-card-grid .source-card-actions{grid-area:actions;display:flex;flex-direction:column;align-items:flex-end;justify-content:center;gap:2px;margin:0;padding:0;border:0}
.source-card-grid .source-card-actions a{font-size:12px;min-height:0;padding:2px 0;white-space:nowrap}
@media(max-width:700px){.source-card-grid .source-card{grid-template-columns:minmax(0,1fr);grid-template-areas:"context" "title" "host" "flags" "note" "actions"}.source-card-grid .source-card-actions{flex-direction:row;justify-content:flex-start;gap:14px;margin-top:4px}}
"""
    open(P, 'w', encoding='utf-8', newline='').write(css)
print('source rows applied')
