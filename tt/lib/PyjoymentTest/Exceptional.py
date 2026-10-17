import Pyjoyment.Controller


class PyjoymentTest_Exceptional(Pyjoyment.Controller.object):
    def this_one_dies(self):
        raise Exception('doh!\n')

    def this_one_might_die(self):
        if not self.req.headers.header('X-DoNotDie'):
            raise Exception('double doh!\n')
        return 1


object = PyjoymentTest_Exceptional
