from flask import Flask, request, render_template, redirect, url_for
from transformers import BertTokenizer, BertModel
import torch
from sshtunnel import SSHTunnelForwarder
import mariadb
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)

# SSHトンネルとDB接続のグローバル変数
server = None
connection = None

def create_ssh_tunnel():
    global server
    server = SSHTunnelForwarder(
        ('xs333002.xsrv.jp', 10022),  # SSHサーバーのホストとポート
        ssh_username='xs333002',  # SSHユーザー名
        ssh_pkey=r'C:\Users\ootom\OneDrive\デスクトップ\文化祭のネタ\rga_pro\xs333002 (1).key',  # SSHキーのパス
        remote_bind_address=('localhost', 3306),  # リモートのMariaDBホストとポート
        local_bind_address=('localhost', 5969)  # ローカルでバインドするポート
    )
    server.start()
    logging.info("SSHトンネルが正常に開始されました")

def get_db_connection():
    global connection
    if connection is None:
        try:
            connection = mariadb.connect(
                host='localhost',
                port=5969,  # SSHトンネルを通じてバインドしたポート
                user='xs333002_root',
                password='Stemask1234',
                database='xs333002_stem'
            )
            logging.info("データベース接続が確立されました")
        except mariadb.Error as e:
            logging.error(f"Database connection error: {e}")
            raise
    return connection

# Flaskアプリの設定
app = Flask(__name__)

# BERTモデルの準備
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        # データベース接続を取得
        conn = get_db_connection()
        cursor = conn.cursor()

        # ドキュメントを保存
        cursor.execute("INSERT INTO documents (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
        document_id = cursor.lastrowid

        # ベクトル化
        inputs = tokenizer(content, return_tensors='pt', truncation=True, padding=True, max_length=512)
        outputs = model(**inputs)
        vector = outputs.last_hidden_state.mean(dim=1).detach().numpy().tobytes()  # ベクトル化

        # ベクトルを保存
        cursor.execute("INSERT INTO vectors (document_id, vector) VALUES (?, ?)", (document_id, vector))
        conn.commit()

        cursor.close()

        return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    create_ssh_tunnel()  # SSHトンネルを作成
    try:
        app.run(debug=True)
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
    finally:
        if connection:
            connection.close()  # データベース接続をクローズ
            logging.info("データベース接続がクローズされました")
        if server:
            server.stop()  # SSHトンネルを停止
            logging.info("SSHトンネルが停止しました")
