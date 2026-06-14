#!/usr/bin/env python3
"""冷面物理 · Markdown 转 HTML 转换器 v2"""

import re, os

def parse_md(text):
    lines = text.split('\n')
    blocks = []
    i = 0
    in_list = False
    sections = {'🎬 开场','🔥 段子时间','📖 法则小课堂','💡 互动挑战','🎯 本期金句'}
    
    # Skip frontmatter lines that start with > **
    frontmatter_done = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            if in_list: blocks.append(('list_end','')); in_list = False
            i += 1; continue
        
        # Skip H1 title lines (already in banner)
        if line.startswith('# '):
            i += 1; continue
        
        # Skip frontmatter info lines (> **...)
        if stripped.startswith('> **') and not frontmatter_done:
            # Extract key info
            m = re.match(r'> \*\*知识点\*\*[：:]\s*(.*)', stripped)
            if m: blocks.append(('meta_topics', m.group(1)))
            i += 1; continue
        if stripped.startswith('> **') or stripped.startswith('> *'):
            # Other frontmatter - skip
            i += 1; continue
        
        frontmatter_done = True
        
        # Headers
        if line.startswith('## '):
            if in_list: blocks.append(('list_end','')); in_list = False
            blocks.append(('h2', line[3:].strip()))
            i += 1; continue
        if line.startswith('### '):
            if in_list: blocks.append(('list_end','')); in_list = False
            blocks.append(('h3', line[4:].strip()))
            i += 1; continue
        
        # Dividers
        if stripped in ('---', '—— · —— · ——', '——', '———'):
            if in_list: blocks.append(('list_end','')); in_list = False
            blocks.append(('hr',''))
            i += 1; continue
        
        # Blockquotes
        if line.startswith('> '):
            if in_list: blocks.append(('list_end','')); in_list = False
            blocks.append(('bq', line[2:].strip()))
            i += 1; continue
        
        # List items
        if stripped.startswith('- '):
            if not in_list: blocks.append(('ul_start','')); in_list = True
            blocks.append(('li', stripped[2:].strip()))
            i += 1; continue
        if re.match(r'^\d+[.、]\s', stripped):
            if not in_list: blocks.append(('ul_start','')); in_list = True
            blocks.append(('li', re.sub(r'^\d+[.、]\s*','',stripped).strip()))
            i += 1; continue
        
        if in_list: blocks.append(('list_end','')); in_list = False
        
        # Tables (skip raw table formatting)
        if stripped.startswith('|'):
            i += 1; continue
        
        # Section labels
        found = False
        for s in sections:
            if stripped == s or stripped == s.replace(' ',''):
                blocks.append(('stag', s))
                found = True; break
        if found: i += 1; continue
        
        # Regular paragraph
        blocks.append(('p', line))
        i += 1
    
    if in_list: blocks.append(('list_end',''))
    return blocks


def inline(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


def make_html(blocks, title, topics, ep_num):
    parts = []
    in_ul = False
    
    for bt, c in blocks:
        if bt == 'meta_topics':
            topics = topics or c
            continue
        if bt == 'h2':
            if in_ul: parts.append('</ul>'); in_ul = False
            parts.append(f'<h2 class="h2">{inline(c)}</h2>')
        elif bt == 'h3':
            if in_ul: parts.append('</ul>'); in_ul = False
            parts.append(f'<h3 class="h3">{inline(c)}</h3>')
        elif bt == 'p':
            if in_ul: parts.append('</ul>'); in_ul = False
            if c.rstrip(): parts.append(f'<p class="p">{inline(c.rstrip())}</p>')
        elif bt == 'bq':
            if in_ul: parts.append('</ul>'); in_ul = False
            parts.append(f'<blockquote class="bq">{inline(c)}</blockquote>')
        elif bt == 'li':
            if not in_ul: parts.append('<ul class="ul">'); in_ul = True
            parts.append(f'<li>{inline(c)}</li>')
        elif bt == 'list_end':
            if in_ul: parts.append('</ul>'); in_ul = False
        elif bt == 'hr':
            if in_ul: parts.append('</ul>'); in_ul = False
            parts.append('<div class="divider">✦ ✦ ✦</div>')
        elif bt == 'stag':
            if in_ul: parts.append('</ul>'); in_ul = False
            label = c[2:].strip()
            parts.append(f'<div class="stag">{c[0]} <span>{label}</span></div>')
    
    if in_ul: parts.append('</ul>')
    
    body = '\n'.join(parts)
    t_html = f'<div class="topics">📖 {inline(topics)}</div>' if topics else ''
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - 冷面物理</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  font-family:'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif;
  background:#f8f6f2;color:#2c2c2c;line-height:1.9;
}}
.wx{{max-width:680px;margin:0 auto;padding:30px 24px 60px}}
.banner{{
  background:linear-gradient(135deg,#1a2744,#2a3a5c);color:#fff;
  border-radius:16px;padding:32px 24px;text-align:center;margin:0 0 28px;
  position:relative;overflow:hidden;
}}
.banner::before{{
  content:'';position:absolute;top:-60%;left:-30%;
  width:200px;height:200px;
  background:radial-gradient(circle,rgba(100,180,255,0.08),transparent 70%);
  border-radius:50%;
}}
.banner h1{{font-size:26px;margin:0 0 4px;color:#fff;letter-spacing:4px;position:relative}}
.ep-tag{{font-size:12px;color:rgba(255,255,255,0.5);letter-spacing:2px;margin-bottom:6px;position:relative}}
.banner p{{font-size:14px;margin:6px 0 0;color:rgba(255,255,255,0.7);position:relative}}
.topics{{
  display:inline-block;background:rgba(255,255,255,0.08);
  padding:3px 14px;border-radius:20px;font-size:12px;
  color:rgba(255,255,255,0.8);margin-top:10px;position:relative;
}}
.p{{font-size:16px;line-height:2;margin:10px 0;text-indent:2em;color:#333}}
.h2{{font-size:20px;font-weight:700;color:#1a2744;margin:36px 0 16px;padding-bottom:8px;border-bottom:2px solid #d4a853}}
.h3{{font-size:17px;font-weight:700;color:#2a3a5c;margin:24px 0 10px}}
.stag{{font-size:14px;font-weight:700;color:#d4a853;margin:32px 0 12px;padding:8px 0;letter-spacing:2px}}
.stag span{{color:#1a2744}}
.bq{{
  background:linear-gradient(135deg,#f0f4ff,#e8edf8);
  border-left:4px solid #d4a853;padding:14px 18px;
  margin:14px 0;border-radius:0 8px 8px 0;
  font-size:15px;line-height:1.8;color:#1a2744;
}}
.ul{{padding-left:28px;margin:12px 0;list-style:none}}
.ul li{{font-size:15px;line-height:1.9;color:#333;margin:4px 0;padding-left:8px;position:relative}}
.ul li::before{{content:'·';position:absolute;left:-14px;color:#d4a853;font-weight:700}}
.divider{{text-align:center;color:#ccc;margin:30px 0;font-size:14px;letter-spacing:8px}}
strong{{color:#1a2744}}
code{{background:#edf0f5;padding:2px 8px;border-radius:4px;font-size:14px;color:#2a3a5c}}
.footer{{
  text-align:center;margin:40px 0 20px;padding:24px;
  background:linear-gradient(135deg,#f0f4ff,#f8f6f2);
  border-radius:12px;font-size:13px;color:#666;
  border:1px solid #e0e4eb;
}}
.footer .brand{{color:#d4a853;font-weight:700}}
</style>
</head>
<body>
<div class="wx">
<div class="banner">
  <div class="ep-tag">{ep_num}</div>
  <h1>{title}</h1>
  <p>❄️ 冷面物理 · 笑着笑着就学会了</p>
  {t_html}
</div>
{body}
<div class="footer">
  <p style="margin:4px 0;">❄️ <span class="brand">冷面物理</span> · 笑着笑着就学会了</p>
  <p style="margin:4px 0;text-indent:0;">📖 想读故事版？→ 看看「物理解码者：异世法则」</p>
  <p style="margin:4px 0;text-indent:0;">💬 有想听的物理知识点？→ 评论区留言</p>
</div>
</div>
</body>
</html>'''


def convert(md_path, out_dir):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    title = '冷面物理'
    ep_num = ''
    topics = ''
    
    for line in text.split('\n'):
        if line.startswith('# ') and 'EP' in line:
            m = re.search(r'EP\s*(\d+)\s*[:：]?\s*(.*)', line)
            if m:
                ep_num = f'EP {m.group(1)}'
                t = m.group(2).strip()
                t = re.sub(r'[>》].*', '', t).strip()
                if t: title = t
        if '知识点' in line and '：' in line:
            if not topics:
                topics = line.split('：', 1)[-1].strip()
    
    blocks = parse_md(text)
    html = make_html(blocks, title, topics, ep_num)
    
    basename = os.path.basename(md_path).replace('.md', '.html')
    with open(os.path.join(out_dir, basename), 'w', encoding='utf-8') as f:
        f.write(html)
    return basename


def main():
    sd = os.path.dirname(os.path.abspath(__file__))
    pd = os.path.dirname(sd)
    out = os.path.join(pd, '专场稿')
    root = os.path.dirname(pd)
    
    files = []
    f = os.path.join(root, '脱口秀物理课-样稿-开场秀.md')
    if os.path.exists(f): files.append(f)
    
    if os.path.exists(out):
        for fn in sorted(os.listdir(out)):
            if fn.endswith('.md'):
                files.append(os.path.join(out, fn))
    
    print('🔄 转换中...')
    for f in files:
        r = convert(f, out)
        print(f'  ✅ {r}')


if __name__ == '__main__':
    main()
