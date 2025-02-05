Keskustelusovellus

Sovelluksessa näkyy keskustelualueita, joista jokaisella on tietty aihe. Alueilla on keskusteluketjuja, jotka muodostuvat viesteistä. Jokainen käyttäjä on peruskäyttäjä tai ylläpitäjä.

Sovelluksen ominaisuuksia:

    - Käyttäjä voi kirjautua sisään ja ulos sekä luoda uuden tunnuksen.
    - Käyttäjä näkee sovelluksen etusivulla listan alueista sekä jokaisen alueen ketjujen ja viestien määrän ja viimeksi lähetetyn viestin ajankohdan.
    - Käyttäjä voi luoda uuden keskustelualueen.
    - Käyttäjä voi luoda alueelle uuden ketjun antamalla ketjun otsikon, joka toimii aloitusviestinä.
    - Käyttäjä voi kirjoittaa uuden viestin olemassa olevaan ketjuun.
    - Käyttäjä voi muokata luomansa ketjun otsikkoa/aloitusviestiä sekä lähettämänsä viestien sisältöä. Käyttäjä voi myös poistaa ketjun tai viestin.
    - Käyttäjä voi etsiä kaikki viestit, joiden osana on annettu sana.
    - Ylläpitäjä voi lisätä ja poistaa salaisia keskustelualueita, sekä määrittää, keillä käyttäjillä on pääsy salaiselle alueelle.


Sovelluksen asennus

    - Asenna Flask
    - Asenna Flask sqlalchemy
    - Asenna Flask PostgreSQL adapter psycopg2:
        $ pip install psycopg2-binary

    - Asenna PostgreSQL psql
    - Vie schema.sql tiedosto psql:ään:
        $ psql mydatabase < /path/to/schema.sql

    - Asenna ja aja virtuaalinen ympäristö (venv):
        $ source venv/bin/activate
        $ flask run
    - Poistu virtuaalisesta ympäristöstä (venv):
        $ deactivate
