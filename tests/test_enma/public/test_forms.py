# -*- coding: utf-8 -*-
import pytest

from enma.public.forms import LoginUserPasswordForm, \
    RegisterUserPasswordForm, RequestPasswordChangeForm


class TestRegisterForm:

    def test_validate_user_already_registered(self, user):
        # Enters username that is already registered
        # '%local' consists of 6 characters
        form = RegisterUserPasswordForm(username=user.username[:-6],
                                        email='foo@bar.com',
            password='example', confirm='example')
        assert form.validate() is False
        assert 'Username already registered' in form.username.errors

    def test_validate_success(self, db):
        form = RegisterUserPasswordForm(username='newusername',
                                        email='new@test.test',
            password='example', confirm='example')
        assert form.validate() is True


class TestLoginForm:

    def test_validate_success(self, user):
        user.active = True
        user.set_password('example')
        user.save()
        # '%local' consists of 6 characters
        form = LoginUserPasswordForm(username=user.username[:-6],
                                     password='example')
        assert form.validate() is True
        assert form.user == user

    def test_validate_unknown_username(self, db):
        form = LoginUserPasswordForm(username='unknown', password='example')
        assert form.validate() is False
        assert 'Unknown username' in form.username.errors
        assert form.user is None


    def test_validate_invalid_password(self, user):
        user.active = True
        user.set_password('example')
        user.save()
        # '%local' consists of 6 characters
        form = LoginUserPasswordForm(username=user.username[:-6],
                                     password='wrongpassword')
        assert form.validate() is False
        assert 'Invalid password' in form.password.errors

    def test_validate_inactive_user(self, user):
        user.active = False
        user.set_password('example')
        user.save()
        # Correct username and password, but user is not activated
        # '%local' consists of 6 characters
        form = LoginUserPasswordForm(username=user.username[:-6],
                                     password='example')
        assert form.validate() is False
        assert 'User not activated' in form.username.errors


class TestRequestPasswordChangeForm:

    def test_validate_username_unknown(self, user):
        # The user argument is required even if unused to have a propper
        # application environment
        form = RequestPasswordChangeForm(username='newusername')
        assert form.validate() is False
        assert 'Unknown username' in form.username.errors

    def test_validate_success(self, user):
        # Enters username that is already registered
        # '%local' consists of 6 characters
        form = RequestPasswordChangeForm(username=user.username[:-6])
        assert form.validate() is True