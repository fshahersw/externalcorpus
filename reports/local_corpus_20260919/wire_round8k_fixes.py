"""Round 8k: source rows target the real list container; page headings stay above the workbench on in-app navigation. Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'
css = open(D + 'styles.css', encoding='utf-8').read()
if '.source-grid .source-card{' not in css:
    start = css.index('/* source rows */')
    block = css[start:]
    css = css[:start] + block.replace('.source-card-grid', '.source-grid')
    open(D + 'styles.css', 'w', encoding='utf-8', newline='').write(css)

app = open(D + 'app.js', encoding='utf-8').read()
old = "    }else body.append(node);\n    node=next;"
new = ("    }else if(node.nodeType===1&&node.matches('.page-heading,.home-hero,.notice,.page-summary,.back-link')){\n"
       "      main.insertBefore(node,bench); // a heading drawn after the rail still belongs above it\n"
       "    }else body.append(node);\n    node=next;")
if new not in app:
    assert app.count(old) == 1
    app = app.replace(old, new)
    open(D + 'app.js', 'w', encoding='utf-8', newline='').write(app)
print('fixes applied')
