#!/usr/bin/env python3
"""
将飞书知识库导出的 Markdown 文件转化为 CSV 问答对。
最终优化版本：
- 过滤掉无实质内容的问答对（只有标题复述的）
- 优化表格处理
- 合并短段落文档为完整的操作指引
- 生成自然流畅的中文问答
"""

import os
import re
import csv
import glob
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

MARKDOWN_DIR = r"d:\AI\feishu\all_markdowns"
OUTPUT_CSV = r"d:\AI\feishu\knowledge_base_qa.csv"

# === 文本清理工具 ===

def clean_text(text: str) -> str:
    """清理 Markdown 文本"""
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'📎\s*\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'```\w*\n?', '', text)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def clean_heading(text: str) -> str:
    """清理标题文本"""
    text = re.sub(r'^#{1,6}\s+', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[：:]\s*$', '', text)
    text = text.strip()
    return text


def is_question_like(title: str) -> bool:
    """判断标题是否像一个问题"""
    patterns = [
        r'怎么', r'如何', r'什么', r'为什么', r'哪里', r'在哪', r'是否',
        r'能不能', r'可以.*吗', r'.*吗[？?]?$', r'.*？$', r'\?$',
        r'怎样', r'多少', r'哪个', r'哪些', r'几个',
    ]
    return any(re.search(p, title) for p in patterns)


# === 问题生成 ===

def title_to_question(title: str) -> str:
    """将标题转换为自然问句"""
    title = clean_heading(title)
    if is_question_like(title):
        return title if title.endswith('？') or title.endswith('?') else title + '？'

    if '流程' in title:
        return f'{title}是怎样的？'
    elif '指南' in title:
        return f'{title}怎么操作？'
    elif '说明' in title:
        return f'{title}怎么操作？'
    elif '方法' in title or '解决办法' in title:
        return f'{title}是什么？'
    elif '驱动' in title and '安装' in title:
        return f'如何{title}？'
    elif '驱动' in title:
        return f'{title}怎么安装和使用？'
    elif '安装' in title:
        return f'如何{title}？'
    elif '对接' in title:
        return f'{title}怎么操作？'
    elif '规则' in title or '策略' in title:
        return f'{title}是什么？'
    elif '登录' in title and '下载' in title:
        return f'{title}的网址和操作方式是什么？'
    elif '登录' in title:
        return f'{title}是什么？'
    elif '下载' in title:
        return f'如何{title}？'
    elif '常见问题' in title or '常见QA' in title:
        return f'{title}有哪些？'
    elif '配置' in title or '设备' in title:
        return f'{title}是什么？'
    elif '方案' in title:
        return f'{title}是什么？'
    elif '地图' in title:
        return f'{title}？'
    elif '退货' in title:
        return f'{title}怎么操作？'
    elif '配对' in title:
        return f'{title}怎么操作？'
    elif '测试' in title or '推流' in title:
        return f'{title}怎么使用？'
    elif '打印机' in title or '鼠标' in title:
        return f'{title}怎么设置和使用？'
    elif '转发' in title:
        return f'如何{title}？'
    elif '跳过' in title:
        return f'{title}'
    else:
        return f'请介绍一下{title}。'


def section_to_question(h1: str, sec: str) -> str:
    """将 ## 段落标题转换为带上下文的问句"""
    sec = clean_heading(sec)
    h1 = clean_heading(h1)

    if is_question_like(sec):
        return sec if sec.endswith('？') or sec.endswith('?') else sec + '？'

    if '流程' in sec or '步骤' in sec:
        return f'{h1}中，{sec}怎么操作？'
    elif '注意事项' in sec or '注意' in sec:
        return f'{h1}的注意事项有哪些？'
    elif '字段' in sec or '定义' in sec:
        return f'{h1}的{sec}是什么？'
    elif '打印' in sec:
        return f'{h1}中如何打印？'
    elif '导出' in sec:
        return f'{h1}中如何导出数据？'
    elif '退货' in sec:
        return f'{h1}中退货怎么处理？'
    elif '审批' in sec or '审核' in sec:
        return f'{h1}中{sec}怎么操作？'
    elif '下载' in sec:
        return f'{h1}在哪下载？'
    elif '登录' in sec:
        return f'{h1}怎么登录？'
    elif '配置' in sec or '设置' in sec:
        return f'{h1}的{sec}怎么操作？'
    elif '区别' in sec:
        return f'{sec}是什么？'
    elif '内部分工' in sec or '找人' in sec:
        return f'{h1}中各角色的分工是什么？找谁负责什么？'
    elif sec.startswith(('一、', '二、', '三、', '四、', '五、')):
        return f'{h1}中{sec}怎么操作？'
    else:
        return f'{h1}中，{sec}是什么？'


# === Markdown 解析 ===

def parse_h2_sections(content: str):
    """按 ## 标题分割内容"""
    lines = content.split('\n')
    sections = []
    cur_title = None
    cur_lines = []
    pre_h2_lines = []  # ## 之前的内容

    for line in lines:
        m = re.match(r'^##\s+(.+)', line)
        if m and not line.startswith('###'):
            if cur_title is not None:
                sections.append((cur_title, '\n'.join(cur_lines)))
            elif cur_lines:
                pre_h2_lines = cur_lines[:]
            cur_title = m.group(1).strip()
            cur_lines = []
        else:
            cur_lines.append(line)

    if cur_title is not None:
        sections.append((cur_title, '\n'.join(cur_lines)))

    return pre_h2_lines, sections


def extract_h1(content: str):
    m = re.match(r'^#\s+(.+)', content.strip())
    return m.group(1).strip() if m else None


def body_after_h1(content: str) -> str:
    lines = content.strip().split('\n')
    if lines and re.match(r'^#\s+', lines[0]):
        return '\n'.join(lines[1:])
    return content


# === 表格处理 ===

def table_to_text(text: str) -> str:
    """Markdown 表格 → 可读纯文本"""
    lines = text.split('\n')
    result = []
    headers = []
    rows = []
    in_table = False

    def flush():
        nonlocal headers, rows, in_table
        if rows:
            for row in rows:
                parts = []
                for i, cell in enumerate(row):
                    cell = cell.strip()
                    if not cell:
                        continue
                    if headers and i < len(headers) and headers[i].strip():
                        parts.append(f"{headers[i].strip()}：{cell}")
                    else:
                        parts.append(cell)
                if parts:
                    result.append('；'.join(parts))
        elif headers:
            h = [h.strip() for h in headers if h.strip()]
            if h:
                result.append('；'.join(h))
        headers = []
        rows = []
        in_table = False

    for line in lines:
        s = line.strip()
        if s.startswith('|') and s.endswith('|') and '|' in s[1:-1]:
            cells = [c.strip() for c in s.split('|')[1:-1]]
            if all(re.match(r'^[-:]+$', c) for c in cells if c):
                in_table = True
                continue
            if not in_table and not headers:
                headers = cells
                in_table = True
            else:
                rows.append(cells)
        else:
            flush()
            result.append(line)

    flush()
    return '\n'.join(result)


# === 核心处理逻辑 ===

def has_real_content(text: str, section_title: str = '') -> bool:
    """判断清理后的文本是否有实质内容（不只是复述标题）"""
    cleaned = clean_text(text)
    if not cleaned or len(cleaned) < 5:
        return False
    # 如果文本和标题几乎一样，说明没有额外信息
    title_clean = clean_heading(section_title) if section_title else ''
    if title_clean and cleaned.strip() == title_clean.strip():
        return False
    return True


def process_file(filepath: str) -> list:
    """处理单个 Markdown 文件，返回 (question, answer, source) 列表"""
    qa_pairs = []
    filename = os.path.basename(filepath)
    doc_name = os.path.splitext(filename)[0]

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    stripped = content.strip()
    if not stripped:
        return []

    non_empty = [l for l in stripped.split('\n') if l.strip()]
    if len(non_empty) <= 1:
        return []

    h1 = extract_h1(content) or doc_name
    body = body_after_h1(content)
    pre_h2, sections = parse_h2_sections(body)

    # --- 注意事项/提示块（在 ## 之前的 > 引用块）---
    pre_text = clean_text('\n'.join(pre_h2))

    if len(sections) >= 2:
        # 检查是否所有段落都太短（仅有标题+图片的情况）
        real_sections = [(t, c) for t, c in sections if has_real_content(c, t)]
        only_title_sections = [(t, c) for t, c in sections if not has_real_content(c, t)]

        if len(real_sections) == 0 and len(only_title_sections) >= 2:
            # 所有 ## 都没有实质文本内容，合并标题为操作步骤
            steps = []
            for i, (title, _) in enumerate(sections, 1):
                t = clean_heading(title)
                if t:
                    steps.append(f"{i}. {t}")
            answer = '\n'.join(steps)
            if pre_text:
                answer = f"注意事项：{pre_text}\n\n操作步骤：\n{answer}"
            question = title_to_question(h1)
            qa_pairs.append((question, answer, doc_name))
        else:
            # 正常多段落：每个有实质内容的 ## 生成一个 QA
            # 如果有前置注意事项，先生成一个注意事项 QA
            if pre_text and len(pre_text) > 15:
                qa_pairs.append((
                    f'{clean_heading(h1)}的注意事项和说明是什么？',
                    pre_text,
                    doc_name
                ))

            for sec_title, sec_content in sections:
                cleaned = clean_text(sec_content)
                if not cleaned or len(cleaned) < 5:
                    # 用子标题文本本身作为简要回答（但前提是标题足够有信息量）
                    title_text = clean_heading(sec_title)
                    if len(title_text) > 10:
                        cleaned = title_text
                    else:
                        continue

                question = section_to_question(h1, sec_title)
                qa_pairs.append((question, cleaned, doc_name))

    elif len(sections) == 1:
        full = clean_text(body)
        if full and len(full) >= 5:
            question = title_to_question(h1)
            qa_pairs.append((question, full, doc_name))

    else:
        full = clean_text(body)
        if full and len(full) >= 5:
            question = title_to_question(h1)
            qa_pairs.append((question, full, doc_name))

    return qa_pairs


def main():
    all_pairs = []
    md_files = glob.glob(os.path.join(MARKDOWN_DIR, '*.md'))
    print(f"找到 {len(md_files)} 个 Markdown 文件")

    skipped = []
    for fp in sorted(md_files):
        pairs = process_file(fp)
        if pairs:
            all_pairs.extend(pairs)
        else:
            skipped.append(os.path.basename(fp))

    # 后处理
    final = []
    for q, a, src in all_pairs:
        a = table_to_text(a)
        a = re.sub(r'\n{3,}', '\n\n', a).strip()
        q = q.strip()
        # 过滤：答案不能只是问题的复述
        if q and a and len(a) >= 5:
            final.append((q, a, src))

    # 写入CSV
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['question', 'answer', 'source_document'])
        for q, a, src in final:
            writer.writerow([q, a, src])

    print(f"\n✅ 成功生成 {len(final)} 个问答对")
    print(f"📄 CSV文件：{OUTPUT_CSV}")

    if skipped:
        print(f"\n⚠️  跳过 {len(skipped)} 个空/无内容文档：")
        for s in skipped:
            print(f"   - {s}")

    # 按来源统计
    from collections import Counter
    src_counts = Counter(src for _, _, src in final)
    print(f"\n📊 各文档生成的问答数量：")
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        print(f"   {src}: {cnt} 条")

    # 示例
    print(f"\n{'='*60}")
    print(f"问答对示例")
    print(f"{'='*60}")
    for i, (q, a, src) in enumerate(final[:8]):
        print(f"\n【问题 {i+1}】{q}")
        preview = a[:250] + '...' if len(a) > 250 else a
        print(f"【回答】{preview}")
        print(f"【来源】{src}")

    print(f"\n{'='*60}")
    print(f"共计 {len(final)} 个问答对，来自 {len(src_counts)} 个文档")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
