import os
import urllib.request
import subprocess
import datetime
from os.path import expanduser
import sys
import json
import unicodedata
# import boto3
import platform
from dataclasses import dataclass

"""
Envs:
  NHK_DOWNLOAD_DIR                  -- データをダウンロードするフォルダ。番組名年度でフォルダが作られ、その中に音声データが格納される。
  NHK_FFMPEG_BIN                    -- ffmpegの実行コマンド。
  NHK_OUTPUT_AUDIO_FORMAT_EXTENTION -- 作成する音声データのフォーマット拡張子。m4a(デフォルト)か、mp3。
  NHK_GOGAKU_CORNERS_URL            -- NHKらじる★らじるの番組リストを配信しているURL。JSONで提供されている。
"""

@dataclass
class NhkRadioProgram:
    id_keyword :str                 #各語学講座のseries/corner ID取得キーワード
    program_name :str               #講座名
    file_size_check_standard :int   #ダウンロード完了済みかどうかをチェックするファイルサイズの基準値
    remove_program_word :str        #MP3タイトルタグから消去するプレフィックス文字列
    filter :str                     #ダウンロード対象にしない配信のキーワード
    series_site_id :str             #(定義ファイルに気記載するのではなく、後でNHKの番組情報から読み取って代入する)
    corner_site_id :str             #(定義ファイルに気記載するのではなく、後でNHKの番組情報から読み取って代入する)
    thumbnail_url :str              #(定義ファイルに気記載するのではなく、後でNHKの番組情報から読み取って代入する)

    def url(self)->str:
        return 'https://www.nhk.or.jp/radio-api/app/v1/web/ondemand/series?site_id='+self.series_site_id+'&corner_site_id='+self.corner_site_id #配信データのURLを作成し、データに保存

def decodeNhkRadioProgram(data :dict) -> NhkRadioProgram:
    program = NhkRadioProgram(id_keyword=data['id_keyword']
                              , program_name=data['program_name']
                              , file_size_check_standard=data['file_size_check_standard']
                              , remove_program_word=data['remove_program_word']
                              , filter=data['filter']
                              , series_site_id=None
                              , corner_site_id=None
                              , thumbnail_url=None)
    return program

@dataclass
class ApplicationSettings:
    def __init__(self) :
        self.download_dir=os.environ.get("NHK_DOWNLOAD_DIR","./download")
        self.ffmpeg_bin=os.environ.get("NHK_FFMPEG_BIN","ffmpeg")
        self._FORMAT_EXTENTION="." + os.environ.get("NHK_OUTPUT_AUDIO_FORMAT_EXTENTION","m4a")    #拡張子の.をつけて変数格納する
        self._NHK_GOGAKU_CORNERS_URL=os.environ.get("NHK_GOGAKU_CORNERS_URL","https://www.nhk.or.jp/radio-api/app/v1/web/ondemand/corners/new_arrivals")

        radio_program = os.path.join(self.download_dir,"radio_program.json")
        with open(radio_program,'r',encoding="utf-8") as f:
            self.programs :list[NhkRadioProgram] = json.load(f, object_hook=decodeNhkRadioProgram)

# @dataclass
# class ProgramSettings:
#     #各語学講座のseries/corner ID取得キーワード、講座名、ダウンロード完了済みかどうかをチェックするファイルサイズ、MP3タイトルタグから消去するプレフィックス文字列を定義する
#     id_keyword :str                 #各語学講座のseries/corner ID取得キーワード
#     program_name :str               #講座名
#     file_size_check_standard :int   #ダウンロード完了済みかどうかをチェックするファイルサイズの基準値
#     remove_program_word :str        #MP3タイトルタグから消去するプレフィックス文字列
#     filter :str                     #ダウンロード対象にしない配信のキーワード
#     url :str                        #配信データのURL



def download():
    # 設定情報
    applicationSettings = ApplicationSettings()

    # ダウンロード先のフォルダがない場合はフォルダを作成する
    os.makedirs(applicationSettings.download_dir, exist_ok=True)
    #各語学講座のseries_site_idとcorner_site_idが記載されているJSONからIDを取得し、各講座のJSONファイルのダウンロードURLを生成する
    series_corner_id_json = os.path.join(applicationSettings.download_dir, "series_corner_id.json")
    urllib.request.urlretrieve(applicationSettings._NHK_GOGAKU_CORNERS_URL, series_corner_id_json)
    with open(series_corner_id_json,'r',encoding="utf-8") as f:
        series_corner_ids = json.load(f)
    os.remove(series_corner_id_json)
    for series_corner_id in series_corner_ids['corners']:
        for program in applicationSettings.programs:
            if series_corner_id['title']==program.id_keyword :
                program.series_site_id = series_corner_id['series_site_id']
                program.corner_site_id = series_corner_id['corner_site_id']
                program.thumbnail_url =  series_corner_id['thumbnail_url']      #TODO: 番組サムネイルを番組フォルダに保存する
                break   #TODO: 現在の作りだと、1番組複数コーナーがあった場合、最初のものしか有効にならない(ラジオ深夜便はコーナーが放送日(曜日?)で別々に設定されている)
    #各語学講座のストリーミングデータをダウンロードする
    for program in applicationSettings.programs:
        # JSONコンテンツを読み出す
        bangumi_json = os.path.join(applicationSettings.download_dir, "bangumi.json")
        urllib.request.urlretrieve(program.url(), bangumi_json)
        with open(bangumi_json,'r',encoding="utf-8") as f:
            json_dict = json.load(f)
        os.remove(bangumi_json)
        # ダウンロードしたファイルパスを保持する変数を初期化する
        last_download_path_only_date=""
        # 各LessonのストリーミングデータをMP3に変換してダウンロードする
        for json_element in json_dict['episodes']:
            #放送年月日を取得する
            datetime_string=json_element['aa_contents_id'].split(";")[3]
            month=int(datetime_string[4:6])
            day=int(datetime_string[6:8])
            year=int(datetime_string[0:4])
            if month<4:
                nendo=year-1
            else:
                nendo=year
            contents=json_element['aa_contents_id'].split(";")[1]
            # print(f"year:{year} / month:{month} / day:{day} / content:{contents}")
            #フィルタが定義されており、かつfile_titleがフィルタと一致しない場合はスキップする
            if program.filter!='' and contents.find(program.filter) != 0:
                continue
            # MP3に埋め込むタグ情報をセットする
            content=unicodedata.normalize('NFKC', contents).replace(program.remove_program_word, '').replace('\u3000',' ')  #\u3000は全角スペース
            tag_title="{0}年{1}月{2}日放送分「{3}」".format(year,str(month).zfill(2),str(day).zfill(2),content).replace('「「','「').replace('」」','」')
            tag_year=nendo
            tag_date="{0}{1}".format(str(month).zfill(2),str(day).zfill(2))
            tag_album=program.program_name+"["+str(nendo)+"年度]"
            # tag_date="{0}-{1}-{2}".format(year,str(month).zfill(2),str(day).zfill(2))
            #print(f"tag_title:{tag_title} / tag_year:{tag_year} / tag_album:{tag_album}")

            # MP3のダウンロードパスをセットする TODO:パスのデリみた処理を改善
            download_subdir=os.path.join(applicationSettings.download_dir, program.program_name+"["+str(nendo)+"年度]")
            os.makedirs(download_subdir, exist_ok=True)
            download_filename="{0}年{1}月{2}日放送分".format(year,str(month).zfill(2),str(day).zfill(2))+" "+program.program_name
            download_path=os.path.join(download_subdir, download_filename+applicationSettings._FORMAT_EXTENTION)
            # 同日に放送された番組は特別番組と判断してダウンロードファイルのファイル名にコンテンツ名を付与する
            if download_path == last_download_path_only_date :
                # download_filename=kouza+" "+"{0}年{1}月{2}日放送分".format(year,str(month).zfill(2),str(day).zfill(2))
                download_path=os.path.join(download_subdir, download_filename+"_"+content+applicationSettings._FORMAT_EXTENTION)
            else:
                last_download_path_only_date = download_path
            download_tmp_path=download_path+".downloading"
            #print(f"download_path:{download_path}")
            # ストリーミングファイルのURLをセットする
            download_url=json_element['stream_url']
            #print(f"download_url:{download_url}")
            # ffmpegのダウンロード処理用コマンドラインを生成する
            command_line=ffmpegCommandM4a(applicationSettings.ffmpeg_bin, download_url, tag_title, tag_album, tag_year, tag_date, download_tmp_path)
            # ダウンロード処理を実行する
            downloadCore(command_line,download_path, download_tmp_path, datetime.datetime.fromisoformat(json_element['aa_contents_id'].split(";")[4][0:25]), download_filename, program.file_size_check_standard)

def ffmpegCommandMp3(ffmpeg_bin :str, download_url :str, tag_title :str, tag_album :str, tag_year :str, tag_date :str, download_tmp_path :str) ->str:
    command_line=f"{ffmpeg_bin}" \
                f" -http_seekable 0" \
                f" -i {download_url}" \
                f" -id3v2_version 3" \
                f" -metadata artist=\"NHK\" -metadata title=\"{tag_title}\"" \
                f" -metadata album=\"{tag_album}\" -metadata date=\"{tag_year}\"" \
                f" -metadata TDAT={tag_date}" \
                f" -ar 44100 -ab 64k -c:a mp3" \
                f" -f mp3" \
                f" \"{download_tmp_path}\""
    return command_line

def ffmpegCommandM4a(ffmpeg_bin :str, download_url :str, tag_title :str, tag_album :str, tag_year :str, tag_date :str, download_tmp_path :str) ->str:
    command_line=f"{ffmpeg_bin}" \
                f" -http_seekable 0" \
                f" -i {download_url}" \
                f" -id3v2_version 3" \
                f" -metadata artist=\"NHK\" -metadata title=\"{tag_title}\"" \
                f" -metadata album=\"{tag_album}\" -metadata date=\"{tag_year}\"" \
                f" -metadata TDAT={tag_date}" \
                f" -vn -acodec copy" \
                f" -f ipod" \
                f" \"{download_tmp_path}\""
    return command_line

def downloadCore(command_line :str, download_path :str, download_tmp_path :str, programDate :datetime, download_filename :str, size :int):
    # ダウンロード済みファイルがある場合はダウンロードしない(ファイルサイズチェックする)
    if( os.path.isfile(download_path) and size<os.path.getsize(download_path)):
        print(" - - - -  SKIP: " + download_filename + " - - - -")
        return

    # tmpダウンロードファイルが残っている場合は削除する
    if( os.path.isfile(download_tmp_path)):
        os.remove(download_tmp_path)

    # ダウンロードファイルが残っている場合は削除する
    if( os.path.isfile(download_path)):
        os.remove(download_path)

    # ダウンロード処理実行
    print(command_line)
    subprocess.run(command_line,shell=True)
    # ファイルの作成日更新日を放送日に変更する
    if sys.platform=='darwin': #Mac
        os.utime(download_tmp_path, (programDate.timestamp(), programDate.timestamp()))     #ファイル作成日を更新日より過去日にできない?一度ファイル作成日と更新日を合わせて放送日時で設定する←Docker on Mac(ファイル作成日時、ファイル更新日時)。Linux(ファイル変更日時、最終アクセス日時)
        os.utime(download_tmp_path, (programDate.timestamp(), datetime.datetime.now().timestamp()))
    elif sys.platform=='linux' and platform.machine()=='aarch64': #LinuxLinux(raspberry pi)
        os.utime(download_tmp_path, (programDate.timestamp(), programDate.timestamp()))
    else:
        os.utime(download_tmp_path, (programDate.timestamp(), programDate.timestamp()))

    os.rename(download_tmp_path, download_path)

def main():
    # ログを出力する
    print('main')
    printSystemInfo()
    download()

# def handler(event, context):
#     print('Docker handler')
#     printSystemInfo()
#     print(f'boto3 version: {boto3.__version__}')
#     # print(f'botocore version: {botocore.__version__}')
#     download()
#     return 'Hello from AWS Lambda using Python' + sys.version + '!'

def printSystemInfo():
    print('OS:' + sys.platform)
    print('Version:' + sys.version)
    print('Platform.Machne:' + platform.machine())
    print('Platform.platform:' + platform.platform())

if __name__ == "__main__":
    main()
    