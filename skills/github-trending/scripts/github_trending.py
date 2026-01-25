#!/usr/bin/env python3
"""
GitHub Trending 爬虫脚本
获取 GitHub 热门项目和仓库 README
"""

import requests
from bs4 import BeautifulSoup
import re
import sys
import argparse
from datetime import datetime


def get_github_trending(since: str = "daily", language: str = "") -> str:
    """获取 GitHub trending 榜单"""
    url = f"https://github.com/trending/{language.lower()}?since={since}" if language else f"https://github.com/trending?since={since}"

    try:
        current_date = datetime.now()
        date_str = current_date.strftime("%Y年%m月%d日")
        weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_str = weekday_names[current_date.weekday()]
        since_display = {"daily": "今日", "weekly": "本周", "monthly": "本月"}

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('article', class_='Box-row')

        if not articles:
            return f"❌ 未找到 trending 项目\n请求URL: {url}"

        result = []
        result.append(f"🌟 GitHub Trending Repositories")
        result.append(f"📅 获取时间: {date_str} {weekday_str}")
        result.append(f"⏰ 时间范围: {since_display.get(since, since)}")
        if language:
            result.append(f"💻 编程语言: {language}")
        result.append(f"📊 共发现 {len(articles)} 个热门项目")
        result.append("")

        for i, article in enumerate(articles, 1):
            try:
                title_elem = article.find('h2', class_='h3')
                if not title_elem:
                    continue
                title_link = title_elem.find('a')
                if not title_link:
                    continue

                title = ' '.join(title_link.get_text(strip=True).split())
                project_url = "https://github.com" + title_link.get('href', '')

                description_elem = article.find('p', class_='col-9')
                description = description_elem.get_text(strip=True) if description_elem else "无描述"

                language_elem = article.find('span', {'itemprop': 'programmingLanguage'})
                project_language = language_elem.get_text(strip=True) if language_elem else "未知"

                star_link = article.find('a', href=re.compile(r'/stargazers'))
                total_stars = star_link.get_text(strip=True) if star_link else "0"

                fork_link = article.find('a', href=re.compile(r'/forks'))
                total_forks = fork_link.get_text(strip=True) if fork_link else "0"

                period_stars = "0"
                for span in article.find_all('span'):
                    span_text = span.get_text(strip=True)
                    if 'stars' in span_text.lower() and ('today' in span_text.lower() or 'this week' in span_text.lower() or 'this month' in span_text.lower()):
                        period_match = re.search(r'(\d+[,\d]*)\s*stars?', span_text, re.IGNORECASE)
                        if period_match:
                            period_stars = period_match.group(1)
                        break

                result.append(f"{i}. {title}")
                result.append(f"   🔗 {project_url}")
                result.append(f"   📝 {description}")
                result.append(f"   💻 语言: {project_language} | ⭐ 总星数: {total_stars} | 🍴 Forks: {total_forks} | 🔥 {since_display.get(since, since)}: +{period_stars}")

            except Exception as e:
                result.append(f"❌ 解析第 {i} 个项目时出错: {str(e)}")
                continue

        return "\n".join(result)

    except requests.exceptions.RequestException as e:
        return f"❌ 网络请求错误: {str(e)}\n请求URL: {url}"
    except Exception as e:
        return f"❌ 程序执行错误: {str(e)}"


def get_repository_readme(repo: str) -> str:
    """获取指定仓库的 README"""
    repo = repo.strip()
    branches = ['main', 'master']
    readme_files = ['README.md', 'readme.md', 'Readme.md', 'README.txt', 'readme.txt']

    for branch in branches:
        for readme_file in readme_files:
            url = f"https://raw.githubusercontent.com/{repo}/refs/heads/{branch}/{readme_file}"
            try:
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    content = response.text
                    if len(content) > 50000:
                        content = content[:50000] + "\n\n... [内容过长，已截断] ..."
                    return f"✅ 成功获取 {repo} 的 README\n来源: {url}\n\n{content}"
            except:
                continue

    return f"❌ 未找到 {repo} 的 README 文件"


def main():
    parser = argparse.ArgumentParser(description='GitHub Trending 工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # trending 子命令
    trending_parser = subparsers.add_parser('trending', help='获取 trending 列表')
    trending_parser.add_argument('--since', '-s', default='daily', choices=['daily', 'weekly', 'monthly'], help='时间范围')
    trending_parser.add_argument('--language', '-l', default='', help='编程语言过滤')

    # readme 子命令
    readme_parser = subparsers.add_parser('readme', help='获取仓库 README')
    readme_parser.add_argument('repo', help='仓库名称 (owner/repo)')

    args = parser.parse_args()

    if args.command == 'trending':
        print(get_github_trending(args.since, args.language))
    elif args.command == 'readme':
        print(get_repository_readme(args.repo))
    else:
        # 默认行为：获取 daily trending
        print(get_github_trending())


if __name__ == "__main__":
    main()
