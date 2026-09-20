"""Replace applyWorkbench with a version that adopts filters and results that a page appends after the rail was built."""
P = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/app.js'
text = open(P, encoding='utf-8').read()
start = text.index('function applyWorkbench(){')
end = text.index('const workbenchObserver=new MutationObserver')
NEW = r"""function applyWorkbench(){
  if(!main)return;
  const segments=(window.ACTIVE_SEGMENTS&&window.ACTIVE_SEGMENTS.items)||[],active=window.ACTIVE_SEGMENTS&&window.ACTIVE_SEGMENTS.active;
  let bench=main.querySelector(':scope > .workbench');
  const looseForm=main.querySelector(':scope > form.filters');
  if(!bench){
    const listing=['laws','documents','federal','judges','people','counties','sources'].includes(route.view)||Boolean(extensionArea(route.view));
    if(!looseForm&&(segments.length<2||!listing||route.id))return;
    bench=el('div','workbench');const rail=el('aside','rail'),body=el('div','workbench-body');rail.setAttribute('aria-label','Collections and filters');
    if(segments.length>1){
      const group=el('nav','rail-group rail-collections');group.setAttribute('aria-label','Collections');group.append(el('h2','rail-title','Collection'));
      for(const seg of segments){const a=el('a',seg.view===active?'rail-item active':'rail-item');a.href=`#${seg.view}`;if(seg.view===active)a.setAttribute('aria-current','page');a.append(el('strong','',seg.label));if(seg.hint)a.append(el('span','',seg.hint));group.append(a);}
      rail.append(group);
    }
    bench.append(rail,body);
    const anchor=looseForm||[...main.children].find(node=>!node.matches('.page-heading,.home-hero,.notice,.view-switch,.scope-switch,.page-summary,.back-link'))||null;
    if(anchor)main.insertBefore(bench,anchor);else main.append(bench);
  }
  const rail=bench.querySelector(':scope > .rail'),body=bench.querySelector(':scope > .workbench-body');
  // Pages render in stages: whatever they append after the rail exists is adopted here (filters into the rail, the rest beside it).
  let node=bench.nextSibling;
  while(node){
    const next=node.nextSibling;
    if(node.nodeType===1&&node.matches('form.filters')){
      let group=rail.querySelector(':scope > .rail-filter-group');
      if(!group){group=el('div','rail-group rail-filter-group');group.append(el('h2','rail-title','Filters'));const toggle=el('details','rail-filters');toggle.open=window.matchMedia('(min-width: 1001px)').matches;toggle.append(el('summary','','Show filters'));group.append(toggle);rail.append(group);}
      const toggle=group.querySelector('details');for(const old of toggle.querySelectorAll(':scope > form.filters'))old.remove();toggle.append(node);
    }else body.append(node);
    node=next;
  }
}
"""
text = text[:start] + NEW + text[end:]
text = text.replace("const workbenchObserver=new MutationObserver(()=>{workbenchObserver.disconnect();try{applyWorkbench();}finally{workbenchObserver.observe(main,{childList:true});}});",
                    "const workbenchObserver=new MutationObserver(()=>{workbenchObserver.disconnect();try{applyWorkbench();}catch(error){console.error(error);}finally{workbenchObserver.observe(main,{childList:true});}});")
open(P, 'w', encoding='utf-8', newline='').write(text)
print('workbench replaced')
