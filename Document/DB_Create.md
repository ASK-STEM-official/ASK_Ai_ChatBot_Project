# DBのクリエイト文(暫定)
```sql
CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE vectors (
    document_id INT,
    vector LONGBLOB NOT NULL,
    PRIMARY KEY (document_id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
```