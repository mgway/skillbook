Skillbook is a web based tool for managing skill plans for EVE Online. 


Requirements
---
**For development:**

* postgreql-server >= 9.1
* postgresql-server-dev-X.Y
* python >= 3.3
* redis >= 2.6
* virtualenv is nice to have but isn't strictly required

**For production:**

* lighttpd or nginx
* supervisord

All of the python package dependencies can be found in the requirements file:

	$ pip install -r setup/requirements.txt

Additionally, data extract from the CCP SDE requires:

* mysql-server >= 5.5
* oursql

Note: This extract is **not** required; the result of the extract is provided in data.sql


PostgreSQL setup
---
Create the user and database:

	$ sudo -u postgres psql

	CREATE DATABASE eveskill;
	CREATE USER eveskill WITH PASSWORD 'eveskill';
	GRANT ALL ON DATABASE eveskill TO eveskill;
 
Load the schema and static data:

	$ psql eveskill < setup/schema.sql
	$ psql eveskill < setup/data.sql


Server setup
---
Once you have all of the dependencies installed and have both the database and redis running:

	$ cp config.yaml.example config.yaml
	
And configure as appropriate

Run the server with 
	
	$ python server.py

**For production use:**

* Configure lighttpd or nginx to act as a reverse proxy. Sample configuration files are located in `setup/lighttpd.conf.example` and `setup/nginx.conf.example`
* Configure supervisord 


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

