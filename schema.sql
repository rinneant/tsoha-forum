CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    admin BOOLEAN DEFAULT FALSE
);

CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    content TEXT UNIQUE,
    secret BOOLEAN DEFAULT FALSE,
    visible BOOLEAN DEFAULT TRUE
);

CREATE TABLE threads (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects,
    user_id INTEGER REFERENCES users,
    content TEXT,
    visible BOOLEAN DEFAULT TRUE
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    thread_id INTEGER REFERENCES threads,
    user_id INTEGER REFERENCES users,
    created_at TIMESTAMP,
    content TEXT,
    visible BOOLEAN DEFAULT TRUE
);



'''
###Tee rekisteröinnissä pieni ruudukko, johon voi kirjoittaa koodin, jolla voi saada admin-oikeudet, jos koodit täsmäävät###
##Admin voi luoda salaisen alueen, ja valita listasta kaikki ne käyttäjät, jotka voivat nähdä alueen##
# Pitää olla mahdollisuus luoda uusi alue, ketju ja lisätä teksti, jos koko keskusteluforumi on tyhjä#
Lisää user_id referenssi subjects, threads ja messages taulukoihin. Lisää näihin kolmeen edellämainittuun, kuka ne on luonut/lähettänyt.
'''


