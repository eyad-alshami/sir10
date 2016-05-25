import os
import psycopg2
import urlparse

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["postgres://clwhxwmbefonuv:Mf-xNtCZnLYmxeSlspq4hQtEhg@ec2-54-243-201-107.compute-1.amazonaws.com:5432/d2k42j0fi9n0ah"])


conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cur = conn.cursor()
cur.execute('SELECT version()')          
ver = cur.fetchone()
print ver  
