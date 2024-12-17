from db_connection import db
from django.db import models

# Create your models here
login_details = db['users']
employee_details = db['employees']