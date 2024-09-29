from sshtunnel import SSHTunnelForwarder
import mariadb

def get_db_connection():
    server = SSHTunnelForwarder(
        ('xs333002.xsrv.jp', 10022),  # SSHサーバーのホストとポート
        ssh_username='xs333002',  # SSHユーザー名
        ssh_pkey=r'C:\Users\ootom\OneDrive\デスクトップ\文化祭のネタ\rga_pro\xs333002 (1).key',  # SSHキーのパス
        remote_bind_address=('localhost', 3306),  # リモートのMariaDBホストとポート
        local_bind_address=('localhost', 3306)  # ローカルでバインドするポート
    )
    server.start()

    connection = mariadb.connect(
        host='localhost',
        port=3306,  # SSHトンネルを通じてバインドしたポート
        user='xs333002_root',
        password='Stemask1234',  # MariaDBのユーザーのパスワード    
        database='xs333002_stem'  
    )
    return connection
