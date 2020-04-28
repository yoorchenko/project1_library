from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os
import csv

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

b = open("books.csv")
reader = csv.reader(b)
i = 0
for isbn, title, author, year in reader:
    db.execute("INSERT INTO books(isbn, title, author, year) VALUES(:isbn, :title, :author, :year)",
               {"isbn":isbn, "title":title, "author":author, "year":year})
    i += 1
    print(i)
db.commit()