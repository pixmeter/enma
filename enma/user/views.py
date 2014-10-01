# -*- coding: utf-8 -*-
import time
import datetime

from flask import Blueprint, render_template, flash, redirect, url_for
from flask import current_app
from flask.ext.login import login_required, current_user, logout_user

from enma.decorators import permission_required
from enma.user.models import User, Permission, Role
from enma.user.forms import DeleteForm, EditForm, ChangePasswordForm, \
    UserAdminForm
from enma.user.forms import RestTokenForm
from enma.database import db
from enma.utils import flash_errors
from enma.activity.models import record_priviledge, record_authentication,\
    record_user


blueprint = Blueprint("user", __name__, url_prefix='/users',
                        static_folder="../static")


@blueprint.route("/")
@login_required
def home():
    current_app.logger.error('token called')

    return render_template("users/home.html")

@blueprint.route("/members")
@login_required
@permission_required(Permission.READ_USER)
def members():
    users = User.query.all()
    return render_template("users/members.html", users=users)


@blueprint.route("/delete/<name>",  methods=["GET", "POST"])
@login_required
@permission_required(Permission.DELETE_USER)
def delete(name):
    user = User.query.filter_by(id=name).first()
    return _delete(user)


@blueprint.route("/terminate", methods=["GET", "POST"])
@login_required
def terminate():
    return _delete(current_user)


def _delete(user):
    delete_form = DeleteForm(user=user, prefix='delete_form')
    if delete_form.delete.data:
        if delete_form.validate():
            db.session.delete(user)
            db.session.commit()
            if user == current_user:
                # delete yourself!!!
                logout_user()
                flash('You are removed from the system and logged out.', 'info')
                record_user('Terminated', user)
                return redirect(url_for('public.home'))
            else:
                flash("User %s deleted" % str(user.username), 'info')
                record_user('Delete by admin', user)
                return redirect(url_for('user.members'))
        else:
            flash_errors(delete_form)

    return render_template("users/delete.html", delete_form=delete_form )


@blueprint.route("/profile/",  methods=["GET", "POST"])
@login_required
def profile():
    user = current_user
    edit_form = EditForm()
    if edit_form.apply.data:
        if edit_form.validate():
            user.first_name = edit_form.firstname.data
            user.last_name = edit_form.lastname.data
            user.email = edit_form.email.data
            db.session.add(user)
            db.session.commit()
            record_user('Update Profile')
            flash('Your profile has been updated', 'info')
        else:
            flash_errors(edit_form)
    edit_form.update_data(user)

    return render_template("users/profile.html", edit_form=edit_form)


@blueprint.route("/edit/<name>",  methods=["GET", "POST"])
@login_required
@permission_required(Permission.UPDATE_USER)
def edit(name):
    user = User.query.filter_by(id=name).first()

    edit_form = EditForm()
    if edit_form.apply.data:
        if edit_form.validate():
            user.first_name = edit_form.firstname.data
            user.last_name = edit_form.lastname.data
            if user.email != edit_form.email.data:
                user.email_validated = False
            user.email = edit_form.email.data
            db.session.add(user)
            db.session.commit()
            if user == current_user:
                flash('Your profile has been updated', 'info')
                record_user('Update profile')
            else:
                flash('The profile of %s has been updated' % user.username,
                      'info')
                record_user('Update other user profile', acted_on=user)
        else:
            flash_errors(edit_form)
    edit_form.update_data(user)

    return render_template("users/profile.html", edit_form=edit_form)


@blueprint.route("/admin/<name>",  methods=["GET", "POST"])
@login_required
def admin(name):
    user = User.query.filter_by(id=name).first()

    admin_form = UserAdminForm(Role.list_of_role_names())

    if admin_form.apply.data:
        if admin_form.validate():
            if user.active != admin_form.active.data:
                user.active = admin_form.active.data
                if user.active:
                    description = 'Activate'
                else:
                    description = 'Deactivate'
                record_priviledge(user, description=description)
            else:
                record_priviledge(user)
            user.set_role(admin_form.role.data)
            db.session.add(user)
            db.session.commit()
        else:
            flash_errors(admin_form)
    admin_form.update_data(user)

    return render_template("users/admin.html", admin_form=admin_form)


@blueprint.route("/password",  methods=["GET", "POST"])
@login_required
def password():
    """
    Changing the password is only supported for the current user.
    """

    chpwd_form = ChangePasswordForm()
    if chpwd_form.setpwd.data:
        if chpwd_form.validate():
            current_user.set_password(chpwd_form.password.data)
            db.session.add(current_user)
            db.session.commit()
            record_authentication('Change password')
            flash('Your password has been updated', 'info')
        else:
            flash_errors(chpwd_form)
    chpwd_form.update_data(current_user)

    return render_template("users/password.html", chpwd_form=chpwd_form)


@blueprint.route("/token",  methods=["GET", "POST"])
@login_required
def token():
    """
    Manage the rest token
    """

    form = RestTokenForm()
    if form.generate.data:
        if form.validate():
            flash('Your token has been updated', 'info')
        else:
            flash_errors(form)
    expiry = time.time() + float(form.lifetime.data)
    form.expiry.data = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
    form.token.data = current_user.generate_auth_token(expiry)
    return render_template("users/token.html", token_form=form)
