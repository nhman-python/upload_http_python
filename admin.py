from werkzeug.security import generate_password_hash, check_password_hash

password = generate_password_hash('test')
admin = generate_password_hash('test')


with open('.env', 'w') as f:
    f.write(
        f'PASSWORD={password}\n'
        f'ADMIN_USER={admin}'
    )
print('password and user create')