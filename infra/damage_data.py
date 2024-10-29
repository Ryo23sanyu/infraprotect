damage_data = {'parts_name': [['横桁 Cr0802']], 'damage_name': [['⑦剥離・鉄筋露出-e']], 'join': [{'parts_name': ['横桁 Cr0802'], 'damage_name': ['⑦剥離・鉄筋露出-e']}], 
               'picture_number': '写真番号-13,14', 
               'this_time_picture': ['https://infraprotect.s3.ap-northeast-1.amazonaws.com/%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB/%E7%B7%91%E6%A9%8B/9%E6%9C%887%E6%97%A5%E3%80%80%E4%BD%90%E8%97%A4/P9070396.JPG', 'https://infraprotect.s3.ap-northeast-1.amazonaws.com/%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB/%E7%B7%91%E6%A9%8B/9%E6%9C%887%E6%97%A5%E3%80%80%E4%BD%90%E8%97%A4/P9070412.JPG'], 'last_time_picture': None, 
               'textarea_content': '横桁に断面減少を伴う鉄筋露出が見られる。', 'damage_coordinate': ['538443.3187868086', '218366.5575399188'], 'picture_coordinate': ['538761.6085522854', '218087.1577589952'], 'search': '1径間'}

new_database_items = []

# picture_number をコンマで分割
picture_numbers = damage_data['picture_number'].split(',')

# this_time_picture の各要素に対して新しい damage_data を作成
if len(picture_numbers) == len(damage_data['this_time_picture']):
    for i in range(len(picture_numbers)):
        new_damage_data = {
            'picture_name': damage_data['parts_name'],
            'damage_name': damage_data['damage_name'],
            'join': damage_data['join'],
            'picture_number': picture_numbers[i].strip(),
            'this_time_picture': [damage_data['this_time_picture'][i]],
            'last_time_picture': [damage_data['last_time_picture'][i]] if damage_data['last_time_picture'] else None,
            'textarea_content': damage_data['textarea_content'],
            'damage_coordinate': damage_data['damage_coordinate'],
            'picture_coordinate': damage_data['picture_coordinate'],
            'search': damage_data['search']
        }
        new_database_items.append(new_damage_data)
else:
    # 長さが一致しない場合の処理
    print("Warning: The number of picture_numbers and this_time_picture items do not match.")

# 出力して確認
print(new_database_items)