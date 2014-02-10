Skillbook is a web based tool for managing skill plans for EVE Online. 


Requirements
---

Development requirements:
PostgreSQL >= 9.2
python >= 3.2
psycopg2, requests

A requirements file is provided for your convenience:

	pip install -r requirements.txt

Additionally, (optional) data extract from the CCP SDE requires:
MySQL
oursql


PostgreSQL setup
---

User eveskill
Password eveskill
Database eveskill

	bunzip2 skillbook.sql.bz2 | psql


License
---

skillbook uses the [AGPLv3 license](http://www.gnu.org/licenses/agpl-3.0.html) which is 
available in the `AGPL3.txt` file.


CCP Copyright notice
---

EVE Online and the EVE logo are the registered trademarks of CCP hf. All rights are reserved. 
All other trademarks are the property of their respective owners. CCP hf. has granted
permission to use the information and graphics provided within this application but does not 
endorse, and is not in any way affiliated with this project.
