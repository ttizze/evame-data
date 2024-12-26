import os
import re


def is_number(s):
    """文字列が数字かK+数字かどうかをチェック"""
    if s.isdigit():
        return True
    # Kで始まり、残りが数字の場合もTrue
    if s.startswith('K') and s[1:].isdigit():
        return True
    return False


def process_frontmatter(content):
    """Frontmatterを処理してタグを更新"""
    # YAMLフロントマターを探す
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return content
    frontmatter_text = match.group(1)
    # タグ行を見つける
    tag_match = re.search(r'^tags:(.*)$', frontmatter_text, re.MULTILINE)
    if tag_match:
        tags_text = tag_match.group(1).strip()
        # 既存のタグをパース
        if tags_text.startswith('[') and tags_text.endswith(']'):
            # ["tag1", "tag2"] 形式の場合
            tags = [tag.strip().strip('"\'') for tag in tags_text[1:-1].split(',') if tag.strip()]
        elif tags_text:
            # - tag1\n- tag2 形式の場合
            tags = [tag.strip().strip('- ') for tag in tags_text.split('\n') if tag.strip()]
        else:
            tags = []
        # タグを処理
        new_tags = []
        for tag in tags:
            if tag and is_number(tag):
                new_tags.append(f'NDC{tag}')
            else:
                new_tags.append(tag)
        # 新しいタグ行を作成（["tag1", "tag2"]形式）
        new_tags_text = f'tags: ["{"\", \"".join(new_tags)}"]'
        # フロントマターを更新
        new_frontmatter = re.sub(
            r'^tags:.*?$',
            new_tags_text,
            frontmatter_text,
            flags=re.MULTILINE
        )
        # 元のコンテンツを更新
        return f"---\n{new_frontmatter}\n---{content[match.end():]}"
    return content


def process_markdown_files(directory):
    """指定ディレクトリ以下のMarkdownファイルを処理"""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                # ファイルを読み込み
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # フロントマターを処理
                new_content = process_frontmatter(content)
                # 変更があれば保存
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"更新しました: {file_path}")


if __name__ == "__main__":
    directory = "./aozorabunko"
    process_markdown_files(directory)
