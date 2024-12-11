import os
import re
from unidecode import unidecode
from slugify import slugify
import yaml
import uuid

def generate_unique_slug(title):
    temp_slug = slugify(unidecode(title))
    base_slug = re.sub(r'[^a-zA-Z0-9]', '', temp_slug)
    random_suffix = uuid.uuid4().hex[:2]
    unique_slug = f"{base_slug}{random_suffix}"
    return unique_slug

def update_frontmatter(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.match(r'^(---\s*\n)([\s\S]+?\n)(---\s*\n)([\s\S]*)', content)
    if not match:
        # frontmatterがない場合
        print(f"front matter not found, {file_path}")
        return file_path  # 失敗ファイルとして返す
    front_start, front_content, front_end, body = match.groups()

    metadata = yaml.safe_load(front_content)
    if not isinstance(metadata, dict):
        # メタデータが辞書でない場合失敗扱い
        print(f"metadata invalid, {file_path}")
        return file_path

    if 'title' not in metadata:
        print(f"title not found,{file_path}")
        return file_path

    title = str(metadata['title']).strip().strip("'").strip('"')
    if 'slug' in metadata:
        # 既にslugがある場合はOK
        return {
            'title': metadata.get('title'),
            'slug': metadata.get('slug')
        }

    slug = generate_unique_slug(title)
    lines = front_content.strip('\n').split('\n')
    new_lines = []
    title_line_found = False
    for line in lines:
        new_lines.append(line)
        if re.match(r'^\s*title\s*:', line):
            title_line_found = True
            new_lines.append(f"slug: {slug}")

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
    target_dir = 'aozorabunko'
    author_works = {}
    failed_files = []

    for root, dirs, files in os.walk(target_dir):
        rel_root = os.path.relpath(root, target_dir)
        if rel_root == '.':
            continue
        parts = rel_root.split(os.sep)
        author_name = parts[0]

        for file in files:
            if not file.endswith('.md'):
                continue
            if file == f"{author_name}.md":
                continue
            file_path = os.path.join(root, file)
            result = update_frontmatter(file_path)

            if isinstance(result, dict) and result.get('title') and result.get('slug'):
                if author_name not in author_works:
                    author_works[author_name] = []
                author_works[author_name].append((result['title'], result['slug']))
            elif isinstance(result, str):
                # 文字列の場合は失敗ファイルとみなす
                failed_files.append(result)

    for author, works in author_works.items():
        author_file = os.path.join(target_dir, author, f"{author}.md")
        author_slug = generate_unique_slug(author)
        author_frontmatter = f"""---\ntitle: {author}\nslug: {author_slug}\n---\n"""
        lines = [author_frontmatter, f"# {author}の作品一覧\n"]
        for w_title, w_slug in works:
            lines.append(f"- [{w_title}]({w_slug})")
        with open(author_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")
        print(f"作者ページ生成完了: {author_file}")

    # 失敗ファイル出力
    if failed_files:
        with open('failed_files.txt', 'w', encoding='utf-8') as f:
            for ff in failed_files:
                f.write(ff + '\n')
        print("タイトルなし、frontmatterなし等で失敗したファイル一覧を failed_files.txt に出力しました。")

if __name__ == "__main__":
    main()