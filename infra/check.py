import fnmatch
from functools import reduce
import glob
from itertools import groupby
from operator import attrgetter
import os
from pathlib import Path
import re

import boto3
from django.conf import settings
from django.db import IntegrityError
from django.shortcuts import render
import ezdxf
from markupsafe import Markup
import urllib
from infra.models import Article, BridgePicture, FullReportData, Infra, NameEntry, Table

def bridge_table(request, article_pk, pk): # idの紐付け infra/bridge_table.htmlに表示
    context = {}
    # プロジェクトのメディアディレクトリからdxfファイルまでの相対パス
    # URL：article/<int:article_pk>/infra/<int:pk>/bridge-table/

    # 指定したInfraに紐づく Tableを取り出す
    article = Article.objects.filter(id=article_pk).first()
    infra = Infra.objects.filter(id=pk).first()
    table = Table.objects.filter(infra=pk).first()
    # << 案件名とファイル名を連結してdxfファイルのURLを取得する >>
    # AWSクライアントを作成
    s3 = boto3.client('s3')

    def match_s3_objects_with_prefix(bucket_name, prefix, pattern):
        # プレフィックス(特定のフォルダ)を指定して、オブジェクトをリスト
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        if 'Contents' not in response:
            return []

        # パターンに基づいてオブジェクトをフィルタリング
        matched_keys = [obj['Key'] for obj in response['Contents'] if fnmatch.fnmatch(obj['Key'], pattern)]

        return matched_keys
    
    bucket_name = 'infraprotect'
    folder_name = article.案件名+"/"
    pattern = f'*{infra.title}*/{infra.title}.dxf'

    # 該当するオブジェクトを取得
    matched_objects = match_s3_objects_with_prefix(bucket_name, folder_name, pattern)

    if matched_objects:
        print(f"該当オブジェクト：{matched_objects}")
    else:
        print("ファイルが見つかりません")

    # 結果を表示
    for obj_key in matched_objects:
        dxf_filename = f"https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{obj_key}"
    
    encode_dxf_filename = urllib.parse.quote(dxf_filename, safe='/:') # スラッシュとコロン以外をエンコード
    dxf_filename = encode_dxf_filename

    print(f"dxfファイルの絶対URLは：{dxf_filename}")
    print(f"dxfファイル（エンコード）の絶対URLは：{encode_dxf_filename}")

    second_search_title_text = "損傷図"

    # << 辞書型として、全径間を1つの多重リストに格納 >>
    max_search_title_text = infra.径間数
    print(f"最大径間数：{max_search_title_text}")
    database_sorted_items = []  # 結果をまとめるリスト
    
    for search_title_text_with_suffix in range(1, max_search_title_text + 1):
        search_title_text = f"{search_title_text_with_suffix}径間"
        print("dxfファイル名")
        print(dxf_filename)
        print(encode_dxf_filename)
        print(search_title_text)
        print("ここまではOK") #                                                              1径間              損傷図
        sub_database_sorted_items = create_picturelist(request, table, dxf_filename, search_title_text, second_search_title_text)
        for item in sub_database_sorted_items:
            item['search'] = search_title_text
            database_sorted_items.append(item)
    # print(f"database_sorted_items:{database_sorted_items}")
    """辞書型の多重リストをデータベースに登録"""
    # << ['']を外してフラットにする >>
    def flatten(value):
        def _flatten(nested_list):
            if isinstance(nested_list, list):
                for item in nested_list:
                    yield from _flatten(item)
            else:
                yield nested_list
        
        return ', '.join(_flatten(value))

    # << joinキーを変換 >>
    def join_to_result_string(join):
        result_parts = []
        for item in join:
            parts_name = item['parts_name'][0]
            damage_names = item['damage_name']
            formatted_damage_names = '/'.join(damage_names)
            result_parts.append(f"{parts_name} : {formatted_damage_names}")
        return ', '.join(result_parts)

    # << 写真のキーを変換 >>
    def simple_flatten(value):
        return ', '.join(map(str, value)) if isinstance(value, list) else value
    
    # <<正規表現で4桁以上の番号を取得>>
    def extract_number(text):
        pattern = r'\d{4,}' # 4文字以上の連続する数字
        matches = re.findall(pattern, text)
        return matches
    
    picture_counter = 1
    index_counter = 0
    picture_number_box = []
    for damage_data in database_sorted_items:
        # 元の辞書から 'picture_number' の値を取得
        #             　辞書型 ↓           ↓ キーの名前      ↓ 存在しない場合、デフォルト値として空白を返す
        picture_number = damage_data.get('picture_number', '')
        # 正規表現で数字のみを抽出
        if picture_number:
            # 数字のみを抽出
            before_numbers_only = re.findall(r'\d+', str(picture_number)) # ['2']  ['2','3']
            print(f"リスト型番号:{before_numbers_only}")
            print(f"{index_counter}  どっちが大きい　{len(before_numbers_only)}")
            # before_numbers_onlyの各元素で別の処理を行う場合
            # カウンターに基づいて処理を行う
            if index_counter == 0:
                picture_number_box = []
            if len(before_numbers_only) > 1:
                for number in before_numbers_only:
                    print(f"{index_counter}番目の要素: {number}")
                    picture_number_box.append(number)
                    index_counter += 1
                index_counter = 0
                print(picture_number_box)
            else:
                picture_number_box = []
                index_counter = 0
                numbers_only = before_numbers_only[index_counter]  # カウンターに対応する数字を取得
                print(f"オンリーナンバーズ（抽出後）: {numbers_only}")
                picture_number_box.append(numbers_only)
        else:
            numbers_only = None

        damage_coordinate = damage_data.get('damage_coordinate', [None, None])
        damage_coordinate_x = damage_coordinate[0] if damage_coordinate else None
        damage_coordinate_y = damage_coordinate[1] if damage_coordinate else None

        picture_coordinate = damage_data.get('picture_coordinate', [None, None])
        picture_coordinate_x = picture_coordinate[0] if picture_coordinate else None
        picture_coordinate_y = picture_coordinate[1] if picture_coordinate else None

        #parts_list = flatten(damage_data.get('parts_name', ''))
        #damage_list = flatten(damage_data.get('damage_name', ''))

        names = damage_data.get('parts_name', '')
        damages = damage_data.get('damage_name', '')
        #print(f"names:{names}")
        #print(f"damages:{damages}")
        
        split_names = []

        for item in names:
            split_items = []
            for split in item:
                if "～" in split:
                    one = split.find("～")
                    start_number = ''.join(extract_number(split[:one])) # 0101
                    end_number = ''.join(extract_number(split[one+1:])) # 0204

                    # 最初の2桁と最後の2桁を取得
                    start_prefix = start_number[:2] # 01
                    start_suffix = start_number[2:] # 01
                    end_prefix = end_number[:2] # 01
                    end_suffix = end_number[2:] # 03
                    
                    part_name = split[:one].replace(start_number, '')
                
                    for prefix in range(int(start_prefix), int(end_prefix)+1):
                        for suffix in range(int(start_suffix), int(end_suffix)+1):
                            number_items = "{:02d}{:02d}".format(prefix, suffix)
                            split_items.append(part_name + number_items)
                else:
                    split_items.append(split)
            split_names.append(split_items)
        
        join = join_to_result_string(damage_data.get('join', ''))
        this_time_picture = simple_flatten(damage_data.get('this_time_picture', ''))
        last_time_picture = simple_flatten(damage_data.get('last_time_picture', ''))
        textarea_content = damage_data.get('textarea_content', '')
        span_number = damage_data.get('search', '')
        print("----------------------------------")
        print(f"damage_data:{damage_data}")
        print(f"join:{join}")
        print(f"this_time_picture:{this_time_picture}")
        name_length = len(split_names)
        damage_length = len(damages)
        
        # 多重リストかどうかを判定する関数
        def is_multi_list(lst):
            return any(isinstance(i, list) for i in lst)
        
        def process_names(names):
            """
            与えられたnamesを処理し、適切な部分を返す関数
            所見用にparts_splitに格納
            """
            
            parts_left = ["主桁", "PC定着部"]  # 左の数字
            parts_right = ["横桁", "橋台"]     # 右の数字
            parts_zero = ["床版"]              # 00になる場合

            # namesから部品名（parts）と数字を抽出
            space = names.find(" ")
            parts = names[:space]  # 部品名
            number = ''.join(extract_number(names))  # 数字
            parts_join = names.replace(number, '') # 符号部分を取得

            # 必要な部分の数字を抽出するロジック
            split_number = ''

            if parts in parts_zero:
                split_number = '00'
            elif len(number) == 4 or int(number[2:]) >= 100:
                if parts in parts_left:
                    split_number = number[:2]
                elif parts in parts_right:
                    split_number = number[2:]
                else:
                    split_number = '00'
            else:
                if parts in parts_left:
                    split_number = number[:3]
                elif parts in parts_right:
                    split_number = number[3:]
                else:
                    split_number = '00'

            result = parts_join + split_number  # 結果を組み立てる
            return result
            # 共通のフィールドを辞書に格納
        infra = Infra.objects.filter(id=pk).first()
        print(f"Infra:{infra}({infra.id})") # 旗揚げチェック(4)
        article = infra.article
        print(f"article:{article}({article.id})") # お試し(2)
        table = Table.objects.filter(infra=infra.id, article=article.id).first()
        print(table) # 旗揚げチェック：お試し（infra/table/dxf/121_2径間番号違い.dxf）
        
    """ 管理サイトに登録するコード"""
                                
    """辞書型の多重リストをデータベースに登録(ここまで)"""

    # # テンプレートをレンダリング
    # return render(request, 'infra/bridge_table.html', context)
    if "search_title_text" in request.GET:
        # request.GET：検索URL（http://127.0.0.1:8000/article/1/infra/bridge_table/?search_title_text=1径間） 
        search_title_text = request.GET["search_title_text"]
        # 検索URL内のsearch_title_textの値（1径間）を取得する
    else:
        search_title_text = "1径間" # 検索URLにsearch_title_textがない場合
    second_search_title_text = "損傷図"
    
    bridges = FullReportData.objects.filter(infra=pk, span_number=search_title_text) # 径間で絞り込み
    # parts_name のカスタム順序リスト
    parts_order = ['主桁', '横桁', '床版', 'PC定着部', '橋台[胸壁]', '橋台[竪壁]', '橋台[翼壁]', '支承本体', '沓座モルタル', '防護柵', '地覆', '伸縮装置', '舗装', '排水ます', '排水管']
    damage_order = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳', '㉑', '㉒', '㉓', '㉔', '㉕', '㉖']

    grouped_data = []
    for key, group in groupby(bridges, key=attrgetter('join', 'damage_coordinate_x', 'damage_coordinate_y')):
        grouped_data.append(list(group))
        
    photo_grouped_data = []
    for pic_key, pic_group in groupby(bridges, key=attrgetter('this_time_picture', 'span_number')):
        photo_grouped_data.append(list(pic_group))
        
    buttons_count = int(table.infra.径間数) # 数値として扱う
    buttons = list(range(1, buttons_count + 1)) # For loopのためのリストを作成
    
    # range(一連の整数を作成):range(1からスタート, ストップ引数3 = 2 + 1) → [1, 2](ストップ引数は含まれない)
    print(buttons)
    
    print(f"ボタン:{Table.objects.filter(infra=pk)}")# ボタン:<QuerySet [<Table: Table object (1)>]>
        # クエリセットを使って対象のオブジェクトを取得
    table_object = Infra.objects.filter(id=pk).first()    
    print(f"橋梁番号:{table_object}")# ボタン:Table object (1)
    print(f"橋梁番号:{table_object.id}")
    article_pk = infra.article.id
    print(f"案件番号:{article_pk}") # 案件番号:1
    
    picture_data = [] # ここで毎回初期化されます
    for data in bridges:
        # クエリセットでフィルタリング
        matches = BridgePicture.objects.filter(
            picture_coordinate_x=data.picture_coordinate_x,
            picture_coordinate_y=data.picture_coordinate_y,
            span_number=data.span_number,
            table=data.table,
            infra=data.infra,
            article=data.article
        ).distinct()
        picture_data.append({"full_report": data, "matches": matches})
        
    context = {'object': table_object, 'article_pk': article_pk, 'grouped_data': grouped_data, 'photo_grouped_data': photo_grouped_data, 'buttons': buttons, 'picture_data': picture_data}
    # 渡すデータ：　損傷データ　↑　　　       　   joinと損傷座標毎にグループ化したデータ　↑　　　　　　 写真毎にグループ化したデータ　↑ 　　       径間ボタン　↑
    # テンプレートをレンダリング
    return render(request, 'infra/bridge_table.html', context)
  
def entity_extension(mtext, neighbor):
    # MTextの挿入点
    mtext_insertion = mtext.dxf.insert
    # 特定のプロパティ(Defpoints)で描かれた文字の挿入点
    neighbor_insertion = neighbor.dxf.insert
    #テキストの行数を求める
    text = mtext.plain_text()
    text_lines = text.split("\n") if len(text) > 0 else []
    # 改行で区切ったリスト数→行数
    text_lines_count = len(text_lines)
    
    # Defpointsを範囲内とするX座標範囲
    x_start = mtext_insertion[0]  # X開始位置
    x_end  = mtext_insertion[0] + mtext.dxf.width # X終了位置= 開始位置＋幅
    y_start = mtext_insertion[1] + mtext.dxf.char_height # Y開始位置
    y_end  = mtext_insertion[1] - mtext.dxf.char_height * (text_lines_count + 1) # 文字の高さ×(行数+1)
    print("～～ DXF文字情報 ～～")
    print(f"mtextテキスト:{mtext.dxf.text}\n　Dxfテキスト:{neighbor.dxf.text}")
    print(f"mtext挿入点:{mtext_insertion}\n　Def挿入点:{neighbor_insertion}\n　行数:{text_lines_count}")
    print(f"mtext文字幅:{mtext.dxf.width}\n　mtext1行当たりの文字高:{mtext.dxf.char_height}")
    print(f"X座標の取得範囲:{x_start}～{x_end}\nY座標の取得範囲:{y_start}～{y_end}")
    print("～～ DXF文字情報 ～～")
        
    # MTextの下、もしくは右に特定のプロパティで描かれた文字が存在するかどうかを判定する(座標：右が大きく、上が大きい)
    if (neighbor_insertion[0] >= x_start and neighbor_insertion[0] <= x_end):
        #y_endの方が下部のため、y_end <= neighbor.y <= y_startとする
        if (neighbor_insertion[1] >= y_end and neighbor_insertion[1] <= y_start):
            return True
    
    return False
  
def find_square_around_text(article_pk, pk, dxf_filename, target_text, second_target_text):
    print("関数の中身")
    print(dxf_filename)
    
    article = Article.objects.filter(id=article_pk).first()
    infra = Infra.objects.filter(id=pk).first()
    table = Table.objects.filter(infra=pk).first()
    
    # << S3からdxfファイルのダウンロード >>
    bucket_name = 'infraprotect'
    object_key = f'{article.案件名}/{infra.title}/{infra.title}.dxf'
    
    # ファイルパスにファイル名を含める
    local_file_path = f'{str(Path.home() / "Desktop")}\intect_dxf\{article.案件名}\{infra.title}\{infra.title}.dxf'

    def download_dxf_from_s3(bucket_name, object_key, local_file_path):
        s3 = boto3.client('s3')

        try:
            # フォルダが存在しない場合は作成
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # S3からファイルを指定したパスにダウンロード
            s3.download_file(bucket_name, object_key, local_file_path)
            print("ファイルのダウンロードが完了しました。")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

    # 関数を呼び出す
    download_dxf_from_s3(bucket_name, object_key, local_file_path)

    # ローカルファイルをezdxfで読み込む
    try:
        doc = ezdxf.readfile(local_file_path)
        print("途中経過　確認")
        msp = doc.modelspace()
        print("途中経過　確認")
    except IOError as e:
        print(f"ファイルの読み込みに失敗しました: {e}")
    except ezdxf.DXFStructureError as e:
        print(f"DXF構造エラー: {e}")
    # desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    # output_filepath = os.path.join(desktop_path, "CAD変更一時保存.dxf")
    # doc.saveas(output_filepath)
    
    text_positions = [] # 見つかったテキストの位置を格納するためのリストを作成
    extracted_text = []
    print("途中経過　確認1")
    # MTEXTエンティティの各要素をtextという変数に代入してループ処理
    for mtext_insert_point in msp.query('MTEXT'): # モデルスペース内の「MTEXT」エンティティをすべて照会し、ループ処理
        if mtext_insert_point.dxf.text == target_text: # エンティティのテキストが検索対象のテキストと一致した場合
            text_insertion_point = mtext_insert_point.dxf.insert # テキストの挿入点(dxf.insert)を取得します。
            text_positions.append(text_insertion_point[0]) # 挿入点のX座標をリストに保存
            break
    print("途中経過　確認2")
    if not text_positions: # text_positionsリストが空の場合(見つけられなかった場合)
        for mtext_insert_point in msp.query('MTEXT'): # モデルスペース内の「MTEXT」エンティティをすべて照会し、ループ処理
            if mtext_insert_point.dxf.text == second_target_text: # エンティティのテキストが検索対象のテキストと一致した場合
                text_insertion_point = mtext_insert_point.dxf.insert # テキストの挿入点(dxf.insert)を取得します。
                text_positions.append(text_insertion_point[0]) # 挿入点のX座標をリストに保存
                break
    print("途中経過　確認3")
    # Defpointsレイヤーで描かれた正方形枠の各要素をsquare変数に代入してループ処理
    for defpoints_square in msp.query('LWPOLYLINE[layer=="Defpoints"]'): # 
        if len(defpoints_square) == 4: # 正方形(=4辺)の場合
            square_x_values = [four_points[0] for four_points in defpoints_square] # squareというリストをループして各点(point)からx座標(インデックス0の要素)を抽出
            square_min_x = min(square_x_values) # 枠の最小X座標を取得
            square_max_x = max(square_x_values) # 枠の最大X座標を取得
            
        # 文字のX座標が枠の最小X座標と最大X座標の間にあるかチェック
        # text_positionsの各要素をtext_x_positionという変数に代入してforループを処理
        for text_x_position in text_positions:
            
            # 文字の座標がDefpoints枠のX座標内にある場合
            if square_min_x <= text_x_position <= square_max_x:
                
                # print(list(square)) 4点の座標を求める 
                left_top_point = list(defpoints_square)[0][0] # 左上の座標
                right_top_point = list(defpoints_square)[1][0] # 右上の座標
                right_bottom_point = list(defpoints_square)[2][0] # 右下の座標
                left_bottom_point = list(defpoints_square)[3][0] # 左下の座標

                defpoints_max_x = max(left_top_point,right_top_point,left_bottom_point,right_bottom_point) # X座標の最大値
                defpoints_min_x = min(left_top_point,right_top_point,left_bottom_point,right_bottom_point) # X座標の最小値
    print("途中経過　確認4")
    # 指定したX座標範囲内にあるテキストを探す
    for circle_in_text in msp.query('MTEXT'):
        if defpoints_min_x <= circle_in_text.dxf.insert.x <= defpoints_max_x and circle_in_text.dxf.layer != 'Defpoints':
        # MTextのテキストを抽出する
            text = circle_in_text.plain_text()
            x, y, _ = circle_in_text.dxf.insert
            if not text.startswith("※"):
                cad_data = text.split("\n") if len(text) > 0 else [] # .split():\nの箇所で配列に分配
                # if len(cad_data) > 0 and not text.startswith("※") and not any(keyword in text for keyword in ["×", ".", "損傷図"]):
                if len(cad_data) > 0 and not any(keyword in text for keyword in ["×", ".", "損傷図"]) and not text.endswith("径間"):
            # 改行を含むかどうかをチェックする(and "\n" in cad):# 特定の文字列で始まるかどうかをチェックする: # 特定の文字を含むかどうかをチェックする
                    related_text = "" # 見つけたMTextと関連するDefpointsレイヤの文字列を代入する変数
            # MTextの下、もしくは右に特定のプロパティ(Defpoints)で描かれた文字を探す
                    for neighbor in msp.query('MTEXT[layer=="Defpoints"]'): # DefpointsレイヤーのMTextを抽出
                    # MTextの挿入位置と特定のプロパティで描かれた文字の位置を比較する
                        if entity_extension(circle_in_text, neighbor):
                        # 特定のプロパティ(Defpoints)で描かれた文字のテキストを抽出する
                            related_text = neighbor.plain_text()
                            print(f"DXFテキストデータ:{related_text}")
                            defx, defy, _ = neighbor.dxf.insert
                        #extracted_text.append(neighbor_text)
                            break # 文字列が見つかったらbreakによりforループを終了する

                    if  len(related_text) > 0: #related_textに文字列がある＝Defpointsレイヤから見つかった場合
                        cad_data.append(related_text[:]) # cad_dataに「部材名～使用写真」までを追加
                        cad_data.append([str(x), str(y)]) # 続いてcad_dataに「MTEXT」のX,Y座標を追加
                #最後にまとめてcad_dataをextracted_textに追加する
                    extracted_text.append(cad_data[:] + [[str(defx), str(defy)]]) # extracted_textに「MTEXTとその座標」およびdefのX,Y座標を追加
                    
# << ※特記なき損傷の抽出用 ↓ >>                            
            else:
                lines = text.split('\n')# 改行でテキストを分割してリスト化
                sub_text = [[line] for line in lines]# 各行をサブリストとして持つ多重リストを構築

                pattern = r"\s[\u2460-\u3256]"# 文字列のどこかにスペース丸数字の並びがあるかをチェックする正規表現パターン
                pattern_start = r"^[\u2460-\u3256]"  # 文字列の開始が①～㉖であることをチェックする正規表現パターン
                pattern_anywhere = r"[\u2460-\u3256]"  # 文字列のどこかに①～㉖があるかをチェックする正規表現パターン
                last_found_circle_number = None  # 最後に見つかった丸数字を保持する変数

                # リストを逆順でループし、条件に応じて処理
                for i in range(len(sub_text)-1, -1, -1):  # 後ろから前にループ
                    item = sub_text[i][0]  # textリストの各サブリストの最初の要素（[0]）をitem変数に代入（地覆 ㉓-c）
                    if item.startswith("※"):
                        sub_text.remove(sub_text[i]) # 配列から除外する
                    elif re.search(pattern, item):  # itemが正規表現patternと一致している場合（スペース丸数字の並びがある）
                        last_found = item  # last_found変数にitem要素を代入（地覆 ㉓-c）
                        # print(last_found) 丸数字が付いている要素のみ出力
                    elif 'last_found' in locals():  # last_foundが定義されている（要素が代入されている）場合のみ
                        space = last_found.replace("　", " ")
                        # 大文字スペースがあれば小文字に変換
                        second = space.find(" ", space.find(" ") + 1)#10
                        # 2つ目のスペース位置まで抽出
                        sub_text[i][0] = item + last_found[second:]
                        # item:スペース丸数字の並びがない文字列
                        # last_found:スペース丸数字の並びがある文字列
                        # last_found[second:]:スペースを含めた文字列
                    elif re.match(pattern_start, item): # 文字列が①～㉖で開始するかチェック
                        last_found_circle_number = item # 丸数字の入っている要素を保持
                        sub_text.remove(sub_text[i])
                    else:
                        if last_found_circle_number is not None and not re.search(pattern_anywhere, item):
                            # 要素に丸数字が含まれておらず、直前に丸数字が見つかっている場合
                            sub_text[i][0] += " " + last_found_circle_number  # 要素の末尾に丸数字を追加

                for sub_list in sub_text:
                    # サブリストの最初の要素を取得してスペース区切りで分割
                    split_items = sub_list[0].split()
                    
                    # 分割した要素から必要なデータを取り出して新しいサブリストに格納
                    header = split_items[0] + " " + split_items[1]  # 例：'主桁 Mg0101'
                    status = split_items[2]  # 例：'①-d'
                    # photo_number = '写真番号-00'
                    # defpoints = 'defpoints'
                    
                    # 新しい形式のサブリストを作成してprocessed_listに追加
                    # new_sub_list = [header, status, photo_number, defpoints]
                    new_sub_list = [header, status]
                    extracted_text.append(new_sub_list)

                    new_sub_list.append([str(x), str(y)])
# << ※特記なき損傷の抽出用 ↑ >>
    return extracted_text
  
def create_picturelist(request, table, dxf_filename, search_title_text, second_search_title_text):
    print("関数スタート：create_picturelist")

    extracted_text = find_square_around_text(dxf_filename, search_title_text, second_search_title_text) # 関数の定義
    print("関数スタート：find_square_around_text")
    # リストを処理して、スペースを追加する関数を定義
    def add_spaces(text):
        # 正規表現でアルファベットと数字の間にスペースを挿入
        return re.sub(r'(?<! )([a-zA-Z]+)(\d{2,})', r' \1\2', text)

    # 変更されたリストを保存するための新しいリスト
    new_extracted_text = []

    # 各サブリストを処理
    for sub_extracted_text in extracted_text:
        # 先頭の文字列を修正
        if " " not in sub_extracted_text[0]:
            sub_extracted_text[0] = add_spaces(sub_extracted_text[0])
        # 新しいリストに追加
        new_extracted_text.append(sub_extracted_text)

    extracted_text = new_extracted_text

    for index, data in enumerate(extracted_text):
        # 最終項目-1まで評価
        if index < (len(extracted_text) -1):
            # 次の位置の要素を取得
            next_data = extracted_text[index + 1]
            # 特定の条件(以下例だと、１要素目が文字s1,s2,s3から始まる）に合致するかチェック
            if ("月" in next_data[0] and "日" in next_data[0]) or ("/" in next_data[0]) and (re.search(r"[A-Z]", next_data[0], re.IGNORECASE) and re.search(r"[0-9]", next_data[0])):
                # 合致する場合現在の位置に次の要素を併合 and "\n" in cad
                data.extend(next_data)
                # 次の位置の要素を削除
                extracted_text.remove(next_data)
    # extracted_text = [['主桁 Mg0101', '①-d', '写真番号-00', 'defpoints'], ['主桁 Mg0902', '⑦-c', '写真番号-00', 'defpoints']]

    # それぞれのリストから文字列のみを抽出する関数(座標以外を抽出)
        def extract_text(data):
            extracted = []  # 空のリストを用意
            removed_elements = []  # バックアップ用リスト

            pattern = r'[\u2460-\u3256]'  # ⓵～㉖

            for list_item in data:  # list_item変数に要素を代入してループ処理
                # print(list_item)
                item_extracted = [item for item in list_item if isinstance(item, str)]
                
                if item_extracted:  # item_extractedが空でないことを確認
                    # 最後の要素に特定の文字が含まれているかどうかをチェック
                    contains_symbols = bool(re.search(pattern, item_extracted[-1]))

                    # '月'と'日'が最後の要素に含まれているかどうかをチェック
                    if '月' in item_extracted[-1] and '日' in item_extracted[-1] and not contains_symbols:
                        extracted.append(item_extracted[:-2])
                        # 座標や日時を削除し、removed_elementsに保存
                        removed_elements.append([item for item in list_item if item not in item_extracted[:-2]])
                    else:
                        extracted.append(item_extracted)
                        # 座標や日時を削除し、removed_elementsに保存
                        removed_elements.append([item for item in list_item if item not in item_extracted])
                else:
                    extracted.append([])
                    removed_elements.append(list_item)

            return extracted, removed_elements  # extractedの結果を関数に返す

        # 関数を使って特定の部分を抽出
        extracted_text, removed_elements = extract_text(extracted_text)

        first_item = []
        current_detail = None  # 現在処理しているdetailを追跡

        for text, removed in zip(extracted_text, removed_elements):  # 1つずつのリスト
            result_list = []
            for item in text:# 1つずつの要素
            # 各条件を個別に確認する
                space_exists = re.search(r"\s+", item) is not None # スペースを含む
                alpha_exists = re.search(r"[a-zA-Z]+", item) is not None # アルファベットを含む
                digits_exists = re.search(r"\d{2,}", item) is not None # 2桁以上の数字を含む
            
                if space_exists and alpha_exists and digits_exists:
                # 新しいdetail項目を作成し、resultsに追加します
                    current_detail = {'detail': item, 'items': []}
                    result_list.append(current_detail)
                
                else:
                # 既存のdetailのitemsに現在の項目を追加
                    if current_detail is not None:
                        current_detail['items'].append(item)
                    
        # 元の要素を結果に追加
            for elem in removed:
                result_list.append(elem)

        #print(result_list)
            first_item.append(result_list)
        
        #print(first_item)
        extracted_text = first_item
            
        sub_first_item = [] 
        for check_sub_list in extracted_text:
            first_sub_item = []
            for first_sub_list in check_sub_list:
                # 各条件を個別に確認する
                space_exists = re.search(r"\s+", str(first_sub_list)) is not None # スペースを含む
                alpha_exists = re.search(r"[a-zA-Z]+", str(first_sub_list)) is not None # アルファベットを含む
                digits_exists = re.search(r"\d{2,}", str(first_sub_list)) is not None # 2桁以上の数字を含む
                # 正規表現を使って、コンマの直後に数字以外の文字が続く場所を見つけます。
                pattern = re.compile(r',(?![0-9])')
                # print(sub_list)
        # リスト内包表記で各要素をチェックして、条件に合致する場合は置き換えを行います。
                if space_exists and alpha_exists and digits_exists and not "月" in first_sub_list:
                    # sub_list自体を文字列に変換するのではなく、detailフィールドのみを操作する
                    detail_str = first_sub_list['detail']
                    # detail_strのカンマの直後に`</br>`タグを挿入
                    processed_str = pattern.sub(",", detail_str)
                    # processed_strをMarkup関数を使ってHTML安全なマークアップに変換
                    markup_str = Markup(processed_str)
                    # markup_strをリストに包む
                    wrapped_markup_str = [markup_str]
                    # first_sub_itemリストに追加
                    first_sub_item.append(wrapped_markup_str)
            sub_first_item.append(first_sub_item)
        # [[[Markup('横桁 Cr0503')]], [[Markup('主桁 Mg0110')], [Markup('床版 Ds0101')]], [[Markup('横桁 Cr0802')]], [[Markup('排水ます Dr0102,0201')]], [[Markup('排水ます Dr0202')]], [[Markup('PC定着部 Cn1101')]], [[Markup('排水ます Dr0102,0201,0202')]]]

            def process_item(item):
                if isinstance(item, Markup):
                    item = str(item)
                
                if ',' in item:
                    sub_items = item.split(',')
                    for i, sitem in enumerate(sub_items):
                        if i > 0 and sitem[0].isnumeric():
                            before_sub_item = sub_items[i - 1]
                            before_sub_item_splitted = before_sub_item.split()
                            before_sub_item_prefix = before_sub_item_splitted[0]
                            before_sub_item_suffix = ''
                            
                            for char in before_sub_item_splitted[1]:
                                if char.isnumeric():
                                    break
                                else:
                                    before_sub_item_suffix += char
                            
                            sub_items[i] = before_sub_item_prefix + ' ' + before_sub_item_suffix + sitem
                    item = ",".join(sub_items)
                
                return item.split(',')

            first_item = []
            for sub_one in sub_first_item:
                append2 = []
                for text_items in sub_one:
                    result_items = []
                    for item in text_items:
                        processed_items = process_item(item)
                        result_items.extend(processed_items)
                    append2.append(result_items)
                first_item.append(append2)

        # << ◆損傷種類(second)の要素◆ >> 
        # リストの各要素から記号を削除する関数
        def remove_symbols(other_items):
            symbols = ['!', '[', ']', "'"]

            processed_other_items = []
            for item in other_items:
                processed_item = ''.join(c for c in item if c not in symbols)
                processed_other_items.append(processed_item)

            return processed_other_items
        
        # それ以外の要素(損傷名)を抽出
        pattern = r'[\u2460-\u2473\u3251-\u3256].*-[a-zA-Z]' # 丸数字とワイルドカードとアルファベット
        second_items = []
        for second_sub_list in extracted_text:
            filtered_sub_list = []
            for damage_item in second_sub_list:
                if 'items' in damage_item:
                # sub_list自体を文字列に変換するのではなく、detailフィールドのみを操作する
                    detail_damage = damage_item['items']
                    for split_detail_damage in detail_damage:
                        if "," in split_detail_damage:
                            join_detail_damage = ""
                            middle_damage = split_detail_damage.split(",")
                            join_detail_damage = middle_damage
                        else:
                            join_detail_damage = detail_damage
                            
                    filtered_sub_list.append(join_detail_damage)
            second_items.append(filtered_sub_list)

        third_items = []
        bottom_item = []
        damage_coordinate = []
        picture_coordinate = []
        for other_sub_list in extracted_text:
            list_count = sum(isinstance(item, list) for item in other_sub_list) # リストの中にリストがいくつあるか数える
            
            if list_count == 2: # 座標が2つのとき=Defpointsが存在するとき
                bottom_item.append(other_sub_list[-3]) # 最後から3番目の要素を抽出（写真番号-00）
                third_items.append(other_sub_list[-4]) # 最後から4番目の要素を抽出（Defpoints）
                damage_coordinate.append(other_sub_list[-2])
                picture_coordinate.append(other_sub_list[-1])
            else: # Defpointsがない時
                bottom_item.append("") # bottom:写真番号なし
                third_items.append(None) # third:Defpointsなし
                damage_coordinate.append(other_sub_list[-1]) # damage:
                picture_coordinate.append(None) # picture:写真指定なし
        #print(other_sub_list)
        print("~~~~~~~~~~~")
        print(bottom_item)
        result_items = []# 配列を作成
        for item in bottom_item:# text_itemsの要素を1つずつitem変数に入れてforループする
            print("～～～")
            print(f"データ確認：{item}")
            if isinstance(item, str) and ',' in item:# 要素が文字列で中にカンマが含まれている場合に実行
                pattern = r',(?![^(]*\))'
                sub_items = re.split(pattern, item)# カンマが含まれている場合カンマで分割
                extracted_item = []# 配列を作成
                
                for sub_item in sub_items:# bottom_itemの要素を1つずつitem変数に入れてforループする
                    for p in range(len(sub_item)):#itemの文字数をiに代入
                        if "A" <= sub_item[p].upper() <= "Z" and p < len(sub_item) - 1 and sub_item[p+1].isnumeric():#i文字目がアルファベットかつ、次の文字が数字の場合
                            extracted_item.append(sub_item[:p+1]+"*/*"+sub_item[p+1:])# アルファベットと数字の間に*/*を入れてextracted_itemに代入
                            break
                join = ",".join(extracted_item)# 加工した内容をカンマ区切りの１つの文字列に戻す
                result_items.append(join)# result_itemsに格納

            elif isinstance(item, str) or ',' in item:  # 要素が文字列でカンマを含まない場合
                non_extracted_item = ''  # 変数のリセット
                for j in range(len(item)):
                    if "A" <= item[j].upper() <= "Z" and j < len(item) - 1 and item[j+1].isnumeric():#i文字目がアルファベットかつ、次の文字が数字の場合
                        non_extracted_item = item[:j+1]+"*/*"+item[j+1:]#アルファベットまでをextracted_itemに代入
                    elif non_extracted_item == '':
                        non_extracted_item = item
                result_items.append(non_extracted_item)
            else:
                result_items.append(item)

        def remove_parentheses_from_list(last):
            pattern = re.compile(r"\([^()]*\)")
            result = [pattern.sub("", string) for string in last]
            return result

        last_item = remove_parentheses_from_list(result_items)

        damage_table = []  # 空のリストを作成
        # table_instance = Table.objects.filter(infra=pk).first()
        # print(f"写真パス:{table_instance.infra.article.ファイルパス}")
        # print(f"橋梁名:{table_instance.infra.title}")
        # first_itemの要素の数だけループ処理
        for i in range(len(first_item)):
            try:
                third = third_items[i]
            except IndexError:
                third = None
            
            # ['NON-a', '9月7日 S404', '9月7日 S537', '9月8日 S117,9月8日 S253']
            if len(last_item)-1 < i:
                break

            if isinstance(last_item[i], list):
                continue
            else:
                # 組み合わせを収集するリスト
                replacements = []

                # name_entriesの取得 NameEntry.objects.all()
                # tableにarticleが紐付いているため、そこから取得(tableのinfraのarticle(id))
                name_entries = NameEntry.objects.filter(article = Article.pk)
                print(name_entries)

                # 置換情報を収集する
                for name_entry in name_entries:
                    replacements.append((name_entry.alphabet, name_entry.name))
                replacements.append((" ", "　"))
                # print(f'replacements: {replacements}')
                # 置換リストをキーの長さで降順にソート
                sorted_replacements = sorted(replacements, key=lambda x: len(x[0]), reverse=True)

                # 置換関数を定義
                def replace_all(text, replacements):
                    return reduce(lambda acc, pair: acc.replace(pair[0], pair[1]), replacements, text)
                
                name_item = replace_all(last_item[i], sorted_replacements) # アルファベットを名前に置換
              # name_item = last_item[i].replace("S", "佐藤").replace("H", "濵田").replace(" ", "　")
            # name_item に格納されるのは 'NON-a', '9月7日 佐藤*/*404', '9月7日 佐藤*/*537', '9月8日 佐藤*/*117,9月8日 佐藤*/*253'のいずれか
            
            pattern = r',(?![^(]*\))'
            dis_items = re.split(pattern, name_item)#「9月8日 佐藤*/*117」,「9月8日 佐藤*/*253」
            # コンマが付いていたら分割
            
            time_result = []
            current_date = ''  # 現在の日付を保持する変数
            for time_item in dis_items:
                #print(f"このデータは：{time_item}")
                # 先頭が数字で始まるかチェック（日付として扱えるか）
                if re.match(r'^\d', time_item):
                    current_date = re.match(r'^\d+月\d+日', time_item).group(0)  # 日付を更新
                    time_result.append(time_item)  # 日付がある項目はそのまま追加
                else:
                    # 日付がない項目は、現在の日付を先頭に追加
                    time_result.append(''.join([current_date, '　', time_item]))

            name_and_wildcardnumber = [item + ".jpg" for item in time_result]
            # ['9月8日 佐藤*/*117.jpg', '9月8日 佐藤*/*253.jpg']
            
            # << S3にアップロードした写真のワイルドカード検索 >>
            s3 = boto3.client('s3')

            bucket_name = 'infraprotect'

            # << カッコを含む文字を削除 ※二重かっこ「 (( 他 )) 」は不可 >>
            # sub_dis_items = ['9月8日 佐藤(いろいろ)/*117.jpg', '9月8日 佐藤(ぽけぽけ)/*253.jpg']
            # スラッシュとコンマで分割する
            pattern = r'\(.*?\)|\.jpg|\*' # カッコとその中・「.jpg」・「*」を削除
            split_wildcard_lists = [re.split(r'[,/]', re.sub(pattern, '', item)) for item in name_and_wildcardnumber]
            # リストを表示する
            s3_folder_name = [item[0]+"/" for item in split_wildcard_lists] # ['9月8日 佐藤', '9月8日 佐藤']
            wildcard_picture = tuple(item[1] for item in split_wildcard_lists) # ('117', '253')

            def search_s3_objects(bucket, prefix, pattern):
                paginate = s3.get_paginator("list_objects_v2")
                matching_keys = []  # 見つかったキーを保持するリスト

                # 各ページを順に確認
                for page in paginate.paginate(Bucket=bucket, Prefix=prefix):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            key = obj['Key']
                            # パターンに基づいてファイルが一致しているか確認
                            if fnmatch.fnmatch(key, f"{prefix}*{pattern}.jpg"):
                                matching_keys.append(key)

                return matching_keys

            sub_dis_items = []

            for prefix, pattern in zip(s3_folder_name, wildcard_picture):
                found_keys = search_s3_objects(bucket_name, prefix, pattern)
                for found_key in found_keys:
                    # 各見つかったキーに基づいてURLを生成してリストに追加
                    object_url = f"https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{found_key}"
                    sub_dis_items.append(object_url)

            print("この写真URLは：", sub_dis_items)
            
            photo_paths = []
            # photo_pathsリストを作成
            for item in sub_dis_items:
                # decoded_item = urllib.parse.unquote(item) # デコード
                # normalized_item = decoded_item.replace('/', '\\')
                # print(f"decoded_item:{decoded_item}")
                #print(f"item：{item}")
                # sub_photo_paths = glob.glob(normalized_item)
                sub_photo_paths = glob.glob(item)
                photo_paths.extend(sub_photo_paths)
                # photo_pathsリストにsub_photo_pathsを追加
            
            if len(photo_paths) > 0:# photo_pathにはリストが入るため、[i]番目の要素が0より大きい場合
                picture_urls = [''.join(photo_path).replace('infra/static/', '') for photo_path in photo_paths]
                # picture_urls = [''.join(photo_path).replace('infra/static/', '').replace('infra/img\\', '') for photo_path in photo_paths]
                # photo_pathsの要素の数だけphoto_pathという変数に代入し、forループを実行
                # photo_pathという1つの要素の'infra/static/'を空白''に置換し、中間文字なしで結合する。
                # picture_urlsという新規配列に格納する。
                # print(f"photo_paths：{picture_urls}")
            else:# それ以外の場合
                picture_urls = None
                #picture_urlsの値は[None]とする。
            
    # << ◆写真メモを作成するコード◆ >>

            bridge_damage = [] # すべての"bridge"辞書を格納するリスト

            bridge = {
                "parts_name": first_item[i],
                "damage_name": second_items[i] if i < len(second_items) else None  # second_itemsが足りない場合にNoneを使用
            }
            bridge_damage.append(bridge)

    # << ◆1つ1つの部材に対して損傷を紐付けるコード◆ >>
            first_element = bridge_damage[0]

            # 'first'キーの値にアクセス
            first_value = first_element['parts_name']

            first_and_second = []
            #<<◆ 部材名が1種類かつ部材名の要素が1種類の場合 ◆>>
            if len(first_value) == 1: # 部材名称が1つの場合
                if len(first_value[0]) == 1: # 要素が1つの場合
                    # カッコを1つ減らすためにリストをフラットにする
                    flattened_first = [first_buzai_item for first_buzai_sublist in first_value for first_buzai_item in first_buzai_sublist]
                    first_element['parts_name'] = flattened_first
                    # 同様に 'second' の値もフラットにする
                    second_value = first_element['damage_name']
                    flattened_second = [second_name_item for second_name_sublist in second_value for second_name_item in second_name_sublist]
                    first_element['damage_name'] = flattened_second

                    first_and_second.append(first_element)
                    #print(first_and_second) # [{'first': ['排水管 Dp0102'], 'second': ['①腐食(小大)-c', '⑤防食機能の劣化(分類1)-e']}]

                #<<◆ 部材名が1種類かつ部材名の要素が複数の場合 ◆>>
                else: # 別の部材に同じ損傷が紐付く場合
                        # 元のリストから各要素を取得
                    for first_buzai_item in bridge_damage:
                        #print(item)
                        before_first_elements = first_buzai_item['parts_name'][0]  # ['床版 Ds0201', '床版 Ds0203']
                        first_elements = []

                        for first_buzai_second_name in before_first_elements:
                            if "～" in first_buzai_second_name:

                                first_step = first_buzai_second_name

                                if " " in first_step:
                                    # 部材記号の前にスペースが「含まれている」場合
                                    first_step_split = first_step.split()

                                else:
                                    # 部材記号の前にスペースが「含まれていない」場合
                                    first_step_split = re.split(r'(?<=[^a-zA-Z])(?=[a-zA-Z])', first_step) # アルファベット以外とアルファベットの並びで分割
                                    first_step_split = [kara for kara in first_step_split if kara] # re.split()の結果には空文字が含まれるので、それを取り除く

                                # 正規表現
                                number = first_step_split[1]
                                # マッチオブジェクトを取得
                                number_part = re.search(r'[A-Za-z]*(\d+～\d+)', number).group(1)

                                one = number_part.find("～")

                                start_number = number_part[:one]
                                end_number = number_part[one+1:]

                                # 最初の2桁と最後の2桁を取得
                                start_prefix = start_number[:2]
                                start_suffix = start_number[2:]
                                end_prefix = end_number[:2]
                                end_suffix = end_number[2:]

                                # 「主桁 Mg」を抽出
                                prefix_text = first_step_split[0] + " " + re.match(r'[A-Za-z]+', number).group(0)

                                # 決められた範囲内の番号を一つずつ追加
                                for prefix in range(int(start_prefix), int(end_prefix)+1):
                                    for suffix in range(int(start_suffix), int(end_suffix)+1):
                                        number_items = "{}{:02d}{:02d}".format(prefix_text, prefix, suffix)
                                        first_elements.append(number_items)
                            else:
                                first_elements.append(first_buzai_second_name)
                        
                        
                        second_elements = first_buzai_item['damage_name'][0]  # ['⑦剥離・鉄筋露出-d']

                        
                        # first の要素と second を一対一で紐付け
                        for first_buzai_second_name in first_elements:
                            first_and_second.append({'parts_name': [first_buzai_second_name], 'damage_name': second_elements})

                #print(first_and_second) # [{'first': '床版 Ds0201', 'second': '⑦剥離・鉄筋露出-d'}, {'first': '床版 Ds0203', 'second': '⑦剥離・鉄筋露出-d'}]

            #<<◆ 部材名が複数の場合 ◆>>
            else:
                for double_item in bridge_damage:
                    first_double_elements = double_item['parts_name'] # [['支承本体 Bh0101'], ['沓座モルタル Bm0101']]
                    second_double_elements = double_item['damage_name'] # [['①腐食(小小)-b', '⑤防食機能の劣化(分類1)-e'], ['⑦剥離・鉄筋露出-c']]
                    
                    for break_first, break_second in zip(first_double_elements, second_double_elements):
                        first_and_second.append({'parts_name': break_first, 'damage_name': break_second})

            for damage_parts in bridge_damage:
                # print(damage_parts)
                if isinstance(damage_parts["damage_name"], list):  # "second"がリストの場合
                    filtered_second_items = []
                    for sublist in damage_parts["damage_name"]:
                        if isinstance(sublist, list):  # サブリストがリストである場合
                            if any(item.startswith('①') for item in sublist) and any(item.startswith('⑤') for item in sublist):
                                # ⑤で始まる要素を取り除く
                                filtered_sublist = [item for item in sublist if not item.startswith('⑤')]
                                filtered_second_items.append(filtered_sublist)
                            else:
                                filtered_second_items.append(sublist)
                        else:
                            filtered_second_items.append([sublist])
                    
                    # フィルタリング後のsecond_itemsに対して置換を行う                
                    #pavement_items = {"first": first_item[i], "second": filtered_second_items}
                        
            combined_list = []
            if damage_parts["damage_name"] is not None:
                combined_second = filtered_second_items #if i < len(updated_second_items) else None
            else:
                combined_second = None
            
            combined = {"parts_name": first_item[i], "damage_name": combined_second}
            combined_list.append(combined)
            request_list = combined_list[0]
            # <<◆ secondの多重リストを統一させる ◆>>
            try:
                # データを取得する
                check_request_list = request_list['parts_name'][1]

                # 条件分岐
                if isinstance(check_request_list, list):
                    request_list
                    #print(request_list)
                    
            except (KeyError, IndexError) as e:
                # KeyError や IndexError の例外が発生した場合の処理

                # secondの多重リストをフラットなリストに変換
                flat_list = [item for sublist in request_list['damage_name'] for item in sublist]
                # フラットなリストを再びサブリストに変換して格納
                request_list['damage_name'] = [flat_list]
                # 完成目標の確認
                
                test = request_list['damage_name'][0]

            # 先頭が文字（日本語やアルファベットなど）の場合
            def all_match_condition(lst):
                """
                リスト内のすべての項目が特定条件に一致するか確認します。
                ただし、空のリストの場合、Falseを返します。
                """
                # 空のリストの場合は False を返す
                if not lst:
                    return False
                
                pattern = re.compile(r'\A[^\W\d_]', re.UNICODE)
                return all(pattern.match(item) for item in lst)

            if all_match_condition(test):
                request_list
            else:
                request_list['damage_name'] = [request_list['damage_name']]

            #<< ◆損傷メモの作成◆ >>
            replacement_patterns = {
                "①腐食(小小)-b": "腐食", # 1
                "①腐食(小大)-c": "全体的な腐食",
                "①腐食(大小)-d": "板厚減少を伴う腐食",
                "①腐食(大大)-e": "全体的に板厚減少を伴う腐食",
                "②亀裂-c": "塗膜割れ", # 2
                "②亀裂-e": "長さのある塗膜割れ・幅0.0mmの亀裂",
                "③ゆるみ・脱落-c": "ボルト・ナットにゆるみ、脱落(●本中●本)", # 3
                "③ゆるみ・脱落-e": "ボルト・ナットにゆるみ、脱落(●本中●本)",
                "④破断-e": "鋼材の破断", # 4
                "⑤防食機能の劣化(分類1)-e": "点錆", # 5
                "⑥ひびわれ(小小)-b": "最大幅0.0mmのひびわれ", # 6
                "⑥ひびわれ(小大)-c": "最大幅0.0mmかつ間隔0.5m未満のひびわれ",
                "⑥ひびわれ(中小)-c": "最大幅0.0mmのひびわれ",
                "⑥ひびわれ(中大)-d": "最大幅0.0mmかつ間隔0.5m未満のひびわれ",
                "⑥ひびわれ(大小)-d": "最大幅0.0mmのひびわれ",
                "⑥ひびわれ(大大)-e": "最大幅0.0mmかつ間隔0.5m未満のひびわれ",
                "⑦剥離・鉄筋露出-c": "コンクリートの剥離", # 7
                "⑦剥離・鉄筋露出-d": "鉄筋露出",
                "⑦剥離・鉄筋露出-e": "断面減少を伴う鉄筋露出",
                "⑧漏水・遊離石灰-c": "漏水", # 8
                "⑧漏水・遊離石灰-d": "遊離石灰",
                "⑧漏水・遊離石灰-e": "著しい遊離石灰・泥や錆汁の混入を伴う漏水",
                "⑨抜け落ち-e": "コンクリート塊の抜け落ち", # 9
                "⑪床版ひびわれ-b": "最大幅0.0mmの1方向ひびわれ", # 11
                "⑪床版ひびわれ-c": "最大幅0.0mmの1方向ひびわれ",
                "⑪床版ひびわれ-d": "最大幅0.0mmの1方向ひびわれ",
                "⑪床版ひびわれ-e": "最大幅0.0mmの角落ちを伴う1方向ひびわれ",
                "⑫うき-e": "コンクリートのうき", # 12
                "⑮舗装の異常-c": "最大幅0.0mmのひびわれ", # 15
                "⑮舗装の異常-e": "最大幅0.0mmのひびわれ・舗装の土砂化",
                "⑯定着部の異常-c": "定着部の損傷", # 16
                "⑯定着部の異常(分類2)-e": "定着部の著しい損傷",
                "⑳漏水・滞水-e": "漏水・滞水", # 20
                "㉓変形・欠損-c": "変形・欠損", # 23
                "㉓変形・欠損-e": "著しい変形・欠損",
                "㉔土砂詰まり-e": "土砂詰まり", # 24
            }

            def describe_damage(unified_request_list):
                described_list = []
                
                for damage in unified_request_list:
                    if damage in replacement_patterns: # 辞書に一致する場合は登録文字を表示
                        described_list.append(replacement_patterns[damage])
                    elif damage.startswith('⑰'): # 17の場合はカッコの中を表示
                        match = re.search(r'(?<=:)(.*?)(?=\)-e)', damage)
                        if match:
                            described_list.append(match.group(1))
                    else:
                        pattern = r'[\u3248-\u3257](.*?)-'
                        match = re.search(pattern, damage)
                        if match:
                            described_list.append(match.group(1))
                        else:
                            described_list.append(damage)  # フォールバックとしてそのまま返す
                return ','.join(described_list)

            # 各ケースに対して出力を確認:
            def generate_report(unified_request_list):
                primary_damages = []
                processed_related_damages = []
                #print(f"unified_request_list：{unified_request_list}")
                first_items = unified_request_list['parts_name']
                #print(first_items) # [['支承本体 Bh0101'], ['沓座モルタル Bm0101']]
                second_items = unified_request_list['damage_name']
                #print(second_items) # [['①腐食(小小)-b', '⑤防食機能の劣化(分類1)-e'], ['⑦剥離・鉄筋露出-c']]
                primary_damages_dict = {}

                for first_item, second_item in zip(first_items, second_items):
                    element_names = [f.split()[0] for f in first_item] # カッコ内の要素について、スペースより前を抽出
                    #print(f"element_names：{element_names}") # ['支承本体'], ['沓座モルタル']
                    damage_descriptions = describe_damage(second_item) # 辞書で置換
                    #print(f"damage_descriptions：{damage_descriptions}") # 腐食,点錆, 剥離
                    
                    if len(element_names) == 1: # ['主桁', '横桁', '対傾構']：これはだめ
                        primary_damages.append(f"{element_names[0]}に{damage_descriptions}が見られる。")
                        #print(f"primary_damages：{primary_damages}") # ['支承本体に腐食,点錆が見られる。', '沓座モルタルに剥離が見られる。']
                    else:
                        element_names = list(dict.fromkeys(element_names))            
                        joined_elements = "および".join(element_names[:-1]) + "," + element_names[-1]
                        if joined_elements.startswith(","):
                            new_joined_elements = joined_elements[1:]
                        else:
                            new_joined_elements = joined_elements
                        primary_damages.append(f"{new_joined_elements}に{damage_descriptions}が見られる。")

                    for elem in first_item:
                        primary_damages_dict[elem] = second_item[:]

                primary_description = "また".join(primary_damages)
                    
                for elem_name, elem_number in zip(first_items, second_items): # 主桁 Mg0101
                    # リストをフラットにする関数
                    def flatten_list(nested_list):
                        return [item for sublist in nested_list for item in sublist]
                    
                    # 辞書から 'first' と 'second' の値を取り出す
                    first_list = request_list['parts_name']
                    second_list = request_list['damage_name']

                    # 'first' の要素数を数える
                    first_count = sum(len(sublist) for sublist in first_list)

                    # 'second' の要素数を数える
                    second_count = sum(len(sublist) for sublist in second_list)
                    # フラットにしたリストを比較
                    if flatten_list(first_items) != elem_name and flatten_list(second_items) != elem_number:
                        sub_related_damages = []
                        for first_item in first_items:
                            for elem in first_item:
                                if elem in primary_damages_dict:
                                    formatted_damages = ",".join(list(dict.fromkeys(primary_damages_dict[elem])))
                                    sub_related_damages.append(f"{elem}:{formatted_damages}")
                                    #print(f"sub_related_damages：{sub_related_damages}") # ['支承本体 Bh0101:①腐食(小小)-b,⑤防食機能の劣化(分類1)-e', '沓座モルタル Bm0101:⑦剥離・鉄筋露出-c']

                        # 処理後のリストを格納するための新しいリスト
                        second_related_damages = []

                        # リスト内の各要素をループする
                        for i, damage in enumerate(sub_related_damages):
                            # コロンの位置を取得
                            colon_index = damage.find(":")
                            
                            if colon_index != -1:
                                if i == 0:
                                    # 1番目の要素の場合
                                    parts = damage.split(',')
                                    
                                    if len(parts) > 1:
                                        first_damage = parts[0].split(':')[0]
                                        after_damage = ':' + parts[1].strip()
                                        create_damage = first_damage + after_damage
                                        second_related_damages.append(create_damage)

                                else:
                                    # 2つ目以降の要素の場合
                                    parts = damage.split(',')
                                    second_related_damages.append(damage)
                                    

                        # 処理後のリストを格納するための新しいリスト
                        processed_related_damages = []
                        #print(f"second_related_damages：{second_related_damages}")
                        for damage in second_related_damages:
                            colon_index = damage.find(":")
                            if colon_index != -1:
                                before_colon_part = damage[:colon_index].strip()
                                after_colon_part = damage[colon_index + 1:].strip()
                                #print(f"damage[colon_index + 1:]：{damage}")
                                if before_colon_part and after_colon_part:
                                    processed_damage = f"{before_colon_part}:{after_colon_part}"
                                    processed_related_damages.append(processed_damage)
                        #print(f"after_colon_part：{processed_related_damages}")
                        
                    elif first_count < 2 and second_count < 2: # {'first': [['横桁 Cr0803']], 'second': [['⑦剥離・鉄筋露出-d']]}
                        None
                    elif first_count > 1 and second_count < 2: # {'first': [['床版 Ds0201', '床版 Ds0203']], 'second': [['⑦剥離・鉄筋露出-d']]}
                        first_items_from_first = first_item[1:]
                        related_damage_list = ','.join(first_items_from_first)# カンマ区切りの文字列に結合
                        related_second_item = ','.join(second_item)
                        processed_related_damages.append(f"{related_damage_list}:{related_second_item}")
                    elif first_count < 2 and second_count > 1: # {'first': [['横桁 Cr0503']], 'second': [['⑦剥離・鉄筋露出-d', '⑰その他(分類6:施工不良)-e']]}
                        second_items_from_second = second_item[1:]
                        related_damage_list = ','.join(second_items_from_second)# カンマ区切りの文字列に結合
                        processed_related_damages.append(f"{','.join(elem_name)}:{related_damage_list}")
                    else:#  len(elem_name) > 1 and len(elem_number) > 1: # {'first': [['排水管 Dp0101', '排水管 Dp0102']], 'second': [['①腐食(小大)-c', '⑤防食機能の劣化(分類1)-e']]}
                        related_damage_list = ','.join(second_item)
                        processed_related_damages.append(f"{','.join(elem_name)}:{related_damage_list}")


                related_description = ""
                if processed_related_damages:
                    related_description = "\n【関連損傷】\n" + ", ".join(processed_related_damages)

                return f"{primary_description} {related_description}".strip()

            combined_data = generate_report(request_list)
            #print(combined_data)
            # print(f"picture_urls：{picture_urls}")
            
                    # \n文字列のときの改行文字
            items = {'parts_name': first_item[i], 'damage_name': second_items[i], 'join': first_and_second, 
                     'picture_number': third, 'this_time_picture': picture_urls, 'last_time_picture': None, 'textarea_content': combined_data, 
                     'damage_coordinate': damage_coordinate[i], 'picture_coordinate': picture_coordinate[i]}
            print(f"items：{items}")
            damage_table.append(items)

        #優先順位の指定
        order_dict = {"主桁": 1, "横桁": 2, "床版": 3, "PC定着部": 4, "橋台[胸壁]": 5, "橋台[竪壁]": 6, "支承本体": 7, "沓座モルタル": 8, "防護柵": 9, "地覆": 10, "伸縮装置": 11, "舗装": 12, "排水ます": 13, "排水管": 14}
        order_number = {"None": 0, "①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5, "⑥": 6, "⑦": 7, "⑧": 8, "⑨": 9, "⑩": 10, "⑪": 11, "⑫": 12, "⑬": 13, "⑭": 14, "⑮": 15, "⑯": 16, "⑰": 17, "⑱": 18, "⑲": 19, "⑳": 20, "㉑": 21, "㉒": 22, "㉓": 23, "㉔": 24, "㉕": 25, "㉖": 26}
        order_lank = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
                
        # <<◆ リストの並び替え ◆>>
        def sort_key_function(sort_item):
            first_value = sort_item['parts_name'][0][0] # firstキーの最初の要素
            #print(first_value) # 主桁 Mg0901

            if " " in first_value:
                # 部材記号の前にスペースが「含まれている」場合
                first_value_split = first_value.split()
                #print(first_value_split) # ['主桁', 'Mg0901']
            else:
                # 部材記号の前にスペースが「含まれていない」場合
                first_value_split = re.split(r'(?<=[^a-zA-Z])(?=[a-zA-Z])', first_value) # アルファベット以外とアルファベットの並びで分割
                first_value_split = [x for x in first_value_split if x] # re.split()の結果には空文字が含まれるので、それを取り除く
                #print(f"first_value_split：{first_value_split}") # ['主桁', 'Mg0901']

            first_name_key = order_dict.get(first_value_split[0], float('inf'))
            #print(first_name_key) # 1
            if "～" in first_value_split[1]:
                match = re.search(r'[A-Za-z]+(\d{2,})(\D)', first_value_split[1])
                if match:
                    first_number_key = int(match.group(1))
            else:
                first_number_key = int(first_value_split[1][2:])
            #print(first_number_key) # 901

            if sort_item['damage_name'][0][0]:  # `second`キーが存在する場合
                second_value = sort_item['damage_name'][0][0] # secondキーの最初の要素
                #print(second_value) # ⑰その他(分類6:異物混入)-e
                second_number_key = order_number.get(second_value[0], float('inf'))  # 先頭の文字を取得してorder_numberに照らし合わせる
                #print(second_number_key) # 17
                second_lank_key = order_lank.get(second_value[-1], float('inf'))  # 末尾の文字を取得してorder_lankに照らし合わせる
                #print(second_lank_key) # 5
            else:
                second_number_key = float('inf')
                second_lank_key = float('inf')
                    
            return (first_name_key, first_number_key, second_number_key, second_lank_key)

        sorted_items = sorted(damage_table, key=sort_key_function)
        # print(f"sorted_items：{sorted_items}")
    return sorted_items