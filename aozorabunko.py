import os
import re
from unidecode import unidecode
from slugify import slugify
import yaml
import uuid
from typing import Optional, Dict,  List, Tuple, Union

def generate_unique_slug(title: str) -> str:
    """
    タイトルからslugを生成する。
    英数字以外を除去したうえで、ランダムな2文字のサフィックスを付与する。
    """
    temp_slug = slugify(unidecode(title))
    base_slug = re.sub(r'[^a-zA-Z0-9]', '', temp_slug)
    random_suffix = uuid.uuid4().hex[:2]
    unique_slug = f"{base_slug}{random_suffix}"
    return unique_slug

def extract_frontmatter(content: str) -> Optional[Tuple[str, str, str, str]]:
    """
    コンテンツからfrontmatter部分を抽出する。
    frontmatterが存在しない場合はNoneを返す。
    """
    match = re.match(r'^(---\s*\n)([\s\S]+?\n)(---\s*\n)([\s\S]*)', content)
    if not match:
        return None
    
    front_start, front_content, front_end, body = match.groups()
    # match.groups() は正規表現上、必ず4つのキャプチャを得る想定のため、
    # ここでNoneになり得ないことを保証できる。型チェッカーへは明示的に型を示すことも可能。
    assert front_start is not None
    assert front_content is not None
    assert front_end is not None
    assert body is not None
    return (front_start, front_content, front_end, body)

def insert_slug_line(front_content: str, slug: str) -> str:
    """
    既存のfrontmatter行群（front_content）にslug行を追加する。
    title行直後にslug行を挿入する。
    """
    lines = front_content.strip('\n').split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if re.match(r'^\s*title\s*:', line):
            new_lines.append(f"slug: {slug}")

    return '\n'.join(new_lines) + '\n'

def update_frontmatter(file_path: str) -> Union[Dict[str, str], str]:
    """
    単一ファイルに対してfrontmatterを更新または検証する。
    - frontmatterがない場合やtitleがない場合はファイルパス（str）を返す（失敗扱い）。
    - slugが無い場合は新規生成してfrontmatterに挿入。
    - 処理成功時は{'title': title, 'slug': slug}を返す。
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter_parts = extract_frontmatter(content)
    if frontmatter_parts is None:
        print(f"front matter not found, {file_path}")
        return file_path

    front_start, front_content, front_end, body = frontmatter_parts
    metadata = yaml.safe_load(front_content)
    if not isinstance(metadata, dict):
        print(f"metadata invalid, {file_path}")
        return file_path

    if 'title' not in metadata:
        print(f"title not found,{file_path}")
        return file_path

    title = str(metadata['title']).strip().strip("'").strip('"')
    if 'slug' in metadata:
        # slugが既にある場合は更新不要
        return {'title': title, 'slug': metadata['slug']}

    # slugがない場合生成
    slug = generate_unique_slug(title)
    new_front_content = insert_slug_line(front_content, slug)
    new_content = front_start + new_front_content + front_end + body

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    return {'title': title, 'slug': slug}

def process_markdown_files(target_dir: str) -> Tuple[Dict[str, List[Tuple[str, str]]], List[str]]:
    """
    指定ディレクトリ配下のマークダウンを走査し、frontmatterを整備する。
    成功した作品一覧を著者名ごとにまとめ、失敗ファイルはリストで返す。
    """
    author_works: Dict[str, List[Tuple[str, str]]] = {}
    failed_files: List[str] = []

    for root, dirs, files in os.walk(target_dir):
        rel_root = os.path.relpath(root, target_dir)
        if rel_root == '.':
            continue

        parts = rel_root.split(os.sep)
        author_name = parts[0]

        for file in files:
            if not file.endswith('.md'):
                continue
            # 著者自身のファイルはスキップ
            if file == f"{author_name}.md":
                continue

            file_path = os.path.join(root, file)
            result = update_frontmatter(file_path)

            if isinstance(result, dict) and result.get('title') and result.get('slug'):
                author_works.setdefault(author_name, []).append((result['title'], result['slug']))
            else:
                # 文字列の場合はエラー扱いで失敗リストに格納
                failed_files.append(str(result))

    return author_works, failed_files

def get_existing_author_slug(author_file: str) -> Optional[str]:
    """
    既存の著者ページファイルからslugを取得する。
    なければNoneを返す。
    """
    if not os.path.exists(author_file):
        return None
    with open(author_file, 'r', encoding='utf-8') as f:
        content = f.read()
    frontmatter_parts = extract_frontmatter(content)
    if frontmatter_parts is None:
        return None
    _, front_content, _, _ = frontmatter_parts
    metadata = yaml.safe_load(front_content)
    if not isinstance(metadata, dict):
        return None
    return metadata.get('slug')

def create_author_pages(target_dir: str, author_works: Dict[str, List[Tuple[str, str]]]) -> None:
    """
    著者ごとに作品一覧Markdownを生成する。
    """
    for author, works in author_works.items():
        author_file = os.path.join(target_dir, author, f"{author}.md")
        # 既存slug取得
        existing_slug = get_existing_author_slug(author_file)
        if existing_slug is None:
            # 新規生成
            author_slug = generate_unique_slug(author)
        else:
            author_slug = existing_slug

        # 作品をタイトル順でソート
        works.sort(key=lambda x: x[0])

        author_frontmatter = f"---\ntitle: {author}\nslug: {author_slug}\n---\n"
        lines = [author_frontmatter, f"## {author}の作品一覧\n"]
        for w_title, w_slug in works:
            lines.append(f"- [{w_title}]({w_slug})")

        with open(author_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")

        print(f"作者ページ生成完了: {author_file}")

def write_failed_files_list(failed_files: List[str], output_file: str) -> None:
    """
    処理失敗ファイルの一覧を出力ファイルに書き込む。
    """
    # 必ずファイルを生成するように変更
    with open(output_file, 'w', encoding='utf-8') as f:
        for ff in failed_files:
            f.write(ff + '\n')

    if failed_files:
        print(f"タイトルなし、frontmatterなし等で失敗したファイル一覧を {output_file} に出力しました。")
    else:
        print("失敗ファイルはありませんでした。空のfailed_files.txtを作成しました。")

def main():
    target_dir = 'aozorabunko'
    author_works, failed_files = process_markdown_files(target_dir)

    # 著者ページ生成
    create_author_pages(target_dir, author_works)

    # 失敗ファイル出力
    write_failed_files_list(failed_files, 'failed_files.txt')

if __name__ == "__main__":
    main()