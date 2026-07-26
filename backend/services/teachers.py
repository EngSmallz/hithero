import base64


def serialize_teacher_summary(teacher):
    return {
        "name": teacher.name,
        "url_id": teacher.url_id,
        "state": teacher.state,
        "county": teacher.county,
        "district": teacher.district,
        "school": teacher.school,
    }


def serialize_teacher_profile(teacher):
    image_data = None
    if teacher.image_data:
        image_data = base64.b64encode(teacher.image_data).decode("utf-8")

    return {
        "name": teacher.name,
        "url_id": teacher.url_id,
        "state": teacher.state,
        "county": teacher.county,
        "district": teacher.district,
        "school": teacher.school,
        "wishlist_url": teacher.wishlist_url,
        "about_me": teacher.about_me,
        "image_data": image_data,
    }
