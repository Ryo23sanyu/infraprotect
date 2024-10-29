if not is_multi_list(split_names):
    picture_number_index = 0
    
    for single_damage in damages: 
        parts_name = names[0]
        pattern = r"(\d+)$"
        match = re.search(pattern, parts_name)
        
        if match:
            four_numbers = match.group(1)
        else:
            four_numbers = "00"
            
        damage_name = flatten(single_damage)
        parts_split = process_names(flatten(parts_name))
        list_in_picture = this_time_picture.split(",")
        
        for single_picture in list_in_picture:
            update_fields = {
                'parts_name': parts_name,
                'four_numbers': four_numbers,
                'damage_name': damage_name,
                'parts_split': parts_split,
                'join': join,
                'this_time_picture': single_picture,
                'last_time_picture': last_time_picture,
                'textarea_content': textarea_content,
                'span_number': span_number,
                'special_links': '/'.join([str(parts_split), str(damage_name), str(span_number)]),
                'infra': infra,
                'article': article,
                'table': table
            }
            print(f"update_fields：{update_fields}")

            if update_fields['this_time_picture']:
                print(update_fields['this_time_picture'])
                images = [update_fields['this_time_picture']]
                update_fields['picture_number'] = picture_counter
                picture_counter += 1

                if numbers_only is not None and numbers_only != '':
                    print(f"images：{images}")
                    
                    for image_path in images:
                        absolute_image_path = image_path
                        print(f"absolute_image_path：{absolute_image_path}") # 写真パス1（別データとして、写真パス2）
                        try:
                            if picture_number_index < len(picture_number_box):
                                current_picture_number = picture_number_box[picture_number_index]
                            else:
                                current_picture_number = None

                            if current_picture_number is None: # 写真がない
                                join_picture_damage_name = BridgePicture.objects.filter(damage_coordinate_x=damage_coordinate_x, damage_coordinate_y=damage_coordinate_y, table=table, infra=infra, article=article)
        
                                if join_picture_damage_name.first():
                                  
                                    for picture in join_picture_damage_name:
                                        if picture.damage_name:
                                            edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                                            new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', damage_name)
                                            damage_name = re.sub(r'-.{1}$', '', new_damage_name)
                                            picture.memo = f"{picture.memo} / {parts_split},{damage_name}"
                                        else:
                                            picture.memo = f"{parts_split},{damage_name}"
                                        picture.save()
                                continue
                            pattern = r'\s+[A-Za-z]{2,}[0-9]{2,}'

                            def remove_alphabets(match):
                                return re.sub(r'[A-Za-z]+', '', match.group())

                            edited_result_parts_name = re.sub(pattern, remove_alphabets, parts_split)
                            new_damage_name = re.sub(r'^[\u2460-\u2473\u3251-\u3256]', '', damage_name)
                            damage_name = re.sub(r'-.{1}$', '', new_damage_name)

                            existing_picture = BridgePicture.objects.filter(
                                picture_number=current_picture_number,
                                span_number=span_number,
                                table=table,
                                article=article,
                                infra=infra
                            ).first()
                            
                            if existing_picture is None:
                                bridge_picture = BridgePicture(
                                    image=absolute_image_path, 
                                    picture_number=current_picture_number,
                                    damage_name=damage_name,
                                    parts_split=edited_result_parts_name,
                                    memo=f"{edited_result_parts_name},{damage_name}",
                                    span_number=span_number,
                                    table=table,
                                    article=article,
                                    infra=infra
                                )
                                bridge_picture.save()
                                picture_number_index += 1
                        except FileNotFoundError:
                            print(f"ファイルが見つかりません: {absolute_image_path}")
    
        else:
            update_fields['picture_number'] = ""
            
        report_data_exists = FullReportData.objects.filter(**update_fields).exists()
        if report_data_exists:
            print("データが存在しています。")
        else:
            try:
                damage_obj, created = FullReportData.objects.update_or_create(**update_fields)
                damage_obj.save()
            except IntegrityError:
                print("ユニーク制約に違反していますが、既存のデータを更新しませんでした。")