from flask_login import UserMixin
from passlib.hash import sha256_crypt
from models import *

class User(UserMixin):
    def __init__(self, email, password=None, user_data=None):
        self.db = model()
        self.email = email
        self.errorLogin = 0

        if user_data:
            # Se fornecido diretamente (ex: no get_user)
            self.user_record = user_data
            self.name = user_data.name
            self.password_hash = user_data.password
            self.password = password
        else:
            # Autenticação normal via email
            query = self.db(self.db.user.email == email)
            if not query.isempty():
                self.user_record = query.select(self.db.user.ALL).first()
                self.name = self.user_record.name
                self.password_hash = self.user_record.password
                self.password = password
            else:
                self.user_record = None

    def get_id(self):
        return str(self.user_record.id) if self.user_record else None

    def is_active(self):
        return True

    def is_authenticated(self):
        if not self.user_record:
            self.errorLogin = 1
            return False
        if sha256_crypt.verify(self.password, self.password_hash):
            return True
        self.errorLogin = 2
        return False

    def is_anonymous(self):
        return False

    @classmethod
    def get_user(cls, user_id):
        db = model()
        query = db(db.user.id == int(user_id))
        if query.isempty():
            return None
        user_data = query.select(db.user.ALL).first()
        return cls(user_data.email, user_data=user_data)
