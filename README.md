Skillbook is a web based tool for managing skill plans for EVE Online. 


Requirements
---

Development requirements:
PostgreSQL >= 9.2
python >= 3.2
psycopg2, requests

Additionally, (optional) data extract from the CCP SDE requires:
MySQL
oursql

PostgreSQL setup
---

User eveskill
Password eveskill
Database eveskill

	bunzip2 skillbook.sql.gz2
	psql < skillbook.sql

