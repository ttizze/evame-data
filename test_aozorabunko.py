import os
import pytest
from pathlib import Path
from aozorabunko import main

@pytest.fixture
def sample_dir(tmp_path: Path):
    # testディレクトリを作成
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # testディレクトリ配下にaozorabunkoを作る
    aozorabunko = test_dir / "aozorabunko"
    aozorabunko.mkdir()

    author_dir = aozorabunko / "NatsumeSoseki"
    author_dir.mkdir()
    
    # 成功パターン
    (author_dir / "wagahaiha_nekodearu.md").write_text(
        "---\n"
        "title: 吾輩は猫である\n"
        "author: 夏目漱石\n"
        "---\n\n"
        "本文開始\n"
    )

    # 失敗パターン(frontmatterなし)
    (author_dir / "no_front.md").write_text("frontmatterなしのファイル\n")

    # authorなし
    (author_dir / "no_author.md").write_text(
        "---\n"
        "title: 坊っちゃん\n"
        "---\n\n"
        "本文\n"
    )

    # titleなし
    (author_dir / "no_title.md").write_text(
        "---\n"
        "author: 夏目漱石\n"
        "---\n\n"
        "本文\n"
    )

    # すでに## author:がある場合
    (author_dir / "already_author.md").write_text(
        "---\n"
        "title: こころ\n"
        "author: 夏目漱石\n"
        "---\n\n"
        "## author: 夏目漱石\n"
        "本文\n"
    )

    return test_dir  # testディレクトリのパスを返す

def test_main_function(sample_dir: Path):
    # testディレクトリに移動
    os.chdir(sample_dir.parent)  # testがあるディレクトリへ移動
    
    # main関数をtestディレクトリで実行
    main(str(sample_dir / "aozorabunko"))

    # 成功ファイルチェック
    success_file = sample_dir / "aozorabunko" / "NatsumeSoseki" / "wagahaiha_nekodearu.md"
    content = success_file.read_text()
    assert "slug:" in content, "slugが挿入されているはず"
    assert "## author: 夏目漱石" in content, "author行が挿入されているはず"

    # 既にauthorがある場合
    already_author_file = sample_dir / "aozorabunko" / "NatsumeSoseki" / "already_author.md"
    already_author_content = already_author_file.read_text()
    assert already_author_content.count("## author:") == 1, "author行は重複挿入されないこと"

    # 失敗ファイル確認
    failed_list = (sample_dir.parent / "failed_files.txt")
    failed_content = failed_list.read_text().strip().split("\n")
    assert str(sample_dir / "aozorabunko" / "NatsumeSoseki" / "no_front.md") in failed_content
    assert str(sample_dir / "aozorabunko" / "NatsumeSoseki" / "no_author.md") in failed_content
    assert str(sample_dir / "aozorabunko" / "NatsumeSoseki" / "no_title.md") in failed_content

    # 著者ページチェック
    author_page = sample_dir / "aozorabunko" / "NatsumeSoseki" / "NatsumeSoseki.md"
    assert author_page.exists()
    author_page_content = author_page.read_text()
    assert "## NatsumeSosekiの作品一覧" in author_page_content
    assert "slug" in author_page_content

    # 著者一覧ページチェック
    # authors.mdはaozorabunkoディレクトリに作成されるはず
    authors_list = sample_dir / "aozorabunko" / "authors.md"
    assert authors_list.exists()
    authors_list_content = authors_list.read_text()
    assert "[NatsumeSoseki]" in authors_list_content
