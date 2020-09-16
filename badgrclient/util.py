import functools


def eid_required(func):
    @functools.wraps(func)
    def check_id(self, *args, **kwargs):
        if self.entityId:
            return func(self, *args, **kwargs)
        else:
            raise Exception("entityId is required for this operation")

    return check_id
