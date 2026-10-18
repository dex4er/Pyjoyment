from Pyjo.Util import secure_compare


USERS = {'joel': 'las3rs', 'marcus': 'lulz', 'sebastian': 'secr3t'}


class Users:
    def check(self, user, password):
        # Success
        if user in USERS and secure_compare(USERS[user], password):
            return True

        # Fail
        return False
