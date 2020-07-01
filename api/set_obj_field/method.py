import jrlib
from jrlib import fields


class UserProfile(fields.ObjField):
    first_name = fields.CharField(required=True)
    last_name = fields.CharField()

    def validate(self):
        print('UUUUUUUUUUUUU')
        print(self.first_name)
        print(self.last_name)


class SetObjField(jrlib.Method):
    user_id = fields.IntField(required=True)
    user_profile = UserProfile()

    def validate(self):
        # print(self.user_profile)
        if self.user_id == 333:
            raise ValueError('error 333!!!!')

    def execute(self):
        # return {'user_id': self.user_id,
        #         'profile': self.user_profile}
        print('sss')
        print(self.user_profile.first_name)
        print(self.user_profile.last_name)
        print('eee')
        return {
            'user_id': self.user_id,
            'user_profile': {
                # 'first_name': self.user_profile.first_name,
                'last_name': self.user_profile.last_name,
                'value': self.user_profile.value,
                'required': self.user_profile.required,
            }
        }
