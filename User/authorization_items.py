# these are item someone allowed to do something
music_info_user = ['title', 'artist', 'genre', 'album', 'release_date']
music_info_staff = music_info_user + ['is_active']

user_info_user = ['email', 'username', 'password']
user_info_staff = user_info_user + ['is_active', 'is_creator']

music_source_type = ['.mp3', '.ogg', '.wav', 'flac']

task_type = ['delete', 'review']
task_update_item = ['task_priority', 'task_type', 'task_name',
                    'task_notes', 'task_complete_time', 'task_state']
task_type_to_get = ['all'] + task_type
task_item_to_get = ['task_id', 'task_name', 'task_type', 'task_priority', 'task_tags',
                    'task_notes', 'task_creator', 'create_date', 'task_state', 'task_completed_time']
