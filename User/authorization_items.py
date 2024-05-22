# these are item someone allowed to do something
music_info_to_update_by_user = ['title', 'artist', 'genre', 'album', 'release_date']
music_info_to_update_by_staff = music_info_to_update_by_user + ['is_active', 'is_reviewed']
music_info_to_get_by_user = ['title', 'artist', 'genre', 'album', 'release_date', 'cover_extension', 'source_extension',
                             'lyrics_extension', 'likes', 'shares', 'search_volume']
music_info_to_get_by_staff = music_info_to_get_by_user + ['is_active', 'is_reviewed', 'music_id']

user_info_to_get_by_user = ['email', 'username']
user_info_to_get_by_staff = user_info_to_get_by_user + ['is_active', 'is_creator', 'uuid']
user_info_to_update_by_user = ['email', 'username', 'password', 'avatar_url', 'to_be_delete', 'follower_id_list',
                               'following_id_list','dislikes_music', 'dislikes_list']
user_info_to_update_by_staff = user_info_to_update_by_user + ['is_active', 'is_creator']

task_type = ['delete.user', 'delete.music','review.user', 'review.music']
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


allowed_upload_audio_type = ['ogg', 'mp3', 'wav']
allowed_upload_image_type = ['png']
allowed_upload_lyric_type = ['lrc']
allowed_upload_file_type = allowed_upload_image_type + allowed_upload_lyric_type + allowed_upload_audio_type
