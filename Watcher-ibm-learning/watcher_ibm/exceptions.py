class RobotException(Exception):
    """
    You have been identified as a robot on Udemy site
    """

    pass


class LoginException(Exception):
    """
    You have failed to login to the Udemy site
    """

    pass


class CourseNotFoundException(Exception):
    """
       You have failed to find the course id
    """

    def getExitCode(self):
        "meant to be overridden in subclass"
        return -2
