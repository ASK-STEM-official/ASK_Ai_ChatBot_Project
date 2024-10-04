from flask import Flask, jsonify, request
import mariadb
import logging
from sshtunnel import SSHTunnelForwarder
import numpy as np
import torch
from transformers import BertTokenizer, BertModel
import datetime
from scipy.spatial import distance
import google.generativeai as genai
# Gemini APIの設定
genai.configure(api_key="AIzaSyBJc9NcsOWwnmSH-robtbpsEJXENwDwRoE")
app = Flask(__name__)
# BERTのトークナイザーとモデルの準備
tokenizer = BertTokenizer.from_pretrained('cl-tohoku/bert-base-japanese')
model = BertModel.from_pretrained('cl-tohoku/bert-base-japanese')
# SSHトンネルの作成
def create_ssh_tunnel():
    global server
    server = SSHTunnelForwarder(
        ('xs333002.xsrv.jp', 10022),
        ssh_username='xs333002',
        ssh_pkey=r'./xs333002.key',
        remote_bind_address=('localhost', 3306),
        local_bind_address=('localhost', 10022)
    )
    server.start()
    logging.info("SSHトンネルが正常に開始されました")
# データベース接続の取得
def get_db_connection():
    try:
        connection = mariadb.connect(
            host='localhost',
            port=10022,
            user='xs333002_root',
            password='Stemask1234',
            database='xs333002_chatrag'
        )
        return connection
    except mariadb.Error as e:
        logging.error(f"Database connection error: {e}")
        raise
# 文書をベクトル化する関数
def vectorize_document(content):
    inputs = tokenizer(content, return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    vector = outputs.last_hidden_state.mean(dim=1).numpy()
    return vector[0]
# 文書をデータベースに登録する関数
def add_document_to_db(title, content):
    vector = vectorize_document(content)
    vector_blob = vector.tobytes()
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''INSERT INTO Document (title, content, vector, created_at)
                      VALUES (?, ?, ?, ?)''',
                   (title, content, vector_blob, datetime.datetime.now()))
    connection.commit()
    cursor.close()
    connection.close()
# 文書を検索する関数
def search_documents(query_vector):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT title, content, vector FROM Document")
    results = []
    for (title, content, vector_blob) in cursor.fetchall():
        vector = np.frombuffer(vector_blob, dtype=np.float32)
        dist = distance.cosine(query_vector, vector)
        results.append((title, content, dist))
    cursor.close()
    connection.close()
    results.sort(key=lambda x: x[2])
    return results
# Gemini APIを使用して検索結果を文章化する関数
def generate_summary_from_results(results, query_content):
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = "これはユーザーからの質問と質問をベクトル検索した結果のデータです。質問内容と結果のデータをもとに、ユーザーへの返答文を記述してください。口調は丁寧な口調を心掛けてください。ベクトル検索した結果のデータの内容を崩さないようにしてください。もしも、検索結果にない質問が来た場合はごめんなさいしてください。\n"
    for result in results:
        prompt += f"検索内容: {query_content}\nタイトル: {result[0]}\n内容: {result[1]}\n類似度: {result[2]}\n\n"
    response = model.generate_content(prompt)
    return response.text
# APIエンドポイント: 文書を追加
@app.route('/add_document', methods=['POST'])
def add_document():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    if title and content:
        add_document_to_db(title, content)
        return jsonify({"message": "Document added successfully!"}), 200
    else:
        return jsonify({"error": "Title and content are required"}), 400
# APIエンドポイント: 文書を検索
@app.route('/search_document', methods=['POST'])
def search_document():
    data = request.get_json()
    query_content = data.get('content')
    if query_content:
        query_vector = vectorize_document(query_content)
        results = search_documents(query_vector)
        summary = generate_summary_from_results(results, query_content)
        return jsonify({
            "summary": summary,
            "results": [{"title": r[0], "content": r[1], "distance": r[2]} for r in results]
        }), 200
    else:
        return jsonify({"error": "Content is required for search"}), 400
# アプリを実行
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    create_ssh_tunnel()
    app.run(host='0.0.0.0', port=5000, debug=True)