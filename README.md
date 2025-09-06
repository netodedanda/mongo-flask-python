# CRUD Flask MySQL + MongoDB

CRUD em **Python/Flask** com MySQL (SQLAlchemy) e MongoDB (PyMongo).

## Config
MySQL: `SQLALCHEMY_DATABASE_URI = "mysql+pymysql://neto:neto@localhost:3306/crud"`  
MongoDB: `MONGO_URL = "mongodb://root:neto@localhost:27017/vendas?authSource=vendas"`

## Rodar
```bash
venv\Scripts\activate
pip install -r requirements.txt
python main.py
