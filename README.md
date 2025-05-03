# nhkgogaku
らじる★らじるから配信データをダウンロード


## 環境変数
NHK_DOWNLOAD_DIR                  -- データをダウンロードするフォルダ。番組名年度でフォルダが作られ、その中に音声データが格納される。  
NHK_FFMPEG_BIN                    -- ffmpegの実行コマンド。  
NHK_OUTPUT_AUDIO_FORMAT_EXTENTION -- 作成する音声データのフォーマット拡張子。m4a(デフォルト)か、mp3。  
NHK_GOGAKU_CORNERS_URL            -- NHKらじる★らじるの番組リストを配信しているJSON URL。(DEFAULT: https://www.nhk.or.jp/radio-api/app/v1/web/ondemand/corners/new_arrivals)  
NHK_GOGAKU_SERIES_URL_FORMAT      -- NHKらじる★らじるの番組JSON URLのフォーマット情報。番組情報と配信中の音声データ情報が提供されている。(DEFAULT: https://www.nhk.or.jp/radio-api/app/v1/web/ondemand/series?site_id={series_site_id}&corner_site_id={corner_site_id})  


## Docker実行
/var/task/downloadにオーディオフォルダを割り当てて実行  
docker run --rm -v ~/NHK語学講座:/var/task/download  -it nhkgogaku:1.6

## 謝辞
[SimpleLife](https://simplelife.pgw.jp)さんの[NHKラジオ語学講座のストリーミングデータをMP3形式で自動ダウンロードする(JSONフォーマット対応版)](https://simplelife.pgw.jp/it/nhk_radio_gogaku_kouza_json/)の内容を参考に開発させていただきました。  
感謝いたします。
