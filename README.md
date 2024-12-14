# evame-data

## dataは下記仕様に従って作成する

### front matter

title,slugが必須

slugはaozorabunko.pyでtitleから生成する



tagsがない場合は空配列として扱う

### ディレクトリ構成

```
data/
├── aozorabunko/
│   ├── 著者名/
│   │   ├── 作品名.md
│   │   ├── 作品名.md
│   │   ├── 著者名.md
├── ├── aozorabunko-authors-list.md
```

のように､著者一覧ページと著者ページを作成する
著者ページは著者名のディレクトリに配置する
title､slugは必須


## まだできていない部分
1. 作品冒頭のauthorに著者ページへのリンクがない

2. slugが短すぎるものがある
3.tagsは配列で､NDC分類ならNDC918､DDC分類ならDDC918のように､分類規則によって接頭条件を付与する

ex:

```yaml
tags: ["NDC918", "DDC918"]
```