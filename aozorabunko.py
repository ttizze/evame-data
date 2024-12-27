import os
import re
from unidecode import unidecode
from slugify import slugify
import yaml
import uuid
from typing import Optional, Dict, List, Tuple, Union

SLUG_PATTERN = r'^[a-zA-Z0-9]{6,15}-[a-zA-Z0-9]{3}$'

def generate_unique_slug(title: str) -> str:
    """
    タイトルからslugを生成する。
    英数字以外を除去したうえで、6-15文字に調整し、
    ランダムな3文字のサフィックスをハイフン付きで付与する。
    """
    temp_slug = slugify(unidecode(title))
    base_slug = re.sub(r"[^a-zA-Z0-9]", "", temp_slug)

    # 6文字以上15文字以下に調整
    if len(base_slug) < 6:
        # 6文字未満の場合は、最後の文字を繰り返して6文字にする
        last_char = base_slug[-1] if base_slug else 'x'
        base_slug = base_slug + last_char * (6 - len(base_slug))
    elif len(base_slug) > 15:
        # 15文字を超える場合は切り詰める
        base_slug = base_slug[:15]

    random_suffix = uuid.uuid4().hex[:3]  # 3文字のサフィックス
    unique_slug = f"{base_slug}-{random_suffix}"  # ハイフン追加
    return unique_slug


def extract_frontmatter(content: str) -> Optional[Tuple[str, str, str, str]]:
    """
    コンテンツからfrontmatter部分を抽出する。
    frontmatterが存在しない場合はNoneを返す。
    """
    match = re.match(r"^(---\s*\n)([\s\S]+?\n)(---\s*\n)([\s\S]*)", content)
    if not match:
        return None

    front_start, front_content, front_end, body = match.groups()
    assert front_start is not None
    assert front_content is not None
    assert front_end is not None
    assert body is not None
    return (front_start, front_content, front_end, body)


def insert_slug_line(front_content: str, slug: str) -> str:
    """
    既存のfrontmatter行群（front_content）のslug行を更新する。
    既存のslugがある場合は置換し、ない場合はtitle行直後に挿入する。
    slugは必ず1つだけになるように制御する。
    """
    lines = front_content.strip("\n").split("\n")
    new_lines = []
    slug_added = False

    for line in lines:
        if re.match(r"^\s*slug\s*:", line):
            if not slug_added:  # 最初のslug行のみ更新
                new_lines.append(f"slug: {slug}")
                slug_added = True
            # 2つ目以降のslug行は無視（追加しない）
        else:
            new_lines.append(line)
            # title行の直後かつまだslugが追加されていない場合
            if not slug_added and re.match(r"^\s*title\s*:", line):
                new_lines.append(f"slug: {slug}")
                slug_added = True

    return "\n".join(new_lines) + "\n"


def update_frontmatter(file_path: str) -> Union[Dict[str, str], str]:
    with open(file_path, "r", encoding="utf-8") as f:
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

    if "title" not in metadata:
        print(f"title not found,{file_path}")
        return file_path

    if "author" not in metadata:
        print(f"author not found,{file_path}")
        return file_path

    # 既存のslugをチェック
    existing_slug = metadata.get("slug", "")

    # slugが存在しないか、無効な形式の場合のみ新しいslugを生成
    if not existing_slug or not re.match(SLUG_PATTERN, existing_slug):
        author_name = str(metadata["author"]).strip().strip("'").strip('"')
        title = str(metadata["title"]).strip().strip("'").strip('"')
        new_slug = generate_unique_slug(title)
        new_front_content = insert_slug_line(front_content, new_slug)

        if "## author:" not in body:
            author_line = f"## author: {author_name}\n\n"
        else:
            author_line = ""

        new_content = front_start + new_front_content + front_end + author_line + body

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {"title": metadata["title"], "slug": new_slug}

    return {"title": metadata["title"], "slug": existing_slug}


def process_markdown_files(
    target_dir: str,
) -> Tuple[Dict[str, List[Tuple[str, str]]], List[str]]:
    """
    指定ディレクトリ配下のマークダウンを走査し、frontmatterを整備する。
    成功した作品一覧を著者名ごとにまとめ、失敗ファイルはリストで返す。
    """
    author_works: Dict[str, List[Tuple[str, str]]] = {}
    failed_files: List[str] = []

    for root, dirs, files in os.walk(target_dir):
        rel_root = os.path.relpath(root, target_dir)
        if rel_root == ".":
            continue

        parts = rel_root.split(os.sep)
        author_name = parts[0]

        for file in files:
            if not file.endswith(".md"):
                continue
            # 著者自身のファイルはスキップ
            if file == f"{author_name}.md":
                continue

            file_path = os.path.join(root, file)
            result = update_frontmatter(file_path)

            if isinstance(result, dict) and result.get("title") and result.get("slug"):
                author_works.setdefault(author_name, []).append(
                    (result["title"], result["slug"])
                )
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
    with open(author_file, "r", encoding="utf-8") as f:
        content = f.read()
    frontmatter_parts = extract_frontmatter(content)
    if frontmatter_parts is None:
        return None
    _, front_content, _, _ = frontmatter_parts
    metadata = yaml.safe_load(front_content)
    if not isinstance(metadata, dict):
        return None
    return metadata.get("slug")


def create_author_pages(
    target_dir: str, author_works: Dict[str, List[Tuple[str, str]]]
) -> Dict[str, str]:
    """
    著者ごとに作品一覧Markdownを生成し、{著者: slug} のマッピングを返す。
    """
    author_slug_map = {}
    for author, works in author_works.items():
        author_file = os.path.join(target_dir, author, f"{author}.md")
        existing_slug = get_existing_author_slug(author_file)
        if existing_slug is None:
            author_slug = generate_unique_slug(author)
        else:
            author_slug = existing_slug

        works.sort(key=lambda x: x[0])

        author_frontmatter = f"---\ntitle: {author}\nslug: {author_slug}\n---\n"
        lines = [author_frontmatter, f"## {author}の作品一覧\n"]
        for w_title, w_slug in works:
            lines.append(f"- [{w_title}]({w_slug})")

        with open(author_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        author_slug_map[author] = author_slug
        print(f"作者ページ生成完了: {author_file}")

    return author_slug_map


def create_authors_list_page(
    target_dir: str,
    author_works: Dict[str, List[Tuple[str, str]]],
    author_slug_map: Dict[str, str],
) -> None:
    """
    全著者の一覧ページauthors.mdを作成する。
    著者名でソートして表示し、各著者ページへのリンクをslugで張る。
    """
    all_authors = list(author_works.keys())
    all_authors.sort()

    # authors.mdを作成
    # slugはそれぞれのauthorごとにauthor_slug_mapから取得してリンクを張る
    frontmatter = "---\ntitle: 青空文庫著者一覧\nslug: aozorabunko-authors-list\n---\n\n"
    lines = [frontmatter, "## 青空文庫著者一覧\n"]
    for author in all_authors:
        author_slug = author_slug_map.get(author, "")
        # 著者ページへのリンク: slug利用
        # slugのみがURLになる想定（静的サイト生成ツールなどを想定）
        # 必要に応じて prefix や相対パスを調整
        lines.append(f"- [{author}]({author_slug})")

    authors_list_file = os.path.join(target_dir, "authors.md")
    with open(authors_list_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"著者一覧ページ生成完了: {authors_list_file}")


def write_failed_files_list(failed_files: List[str], output_file: str) -> None:
    """
    処理失敗ファイルの一覧を出力ファイルに書き込む。
    """
    with open(output_file, "w", encoding="utf-8") as f:
        for ff in failed_files:
            f.write(ff + "\n")

    if failed_files:
        print(
            f"タイトルなし、frontmatterなし、authorなし等で失敗したファイル一覧を {output_file} に出力しました。"
        )
    else:
        print("失敗ファイルはありませんでした。空のfailed_files.txtを作成しました。")


def main(target_dir: str = "aozorabunko"):
    author_works, failed_files = process_markdown_files(target_dir)

    # 著者ページ生成
    author_slug_map = create_author_pages(target_dir, author_works)

    # 著者一覧ページ生成
    create_authors_list_page(target_dir, author_works, author_slug_map)

    # 失敗ファイル出力
    write_failed_files_list(failed_files, "failed_files.txt")


if __name__ == "__main__":
    main()
