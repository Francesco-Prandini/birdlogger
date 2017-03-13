#authentication imports
from webapp2_extras import auth


class Authentication(auth.Auth):
    def login(self, auth_id, remember=False,
                             save_session=True, silent=False):
        """Returns a user based on password credentials.

        :param auth_id:
            Authentication id.
        :param remember:
            If True, saves permanent sessions.
        :param save_session:
            If True, saves the user in the session if authentication succeeds.
        :param silent:
            If True, raises an exception if auth_id or password are invalid.
        :returns:
            A user dict or None.
        :raises:
            ``InvalidAuthIdError`` or ``InvalidPasswordError``.
        """
        if save_session:
            # During a login attempt, invalidate current session.
            self.unset_session()

        self._user = self.store.user_model.get_by_auth_id(auth_id)
        if not self._user:
            self._user = auth._anon
        elif save_session:
            # This always creates a new token with new timestamp.
            self._user=self.store.user_to_dict(self._user)
            self.set_session(self._user, remember=remember)

        return self._user_or_none()


def get_auth(request=None):
    return auth.get_auth(factory=Authentication,request=request)
    pass
