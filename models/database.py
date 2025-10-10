from sqlalchemy import Column, Integer, String, LargeBinary
from config import Base

class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True)
    school_name = Column(String)
    district = Column(String)
    county = Column(String)
    state = Column(String)


class NewUsers(Base):
    __tablename__ = "new_users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    state = Column(String)
    county = Column(String)
    district = Column(String)
    school = Column(String)
    phone_number = Column(String)
    password = Column(String)
    role = Column(String)
    report = Column(Integer)
    emailed = Column(Integer)


class RegisteredUsers(Base):
    __tablename__ = "registered_users"

    id = Column(Integer, primary_key=True)
    email = Column(String)
    phone_number = Column(String)
    password = Column(String)
    role = Column(String)
    createCount = Column(Integer, default=0)


class TeacherList(Base):
    __tablename__ = "teacher_list"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    state = Column(String)
    county = Column(String)
    district = Column(String)
    school = Column(String)
    regUserID = Column(Integer)
    wishlist_url = Column(String)
    about_me = Column(String)
    image_data = Column(LargeBinary)
    url_id = Column(String)


class Spotlight(Base):
    __tablename__ = "spotlight"

    id = Column(Integer, primary_key=True)
    token = Column(String)
    name = Column(String)
    state = Column(String)
    county = Column(String)
    district = Column(String)
    school = Column(String)
    image_data = Column(LargeBinary)