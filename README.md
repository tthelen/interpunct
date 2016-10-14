# interpunct - Embeddable punctuation trainer

The embeddable puntuation trainer for German presents tasks (= sentences) to the user. The user sets and/or removes commas and submits the solution. 

Later, the server will update a user model and select a new task.

## Installation

interpunct is a Django application developped with Python 3.4 and Django 1.10.

To get it running from the github repository, only 

python manage.py runserver

is necessary, as a demo sqlite database is included.

## Admin access 

Adding new sentences currently is only possible via the django admin interface.

URL: Add /admin
Username for demo database: admin
Password: adminadmin

ATTENTION: Never change sentences already in the database.
