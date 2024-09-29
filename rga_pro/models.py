from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)

class Vector(db.Model):
    __tablename__ = 'vectors'
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), primary_key=True)
    vector = db.Column(db.LargeBinary, nullable=False)
    document = db.relationship('Document', backref=db.backref('vector', uselist=False))
