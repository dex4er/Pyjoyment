import Pyjoyment.Plugin

import time


# The age of the moon in days, counted from a new moon in synodic months
def age(epoch):
    return (epoch - 947182440) / 86400 % 29.530588853


# Plugin
class Pyjoyment_Plugin_WerewolfCondition(Pyjoyment.Plugin.object):
    def register(self, app, conf):

        # Add "werewolf" condition
        def werewolf(route, c, captures, days):

            # Keep the werewolves out!
            if abs(14 - age(time.time())) > (days / 2):
                return None

            # It's ok, no werewolf
            return True

        app.routes.add_condition('werewolf', werewolf)


object = Pyjoyment_Plugin_WerewolfCondition
