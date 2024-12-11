import os
import re
from unidecode import unidecode
from slugify import slugify
import yaml
import uuid

def generate_unique_slug(title):
    # タイトルから基本スラグ生成
    temp_slug = slugify(unidecode(title))
    base_slug = re.sub(r'[^a-zA-Z0-9]', '', temp_slug)
    random_suffix = uuid.uuid4().hex[:2]
    unique_slug = f"{base_slug}{random_suffix}"
    return unique_slug

def update_frontmatter(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # フロントマター抽出
    match = re.match(r'^(---\s*\n)([\s\S]+?\n)(---\s*\n)([\s\S]*)', content)
    if not match:
        print(f"front matter not found, {file_path}")
        return None
    front_start, front_content, front_end, body = match.groups()

    # YAML解析（再ダンプなしでslug追加したいので、この時点でtags等は変更しない）
    metadata = yaml.safe_load(front_content)
    if not isinstance(metadata, dict):
        return None

    # title必須
    if 'title' not in metadata:
        print(f"title not found,{file_path}" )
        return None

    title = str(metadata['title']).strip().strip("'").strip('"')

    # 既にslugがある場合は何もしない
    if 'slug' in metadata:
        return {
            'title': metadata.get('title'),
            'slug': metadata.get('slug')
        }

    # slugを生成（tags等は変更せず、slug行のみ挿入）
    slug = generate_unique_slug(title)

    # front_contentを行単位で処理してslug行を追加
    lines = front_content.strip('\n').split('\n')
    # slug行をtitle行の後に追加する
    # title行を見つけたらその直後にslug行を挿入
    new_lines = []
    title_line_found = False
    for line in lines:
        new_lines.append(line)
        # title行は "title:" で始まる
        if re.match(r'^\s*title\s*:', line):
            title_line_found = True
            # title行直後にslug行挿入
            new_lines.append(f"slug: {slug}")

    # 再構築
    new_front_content = '\n'.join(new_lines) + '\n'
    new_content = front_start + new_front_content + front_end + body

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    return {
        'title': title,
        'slug': slug
    }

def main():
    target_dir = 'aozora'
    author_works = {}

    for root, dirs, files in os.walk(target_dir):
        rel_root = os.path.relpath(root, target_dir)
        if rel_root == '.':
            continue
        parts = rel_root.split(os.sep)
        author_name = parts[0]

        for file in files:
            if not file.endswith('.md'):
                continue
            # 作者自身のmarkdown（author_name.md）は一覧に追加しない
            if file == f"{author_name}.md":
                continue

            file_path = os.path.join(root, file)
            result = update_frontmatter(file_path)
            if result and result.get('title') and result.get('slug'):
                if author_name not in author_works:
                    author_works[author_name] = []
                author_works[author_name].append((result['title'], result['slug']))

    # 作者ごとにmarkdown生成
    for author, works in author_works.items():
        author_file = os.path.join(target_dir, author, f"{author}.md")
        
        # 作者名からslug生成
        author_slug = generate_unique_slug(author)

        # frontmatter作成（tags等は関与しない）
        author_frontmatter = f"""---\ntitle: {author}\nslug: {author_slug}\n---\n"""

        # 作品一覧
        lines = []
        lines.append(author_frontmatter)
        lines.append(f"# {author}の作品一覧\n")
        for w_title, w_slug in works:
            lines.append(f"- [{w_title}]({w_slug})")

        with open(author_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")

        print(f"作者ページ生成完了: {author_file}")

if __name__ == "__main__":
    main()
