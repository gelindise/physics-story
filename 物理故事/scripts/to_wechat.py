#!/usr/bin/env python3
"""
Extract story content from HTML chapter files → WeChat Official Account Markdown.
Usage: python3 scripts/to_wechat.py
Output: 公众号版/*.md
"""

import re, os

def strip_tags(text):
    """Remove HTML tags, keep content, normalize whitespace."""
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def strip_em(text):
    """Remove emphasis HTML tags but keep content."""
    text = re.sub(r'<em>(.*?)</em>', r'\1', text)
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
    return text

def extract_chapter_title(html):
    """Extract chapter number + title from h1/h2."""
    ch_num = ''
    ch_title = ''
    
    m = re.search(r'<h2[^>]*>(?:第[一二三四五六七八九十]+章|第一章|第二章)</h2>', html)
    if m:
        ch_num = strip_tags(m.group(0))
    
    m = re.search(r'<h1[^>]*style="[^"]*text-align:center[^"]*"[^>]*>(.*?)</h1>', html)
    if m:
        ch_title = strip_tags(m.group(1))
    
    return ch_num, ch_title

def extract_paragraphs(html):
    """Extract story paragraphs from div.reader-content, excluding special sections."""
    # Get the reader-content div
    m = re.search(r'class="reader-content">(.*?)</div>\s*<script', html, re.DOTALL)
    if not m:
        m = re.search(r'class="reader-content">(.*)', html, re.DOTALL)
    if not m:
        return []
    
    content = m.group(1)
    
    # Remove all special containers
    content = re.sub(r'<div class="knowledge-card">.*?</div>\s*</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div class="canvas-container">.*?</div>\s*</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div class="experiment-box">.*?</div>\s*</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div class="challenge-box">.*?</div>\s*</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div class="note-box">.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script>.*?</script>', '', content, flags=re.DOTALL)
    
    # Extract paragraphs
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
    result = []
    for p in paragraphs:
        text = strip_em(p)
        text = strip_tags(text)
        if text:
            result.append(text)
    
    return result

def extract_knowledge_cards(html):
    """Extract knowledge cards."""
    cards = re.findall(r'<div class="knowledge-card">(.*?)(?:</div>\s*</div>|</article>|(?=<div class="story-divider))', html, re.DOTALL)
    results = []
    
    for card_html in cards:
        title_m = re.search(r'card-header[^>]*>(.*?)(?:</div>|$)', card_html, re.DOTALL)
        body_m = re.search(r'card-body[^>]*>(.*?)(?:</div>\s*</div>|$)', card_html, re.DOTALL)
        
        title = strip_tags(title_m.group(1)) if title_m else '法则笔记'
        title = re.sub(r'⚡\s*', '', title).strip()
        
        body = ''
        if body_m:
            body = strip_em(body_m.group(1))
            body = strip_tags(body)
            body = re.sub(r'\n{3,}', '\n\n', body)
        
        results.append((title, body))
    
    return results

def extract_experiments(html):
    """Extract hands-on experiment boxes."""
    exps = re.findall(r'<div class="experiment-box">(.*?)</div>\s*</div>', html, re.DOTALL)
    results = []
    
    for exp in exps:
        title_m = re.search(r'exp-title[^>]*>(.*?)</div>', exp, re.DOTALL)
        title = strip_tags(title_m.group(1)) if title_m else '动手实验'
        
        body = strip_em(exp)
        body = strip_tags(body)
        body = re.sub(r'\n{3,}', '\n\n', body)
        
        results.append((title, body))
    
    return results

def extract_challenges(html):
    """Extract challenge questions."""
    challenges = re.findall(r'<div class="challenge-box">(.*?)</div>\s*</div>', html, re.DOTALL)
    results = []
    
    for ch in challenges:
        title_m = re.search(r'challenge-title[^>]*>(.*?)</div>', ch, re.DOTALL)
        q_text_m = re.search(r'<p[^>]*>(.*?)</p>', ch, re.DOTALL)
        
        title = strip_tags(title_m.group(1)) if title_m else '挑战题'
        q_text = strip_em(q_text_m.group(1)) if q_text_m else ''
        q_text = strip_tags(q_text)
        
        options = []
        for opt in re.findall(r'<label>(.*?)</label>', ch, re.DOTALL):
            is_correct = 'data-correct="true"' in opt
            opt_text = strip_tags(opt)
            options.append((opt_text, is_correct))
        
        results.append((title, q_text, options))
    
    return results

def extract_interactive_experiments(html):
    """Extract interactive experiment descriptions."""
    exps = re.findall(r'<h3>🔬[^<]*</h3>\s*<p[^>]*class="no-indent"[^>]*>(.*?)</p>', html, re.DOTALL)
    return [strip_tags(e) for e in exps]

def process_chapter(html_path, output_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    lines = []
    
    ch_num, ch_title = extract_chapter_title(html)
    
    # Header
    lines.append(f'> ⚡ **物理解码者：异世法则**')
    lines.append('')
    
    if ch_num:
        lines.append(f'# {ch_num} {ch_title}')
    else:
        lines.append(f'# {ch_title}')
    lines.append('')
    lines.append('---')
    lines.append('')
    
    # Story paragraphs
    paragraphs = extract_paragraphs(html)
    for p in paragraphs:
        # Skip story dividers
        if re.match(r'^[✦✧\s\*]{3,}$', p):
            lines.append('---')
            lines.append('')
            continue
        # Skip "第X章 完" or navigation links
        if re.match(r'^[—\-–]{2,}\s*第.*章\s*完', p):
            lines.append('')
            lines.append('---')
            lines.append('')
            continue
        if '继续阅读' in p or '返回书架' in p:
            continue
        
        lines.append(p)
        lines.append('')
    
    # Knowledge Cards
    cards = extract_knowledge_cards(html)
    if cards:
        lines.append('---')
        lines.append('')
        lines.append('## ⚡ 法则笔记')
        lines.append('')
        for title, body in cards:
            lines.append(f'**📌 {title}**')
            lines.append('')
            if body:
                # Split into lines and add
                for line in body.split('\n'):
                    line = line.strip()
                    if line:
                        lines.append(f'> {line}')
                lines.append('')
    
    # Interactive Experiments
    interactive_exps = extract_interactive_experiments(html)
    if interactive_exps:
        lines.append('---')
        lines.append('')
        lines.append('## 🔬 互动实验')
        lines.append('')
        for exp in interactive_exps:
            lines.append(f'> 💡 {exp}')
            lines.append('')
            lines.append(f'> （在互动电子书中为可操作模拟器，公众号版仅展示说明）')
            lines.append('')
    
    # Hands-on Experiments
    experiments = extract_experiments(html)
    if experiments:
        lines.append('---')
        lines.append('')
        lines.append('## 🧪 动手探索')
        lines.append('')
        for title, body in experiments:
            lines.append(f'### {title}')
            lines.append('')
            for line in body.split('\n'):
                line = line.strip()
                if line:
                    lines.append(line)
            lines.append('')
    
    # Challenges
    challenges = extract_challenges(html)
    if challenges:
        lines.append('---')
        lines.append('')
        lines.append('## 💡 脑力挑战（答案在文末）')
        lines.append('')
        for title, q_text, options in challenges:
            lines.append(f'**{title}**')
            lines.append('')
            lines.append(q_text)
            lines.append('')
            for i, (opt_text, is_correct) in enumerate(options):
                lines.append(f'- {chr(65+i)}. {opt_text}')
            lines.append('')
    
    # Answers
    if challenges:
        lines.append('---')
        lines.append('')
        lines.append('**✅ 参考答案**')
        lines.append('')
        for title, q_text, options in challenges:
            q_num = re.search(r'问题(\d+)', title)
            num = q_num.group(1) if q_num else '?'
            for i, (opt_text, is_correct) in enumerate(options):
                if is_correct:
                    lines.append(f'- 第{num}题：{chr(65+i)}')
            lines.append('')
    
    # Volume end notice
    lines.append('---')
    lines.append('')
    lines.append('📖 *未完待续，下期继续冒险！*')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('> 🏠 **返回书架**：关注公众号，点击菜单栏「异世法则」查看全部章节')
    lines.append('> 🔬 **互动电子书**：访问网页版可体验Canvas交互实验')
    
    output = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"✅ {os.path.basename(output_path)} ({len(lines)} 行)")

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wechat_dir = os.path.join(base, '公众号版')
    os.makedirs(wechat_dir, exist_ok=True)
    
    chapters = [
        'volumes/v01-漂移之原与回音峡谷/ch01.html',
        'volumes/v01-漂移之原与回音峡谷/ch02.html',
        'volumes/v02-炎寒谷的试炼/ch01.html',
        'volumes/v02-炎寒谷的试炼/ch02.html',
    ]
    
    for rel_path in chapters:
        html_path = os.path.join(base, rel_path)
        if not os.path.exists(html_path):
            print(f"⚠️ Not found: {html_path}")
            continue
        
        # Create output filename
        vol_match = re.search(r'v(\d+)-', rel_path)
        ch_match = re.search(r'ch(\d+)\.html', rel_path)
        vol_num = vol_match.group(1) if vol_match else '?'
        ch_num = ch_match.group(1) if ch_match else '?'
        
        # Read first few lines to determine title
        with open(html_path, 'r', encoding='utf-8') as f:
            sample = f.read()
        
        ch_title = ''
        m = re.search(r'<h1[^>]*style="[^"]*text-align:center[^"]*"[^>]*>(.*?)</h1>', sample)
        if m:
            ch_title = strip_tags(m.group(1))
        
        out_name = f'V{vol_num}C{ch_num}-{ch_title}.md'
        out_path = os.path.join(wechat_dir, out_name)
        
        process_chapter(html_path, out_path)

if __name__ == '__main__':
    main()
