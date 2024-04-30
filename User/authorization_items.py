# these are item someone allowed to do something
music_info_to_update_by_user = ['title', 'artist', 'genre', 'album', 'release_date']
music_info_to_update_by_staff = music_info_to_update_by_user + ['is_active', 'is_reviewed']
music_info_to_get_by_user = \
    ['title', 'artist', 'genre', 'album', 'release_date', 'cover_url', 'source_url', 'lyrics_url', 'likes', 'shares', 'search_volume']

user_info_user = ['email', 'username', 'password']
user_info_staff = user_info_user + ['is_active', 'is_creator']

music_source_type = ['mp3', 'ogg', 'wav', 'flac']

task_type = ['delete', 'review']
task_update_item = ['task_priority', 'task_type', 'task_name',
                    'task_notes', 'task_complete_time', 'task_state']
task_item_to_get = ['task_id', 'task_name', 'task_type', 'task_priority', 'task_tags',
                    'task_notes', 'task_creator', 'create_date', 'task_state', 'task_completed_time']

comment_item_to_update_by_user = ['creator', 'content']

music_list_item_to_update_by_user = ['list_type', 'list_name', 'description', 'music_list', 'is_public']
music_list_item_to_update_by_staff = music_list_item_to_update_by_user + ['is_public']
music_list_item_to_get_by_user = ['list_id', 'creator', 'list_type', 'list_name', 'create_date',
                                  'music_list', 'playback_volume', 'search_volume']
music_list_item_to_get_by_staff = music_list_item_to_get_by_user + ['is_public']
