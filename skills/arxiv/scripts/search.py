#!/usr/bin/env python3
"""arxiv 论文搜索脚本"""

import argparse
import arxiv


def search_arxiv(query: str, max_results: int = 20):
    """搜索 arxiv 论文，按日期降序排列"""
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    results = []
    for paper in client.results(search):
        results.append({
            'title': paper.title,
            'authors': ', '.join([author.name for author in paper.authors]),
            'published': paper.published.strftime('%Y-%m-%d'),
            'abstract': paper.summary,
            'pdf_url': paper.pdf_url
        })

    return results


def format_as_markdown(results):
    """格式化为 markdown 表格 + 详细摘要"""
    if not results:
        return "未找到相关论文。"

    # 表格概览
    output = "## 搜索结果\n\n"
    output += "| # | 标题 | 作者 | 发布日期 | PDF |\n"
    output += "|---|------|------|----------|-----|\n"

    for i, paper in enumerate(results, 1):
        title = paper['title'].replace('|', '\\|').replace('\n', ' ')
        authors = paper['authors'].replace('|', '\\|')
        if len(authors) > 50:
            authors = authors[:47] + "..."
        output += f"| {i} | {title} | {authors} | {paper['published']} | [PDF]({paper['pdf_url']}) |\n"

    # 详细摘要
    output += "\n---\n\n## 论文详情\n\n"
    for i, paper in enumerate(results, 1):
        output += f"### {i}. {paper['title']}\n\n"
        output += f"**作者**: {paper['authors']}\n\n"
        output += f"**发布日期**: {paper['published']}\n\n"
        output += f"**PDF**: {paper['pdf_url']}\n\n"
        output += f"**摘要**: {paper['abstract']}\n\n"
        output += "---\n\n"

    return output


def main():
    parser = argparse.ArgumentParser(description='搜索 arxiv 论文')
    parser.add_argument('query', type=str, help='搜索关键词')
    parser.add_argument('-n', '--num', type=int, default=20, help='返回结果数量（默认 20）')

    args = parser.parse_args()

    results = search_arxiv(args.query, args.num)
    print(format_as_markdown(results))


if __name__ == '__main__':
    main()
