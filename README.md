# JMA-AMeDAS
## What
<a href="http://www.data.jma.go.jp/obd/stats/etrn/index.php?prec_no=&block_no=&year=&month=&day=&view=">気象庁</a>よりAMeDASデータを取得


## How to use
- メインファイルは./downloader.py
- コマンドライン引数に都道府県名を取ることでデータ取得対象を指定可能。何も指定しない場合は全データを取得。
- ./make_prefectures.pyで県名とIDを紐づける./settings/prefectures.jsonを生成


## Environment
- requests
- beautifulsoup

## structure
### ./data
- 各都道府県ごとにIDを名前にしてディレクトリを作成。都道府県名とIDの対応は./settings/prefectures.json。
- 各都市のIDを名前にしてcsvファイルで保存。名前とIDの対応は./data/<県ID>/place_dic.jsonとして保存。
### ./settings
- prefectures.jsonで都道府県名とIDを管理。新たに追加する場合は気象庁のサイトよりIDを調べて追記する。
- columns.jsonでカラム名を日本語と英語で管理。名前の変更は自由。順番を変更する、要素を増やす場合はdownloader.pyのget_rowDataをいじる必要がある。
- weather.jsonで天気の日本語名と英語名を管理。## Exceptionに出た天気を追記可能。ここに存在しない天気は日本語名で保存。


## Exception
- 東西南北、静穏以外の風向データはNoneとして扱い、最後にまとめて表示する。
- ./settings/weather.jsonに存在しない天気がデータに含まれるとき最後にまとめて表示する。データは日本語のまま保存。


## References
https://qiita.com/Cyber_Hacnosuke/items/122cec35d299c4d01f10
