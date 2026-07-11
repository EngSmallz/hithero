from fastapi.staticfiles import StaticFiles

from backend.routers.admin import create_admin_router
from backend.routers.forum import create_forum_router
from backend.routers.legacy import create_legacy_router, register_legacy_error_handlers
from backend.routers.profile import create_profile_router
from backend.routers.teachers import create_teacher_router


def register_routers(
    application,
    *,
    session_factory,
    teacher_model,
    spotlight_model,
    school_model,
    directory_response_model,
    profile_response_model,
    post_model,
    comment_model,
    vote_model,
    vote_input_model,
    post_update_model,
    pending_user_model,
    registered_user_model,
    reset_token_model,
    get_current_id,
    get_current_role,
    get_current_email,
    get_index_cookie,
    set_teacher_session,
    verify_recaptcha,
    send_registration_email,
    render_email_template,
    send_email,
    get_admin_secret,
    send_validation_email,
    send_attachment,
    detect_file_type,
    max_file_size,
    limiter,
    clean_html,
    allowed_tags,
    allowed_attrs,
    allowed_protocols,
    model_to_dict,
    logger,
):
    """Register the existing routers without moving their endpoint logic.

    Keeping this wiring dependency-driven lets the compatibility ``app.py``
    remain the deployment entry point while the domain routers are extracted
    incrementally.
    """

    application.include_router(
        create_legacy_router(
            session_factory=session_factory,
            teacher_model=teacher_model,
            spotlight_model=spotlight_model,
            set_teacher_session=set_teacher_session,
            logger=logger,
        )
    )
    application.mount("/pages", StaticFiles(directory="pages"), name="pages")
    register_legacy_error_handlers(application)

    application.include_router(
        create_teacher_router(
            session_factory=session_factory,
            school_model=school_model,
            teacher_model=teacher_model,
            directory_response_model=directory_response_model,
            profile_response_model=profile_response_model,
        )
    )

    application.include_router(
        create_forum_router(
            session_factory=session_factory,
            post_model=post_model,
            comment_model=comment_model,
            vote_model=vote_model,
            vote_input_model=vote_input_model,
            post_update_model=post_update_model,
            get_current_id=get_current_id,
            get_current_role=get_current_role,
            limiter=limiter,
            clean_html=clean_html,
            allowed_tags=allowed_tags,
            allowed_attrs=allowed_attrs,
            allowed_protocols=allowed_protocols,
            model_to_dict=model_to_dict,
        )
    )

    application.include_router(
        create_profile_router(
            session_factory=session_factory,
            pending_user_model=pending_user_model,
            registered_user_model=registered_user_model,
            teacher_model=teacher_model,
            reset_token_model=reset_token_model,
            get_current_id=get_current_id,
            get_current_role=get_current_role,
            get_current_email=get_current_email,
            get_index_cookie=get_index_cookie,
            set_teacher_session=set_teacher_session,
            verify_recaptcha=verify_recaptcha,
            send_registration_email=send_registration_email,
            render_email_template=render_email_template,
            send_email=send_email,
            limiter=limiter,
            detect_file_type=detect_file_type,
            max_file_size=max_file_size,
            logger=logger,
        )
    )

    application.include_router(
        create_admin_router(
            session_factory=session_factory,
            pending_user_model=pending_user_model,
            registered_user_model=registered_user_model,
            teacher_model=teacher_model,
            get_current_id=get_current_id,
            get_current_role=get_current_role,
            set_teacher_session=set_teacher_session,
            get_index_cookie=get_index_cookie,
            send_validation_email=send_validation_email,
            send_attachment=send_attachment,
            logger=logger,
            get_admin_secret=get_admin_secret,
        )
    )

    return application
