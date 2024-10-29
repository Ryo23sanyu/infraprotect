import re


this_time_picture = 'https://infraprotect.s3.ap-northeast-1.amazonaws.com/%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB/%E7%B7%91%E6%A9%8B/9%E6%9C%887%E6%97%A5%E3%80%80%E4%BD%90%E8%97%A4/P9070450.JPG, https://infraprotect.s3.ap-northeast-1.amazonaws.com/%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB/%E7%B7%91%E6%A9%8B/9%E6%9C%887%E6%97%A5%E3%80%80%E4%BD%90%E8%97%A4/P9070452.JPG'

this_time_picture_parts = this_time_picture.split(',')
for i, picture in enumerate(this_time_picture_parts):
  print(i)
  print(picture)
  
this_time_picture = 'https://infraprotect.s3.ap-northeast-1.amazonaws.com/%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB/%E7%B7%91%E6%A9%8B/9%E6%9C%887%E6%97%A5%E3%80%80%E4%BD%90%E8%97%A4/P9070450.JPG, https://infraprotect.s3.ap-northeast-1.amazonaws.com/%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB/%E7%B7%91%E6%A9%8B/9%E6%9C%887%E6%97%A5%E3%80%80%E4%BD%90%E8%97%A4/P9070452.JPG'

this_time_picture_parts = this_time_picture.split(',')
for i, picture in enumerate(this_time_picture_parts):
  print(i)
  print(picture)
  
def remove_unwanted_prefix(text):
    # 「https:/」を探して、それ以前の部分を削除する
    parts = text.split('https:/', 1)
    if len(parts) > 1:
        return 'https:/' + parts[1]
    else:
        return None

# 使用例
input_text = "不要な文字https://example.com"
cleaned_text = remove_unwanted_prefix(input_text)
print(cleaned_text)  # "https://example.com"が出力されます

this_time_picture = 'https://infraprotect.s3.ap-northeast-1.amazonaws.com/%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB/%E7%B7%91%E6%A9%8B/9%E6%9C%887%E6%97%A5%E3%80%80%E4%BD%90%E8%97%A4/P9070396.JPG, https://infraprotect.s3.ap-northeast-1.amazonaws.com/%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB/%E7%B7%91%E6%A9%8B/9%E6%9C%887%E6%97%A5%E3%80%80%E4%BD%90%E8%97%A4/P9070412.JPG'
list_in_picture = this_time_picture.split(",")
print(list_in_picture)
for i in list_in_picture:
  print(i)
  print("///")
  
new = '⑦剥離・鉄筋露出-e'
damage_name = re.sub(r'-.{1}$', '', new)
print(damage_name)