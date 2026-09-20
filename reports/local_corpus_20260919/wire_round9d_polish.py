"""Round 9d: the Judges / Historical biographies switch duplicated the collection rail; hide it when the rail lists collections. CSS only. Idempotent."""
P = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/styles.css'
css = open(P, encoding='utf-8').read()
if '.people-section-nav{display:none}' not in css:
    css += "\n#main:has(> .workbench .rail-collections) .people-section-nav{display:none}\n"
    open(P, 'w', encoding='utf-8', newline='').write(css)
print('polish applied')
