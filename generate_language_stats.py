#!/usr/bin/env python3
"""
Generate language statistics SVG from GitHub repositories.
This script fetches all non-fork repositories for a user and aggregates
language statistics to create a visual SVG representation.
"""

import os
import sys
import json
import requests
from typing import Dict, List, Tuple
from collections import defaultdict


# Language color mapping (common GitHub language colors)
LANGUAGE_COLORS = {
    'Python': '#3572A5',
    'JavaScript': '#f1e05a',
    'TypeScript': '#2b7489',
    'Java': '#b07219',
    'C': '#555555',
    'C++': '#f34b7d',
    'C#': '#178600',
    'PHP': '#4F5D95',
    'Ruby': '#701516',
    'Go': '#00ADD8',
    'Rust': '#dea584',
    'Swift': '#ffac45',
    'Kotlin': '#F18E33',
    'Dart': '#00B4AB',
    'Shell': '#89e051',
    'HTML': '#e34c26',
    'CSS': '#563d7c',
    'Vue': '#41b883',
    'Jupyter Notebook': '#DA5B0B',
    'R': '#198CE7',
    'Scala': '#c22d40',
    'Perl': '#0298c3',
    'Haskell': '#5e5086',
    'Lua': '#000080',
    'Objective-C': '#438eff',
    'MATLAB': '#e16737',
}

DEFAULT_COLOR = '#858585'


def get_username() -> str:
    """Get the GitHub username from environment or default."""
    # Check GITHUB_REPOSITORY first (format: owner/repo)
    github_repo = os.environ.get('GITHUB_REPOSITORY', '')
    if github_repo and '/' in github_repo:
        return github_repo.split('/')[0]
    
    # Fall back to default
    return 'riqueamais'


def fetch_repositories(username: str, token: str = None) -> List[Dict]:
    """Fetch all non-fork repositories for a user with pagination."""
    repos = []
    page = 1
    per_page = 100
    
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    
    while True:
        url = f'https://api.github.com/users/{username}/repos'
        params = {'per_page': per_page, 'page': page, 'type': 'owner'}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
            
            # Filter out forks
            non_fork_repos = [repo for repo in page_repos if not repo.get('fork', False)]
            repos.extend(non_fork_repos)
            
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}", file=sys.stderr)
            break
    
    return repos


def fetch_language_stats(repos: List[Dict], token: str = None) -> Dict[str, int]:
    """Aggregate language statistics from all repositories."""
    language_bytes = defaultdict(int)
    
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    
    for repo in repos:
        languages_url = repo.get('languages_url')
        if not languages_url:
            continue
        
        try:
            response = requests.get(languages_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            languages = response.json()
            for language, bytes_count in languages.items():
                language_bytes[language] += bytes_count
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching languages for {repo.get('name', 'unknown')}: {e}", file=sys.stderr)
            continue
    
    return dict(language_bytes)


def get_top_languages(language_bytes: Dict[str, int], top_n: int = 6) -> List[Tuple[str, int, float]]:
    """Get top N languages by bytes with percentages."""
    if not language_bytes:
        return []
    
    total_bytes = sum(language_bytes.values())
    if total_bytes == 0:
        return []
    
    # Sort by bytes (descending)
    sorted_languages = sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)
    
    # Get top N and calculate percentages
    top_languages = []
    for language, bytes_count in sorted_languages[:top_n]:
        percentage = (bytes_count / total_bytes) * 100
        top_languages.append((language, bytes_count, percentage))
    
    return top_languages


def generate_svg(top_languages: List[Tuple[str, int, float]], output_path: str):
    """Generate an SVG visualization of language statistics."""
    
    if not top_languages:
        # Generate empty/no data SVG
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100" viewBox="0 0 400 100">
  <rect width="400" height="100" fill="#0d1117" rx="4"/>
  <text x="200" y="50" font-family="Arial, sans-serif" font-size="16" fill="#c9d1d9" text-anchor="middle" dominant-baseline="middle">
    No languages found
  </text>
</svg>'''
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        return
    
    # Calculate SVG dimensions
    bar_height = 20
    bar_spacing = 15
    padding = 20
    width = 450
    header_height = 40
    content_height = len(top_languages) * (bar_height + bar_spacing) - bar_spacing
    height = header_height + content_height + padding * 2
    
    # Start building SVG
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'  <rect width="{width}" height="{height}" fill="#0d1117" rx="4"/>',
        f'  <text x="{padding}" y="{padding + 20}" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#c9d1d9">Most Used Languages</text>',
    ]
    
    # Add language bars
    y_offset = header_height + padding
    
    for language, bytes_count, percentage in top_languages:
        color = LANGUAGE_COLORS.get(language, DEFAULT_COLOR)
        
        # Language name
        svg_parts.append(
            f'  <text x="{padding}" y="{y_offset + bar_height/2}" '
            f'font-family="Arial, sans-serif" font-size="14" fill="#c9d1d9" dominant-baseline="middle">{language}</text>'
        )
        
        # Progress bar background
        bar_x = 150
        bar_width = width - bar_x - padding - 60
        svg_parts.append(
            f'  <rect x="{bar_x}" y="{y_offset}" width="{bar_width}" height="{bar_height}" '
            f'fill="#21262d" rx="4"/>'
        )
        
        # Progress bar fill
        fill_width = (percentage / 100) * bar_width
        svg_parts.append(
            f'  <rect x="{bar_x}" y="{y_offset}" width="{fill_width}" height="{bar_height}" '
            f'fill="{color}" rx="4"/>'
        )
        
        # Percentage text
        percent_x = width - padding - 50
        svg_parts.append(
            f'  <text x="{percent_x}" y="{y_offset + bar_height/2}" '
            f'font-family="Arial, sans-serif" font-size="14" fill="#8b949e" text-anchor="end" dominant-baseline="middle">{percentage:.1f}%</text>'
        )
        
        y_offset += bar_height + bar_spacing
    
    svg_parts.append('</svg>')
    
    svg_content = '\n'.join(svg_parts)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"Generated SVG with {len(top_languages)} languages")


def main():
    """Main function to generate language statistics."""
    username = get_username()
    token = os.environ.get('GITHUB_TOKEN')
    
    print(f"Fetching repositories for user: {username}")
    
    repos = fetch_repositories(username, token)
    print(f"Found {len(repos)} non-fork repositories")
    
    if not repos:
        print("No repositories found, generating empty SVG")
        generate_svg([], 'language_stats.svg')
        return 0
    
    language_bytes = fetch_language_stats(repos, token)
    print(f"Collected statistics for {len(language_bytes)} languages")
    
    top_languages = get_top_languages(language_bytes, top_n=6)
    
    if top_languages:
        print("Top languages:")
        for lang, bytes_count, percentage in top_languages:
            print(f"  {lang}: {percentage:.1f}%")
    
    generate_svg(top_languages, 'language_stats.svg')
    print("Successfully generated language_stats.svg")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
