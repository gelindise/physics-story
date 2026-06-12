#!/usr/bin/env python3
"""
Generate beautifully styled WeChat Official Account HTML from chapter HTML files.
Uses table-based layouts and inline CSS for WeChat editor compatibility.
"""
import re, os, html as html_mod

def strip_tags(text):
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def process_bold(text):
    text = re.sub(r'<em>(.*?)</em>', r'\1', text)
    return text

def escape_wx(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text

def get_chapter_meta(html):
    ch_num = ''
    ch_title = ''
    m = re.search(r'<h2[^>]*>(第[^<]+章)</h2>', html)
    if m: ch_num = strip_tags(m.group(1))
    m = re.search(r'style="[^"]*text-align:center[^"]*"[^>]*>\s*([^<]+?)\s*</h1>', html)
    if m: ch_title = strip_tags(m.group(1)).strip()
    if not ch_title:
        m = re.search(r'<h1>(.*?)</h1>', html)
        if m: ch_title = strip_tags(m.group(1))
    return ch_num, ch_title

def get_topics(html):
    m = re.search(r'📖 物理知识点[：:](.*?)</p>', html)
    return strip_tags(m.group(1)) if m else ''

def get_reader_content(html):
    m = re.search(r'class="reader-content">(.*?)<script', html, re.DOTALL)
    if not m:
        m = re.search(r'class="reader-content">(.*)', html, re.DOTALL)
    return m.group(1) if m else ''

def remove_special_blocks_depth(content):
    """Remove all special div blocks using depth counting."""
    classes = ['knowledge-card', 'canvas-container', 'experiment-box', 'challenge-box', 'note-box']
    for cls in classes:
        pat = rf'<div class="{re.escape(cls)}[^>]*">'
        while True:
            m = re.search(pat, content, re.DOTALL)
            if not m: break
            start = m.start()
            depth = 1
            i = m.end()
            while i < len(content) and depth > 0:
                next_open = content.find('<div', i)
                next_close = content.find('</div>', i)
                if next_close == -1: break
                if next_open != -1 and next_open < next_close:
                    depth += 1
                    i = next_open + 4
                else:
                    depth -= 1
                    i = next_close + 6
            content = content[:start] + content[i:]
    return content

def get_story_sections(html):
    content = get_reader_content(html)
    if not content: return []
    
    content = remove_special_blocks_depth(content)
    content = re.sub(r'<script>.*?</script>', '', content, flags=re.DOTALL)
    
    parts = re.split(r'<h3>(.*?)</h3>', content)
    sections = []
    current_title = ''
    current_paras = []
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part: continue
        
        if i % 2 == 1:
            title = strip_tags(part)
            if any(k in title for k in ['互动实验', '动手探索', '脑力挑战', '法则笔记']):
                if current_paras:
                    sections.append((current_title, current_paras))
                    current_paras = []
                current_title = ''
                continue
            if current_paras:
                sections.append((current_title, current_paras))
            current_title = title
            current_paras = []
        else:
            for p in re.findall(r'<p[^>]*>(.*?)</p>', part, re.DOTALL):
                text = process_bold(p)
                text = strip_tags(text)
                if text and len(text) > 3:
                    if any(s in text for s in ['继续阅读', '返回书架']): continue
                    if re.match(r'.*第.*章.*完', text): continue
                    if re.match(r'^[✦✧\s\*\—\-]{3,}$', text): continue
                    current_paras.append(text)
    
    if current_paras:
        sections.append((current_title, current_paras))
    
    return sections

def get_knowledge_cards(html):
    cards = []
    for m in re.finditer(r'<div class="knowledge-card">(.*?)</div>\s*</div>', html, re.DOTALL):
        card_html = m.group(1)
        title_m = re.search(r'card-header[^>]*>(.*?)</div>', card_html, re.DOTALL)
        body_m = re.search(r'card-body[^>]*>(.*?)(?:</div>|$)', card_html, re.DOTALL)
        title = strip_tags(title_m.group(1)) if title_m else '法则笔记'
        title = re.sub(r'[⚡\s]+', '', title).strip()
        body = ''
        if body_m:
            body = process_bold(body_m.group(1))
            body = strip_tags(body)
            body = re.sub(r'\n{3,}', '\n\n', body).strip()
        if title and body:
            cards.append((title, body))
    return cards

def get_handson_experiments(html):
    exps = []
    for m in re.finditer(r'<div class="experiment-box">(.*?)</div>\s*</div>', html, re.DOTALL):
        e_html = m.group(1)
        title_m = re.search(r'exp-title[^>]*>(.*?)</div>', e_html, re.DOTALL)
        title = strip_tags(title_m.group(1)) if title_m else '动手实验'
        body = process_bold(e_html)
        body = strip_tags(body)
        lines = [l.strip() for l in body.split('\n') if l.strip()]
        exps.append((title, lines))
    return exps

def get_challenges(html):
    challenges = []
    for m in re.finditer(r'<div class="challenge-box">(.*?)</div>\s*</div>', html, re.DOTALL):
        c_html = m.group(1)
        title_m = re.search(r'challenge-title[^>]*>(.*?)</div>', c_html, re.DOTALL)
        q_m = re.search(r'<p[^>]*>(.*?)</p>', c_html, re.DOTALL)
        title = strip_tags(title_m.group(1)) if title_m else '挑战题'
        q_text = strip_tags(q_m.group(1)) if q_m else ''
        q_text = process_bold(q_text)
        q_text = strip_tags(q_text)
        options = []
        for opt in re.finditer(r'<label>(.*?)</label>', c_html, re.DOTALL):
            opt_text = strip_tags(opt.group(1))
            is_correct = 'data-correct="true"' in opt.group(0)
            options.append((opt_text, is_correct))
        challenges.append((title, q_text, options))
    return challenges

def format_bold(text):
    return re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

def build_html(ch_num, ch_title, topics, story_sections, cards, handson, challenges):
    lines = ['<!DOCTYPE html><html><head><meta charset="utf-8"><style>']
    lines.append('''
.wx-section{max-width:640px;margin:0 auto;padding:16px;font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif}
.wx-banner{background:linear-gradient(135deg,#1a237e,#283593);color:#fff;border-radius:12px;padding:22px;text-align:center;margin:16px 0}
.wx-banner h1{font-size:22px;margin:0 0 4px;color:#fff;letter-spacing:3px}
.wx-banner p{font-size:13px;margin:4px 0;color:rgba(255,255,255,.85)}
.wx-h2{font-size:17px;font-weight:700;color:#1a237e;margin:22px 0 12px;padding-bottom:6px;border-bottom:2px solid #1a237e}
.wx-h3{font-size:16px;font-weight:700;color:#283593;margin:18px 0 8px}
.wx-p{font-size:15px;line-height:1.8;margin:10px 0;text-indent:2em;color:#333}
.wx-divider{text-align:center;color:#bbb;margin:20px 0;font-size:16px;letter-spacing:8px}
.wx-card{margin:16px 0;border-radius:10px;overflow:hidden;border:1px solid #c5cae9}
.wx-card-header{background:linear-gradient(135deg,#e8eaf6,#c5cae9);padding:10px 16px;font-size:14px;font-weight:700;color:#1a237e}
.wx-card-body{background:#f5f6ff;padding:14px 16px;font-size:14px;line-height:1.8;color:#333}
.wx-card-body strong{color:#1a237e}
.wx-exp{margin:16px 0;border-radius:10px;overflow:hidden;border:1px solid #a5d6a7}
.wx-exp-header{background:linear-gradient(135deg,#e8f5e9,#c8e6c9);padding:10px 16px;font-size:14px;font-weight:700;color:#2e7d32}
.wx-exp-body{background:#f5fcf5;padding:14px 16px;font-size:14px;line-height:1.8;color:#333}
.wx-exp-body ol{padding-left:22px}
.wx-exp-body li{margin:5px 0}
.wx-exp-tip{background:#e8f5e9;border-radius:6px;padding:8px 12px;margin:8px 0;font-size:13px;border-left:3px solid #4caf50}
.wx-exp-warn{background:#fff3e0;border-radius:6px;padding:8px 12px;margin:8px 0;font-size:13px;border-left:3px solid #ff9800}
.wx-challenge{margin:16px 0;border-radius:10px;overflow:hidden;border:1px solid #ffcc80}
.wx-challenge-header{background:linear-gradient(135deg,#fff3e0,#ffe0b2);padding:10px 16px;font-size:14px;font-weight:700;color:#e65100}
.wx-challenge-body{background:#fffcf5;padding:14px 16px;font-size:14px;line-height:1.8;color:#333}
.wx-challenge-opt{padding:6px 10px;margin:3px 0;border-radius:4px;background:rgba(255,255,255,.6);font-size:14px}
.wx-correct{color:#2e7d32;font-weight:700}
.wx-interactive{background:linear-gradient(135deg,#e3f2fd,#bbdefb);border-radius:10px;padding:14px 16px;margin:16px 0;text-align:center;font-size:14px}
.wx-footer{text-align:center;margin:20px 0;padding:14px;background:#f5f5f5;border-radius:10px;font-size:13px;color:#666}
.wx-footer strong{color:#1a237e}
</style></head><body><div class="wx-section">''')
    
    # Banner
    banner = f'<div class="wx-banner"><h1>⚡ 物理解码者</h1><p>{escape_wx(ch_num)} · {escape_wx(ch_title)}</p>'
    if topics:
        banner += f'<p>📖 {escape_wx(topics)}</p>'
    banner += '</div>'
    lines.append(banner)
    
    # Story sections
    for title, paras in story_sections:
        if title:
            lines.append(f'<h3 class="wx-h3">{escape_wx(title)}</h3>')
        for p in paras:
            lines.append(f'<p class="wx-p">{format_bold(escape_wx(p))}</p>')
    
    # Knowledge cards
    if cards:
        lines.append('<h2 class="wx-h2">⚡ 法则笔记</h2>')
        for title, body in cards:
            body_html = format_bold(escape_wx(body)).replace('\n', '<br>')
            lines.append(f'<div class="wx-card"><div class="wx-card-header">📌 {escape_wx(title)}</div><div class="wx-card-body">{body_html}</div></div>')
    
    # Interactive hint
    lines.append('<h2 class="wx-h2">🔬 互动实验</h2>')
    lines.append('<div class="wx-interactive"><p style="margin:4px 0;text-indent:0;">💡 本章有 <strong>Canvas 交互模拟器</strong></p><p style="margin:4px 0;text-indent:0;">📱 回复 <strong>"异世法则"</strong> 获取互动电子书链接，亲手操作！</p></div>')
    
    # Hands-on experiments
    if handson:
        lines.append('<h2 class="wx-h2">🧪 动手探索</h2>')
        for title, body_lines in handson:
            parts_html = []
            in_ol = False
            for bl in body_lines:
                bl_e = format_bold(escape_wx(bl))
                if re.match(r'^\d+[.、]', bl_e) or bl_e.startswith('<strong>'):
                    if not in_ol:
                        parts_html.append('<ol>')
                        in_ol = True
                    parts_html.append(f'<li>{bl_e}</li>')
                else:
                    if in_ol:
                        parts_html.append('</ol>')
                        in_ol = False
                    if bl_e.startswith('💡') or bl_e.startswith('⚠'):
                        cls = 'wx-exp-tip' if bl_e.startswith('💡') else 'wx-exp-warn'
                        parts_html.append(f'<div class="{cls}">{bl_e}</div>')
                    else:
                        parts_html.append(f'<p style="margin:4px 0;text-indent:0;">{bl_e}</p>')
            if in_ol:
                parts_html.append('</ol>')
            lines.append(f'<div class="wx-exp"><div class="wx-exp-header">🔬 {escape_wx(title)}</div><div class="wx-exp-body">{"".join(parts_html)}</div></div>')
    
    # Challenges
    if challenges:
        lines.append('<h2 class="wx-h2">💡 脑力挑战</h2>')
        for title, q_text, options in challenges:
            opts = ''
            for ot, cor in options:
                ot_e = format_bold(escape_wx(ot))
                prefix = '✅' if cor else '⬜'
                suffix = ' <span class="wx-correct">✅ 正确答案</span>' if cor else ''
                opts += f'<div class="wx-challenge-opt">{prefix} {ot_e}{suffix}</div>'
            lines.append(f'<div class="wx-challenge"><div class="wx-challenge-header">{escape_wx(title)}</div><div class="wx-challenge-body"><p style="margin:4px 0;text-indent:0;">{format_bold(escape_wx(q_text))}</p>{opts}</div></div>')
    
    # Footer
    lines.append('<div class="wx-divider">✦ ✦ ✦</div>')
    lines.append('<div class="wx-footer"><p style="margin:4px 0;">📖 未完待续 · 下期继续冒险</p><p style="margin:4px 0;">🔬 回复 <strong>"异世法则"</strong> 获取互动电子书</p></div>')
    lines.append('</div></body></html>')
    
    return '\n'.join(lines)

def process(html_path, out_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    ch_num, ch_title = get_chapter_meta(html)
    topics = get_topics(html)
    story = get_story_sections(html)
    cards = get_knowledge_cards(html)
    handson = get_handson_experiments(html)
    challenges = get_challenges(html)
    result = build_html(ch_num, ch_title, topics, story, cards, handson, challenges)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"✅ {os.path.basename(out_path)} — 故事{len(story)}段, 卡片{len(cards)}, 实验{len(handson)}, 挑战{len(challenges)}")

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base, '公众号版')
    os.makedirs(out_dir, exist_ok=True)
    for rel_path in [
        'volumes/v01-漂移之原与回音峡谷/ch01.html',
        'volumes/v01-漂移之原与回音峡谷/ch02.html',
        'volumes/v02-炎寒谷的试炼/ch01.html',
        'volumes/v02-炎寒谷的试炼/ch02.html',
        'volumes/v03-镜海迷踪/ch01.html',
        'volumes/v03-镜海迷踪/ch02.html',
    ]:
        html_path = os.path.join(base, rel_path)
        if not os.path.exists(html_path): continue
        v = re.search(r'v(\d+)', rel_path).group(1)
        c = re.search(r'ch(\d+)', rel_path).group(1)
        with open(html_path, 'r', encoding='utf-8') as f:
            sample = f.read()
        _, title = get_chapter_meta(sample)
        out_name = f'V{v}C{c}-{title}-公众号.html'
        process(html_path, os.path.join(out_dir, out_name))

if __name__ == '__main__':
    main()
