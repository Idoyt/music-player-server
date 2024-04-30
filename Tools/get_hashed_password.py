from django.contrib.auth.hashers import make_password
import json
import os
import django

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Server.settings')

# 加载Django设置
django.setup()

# 生成密码的哈希值
password_hash = make_password("123456")

# 创建Fixture数据
fixture_data = [
    {
        "model": "User.CustomUser",
        "fields": {
            "email": "123@staff.com",
            "username": "staff_user",
            "password": password_hash,
            "is_staff": True
        }
    }
]

# 将Fixture数据写入文件
with open('../initial_user_data.json', 'w') as f:
    json.dump(fixture_data, f)
