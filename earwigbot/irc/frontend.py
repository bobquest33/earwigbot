# -*- coding: utf-8  -*-
#
# Copyright (C) 2009-2012 by Ben Kurtovic <ben.kurtovic@verizon.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from earwigbot.irc import IRCConnection, Data

__all__ = ["Frontend"]

class Frontend(IRCConnection):
    """
    **EarwigBot: IRC Frontend Component**

    The IRC frontend runs on a normal IRC server and expects users to interact
    with it and give it commands. Commands are stored as "command classes",
    subclasses of :py:class:`~earwigbot.commands.Command`. All command classes
    are automatically imported by :py:meth:`commands.load()
    <earwigbot.managers._ResourceManager.load>` if they are in
    :py:mod:`earwigbot.commands` or the bot's custom command directory
    (explained in the :doc:`documentation </customizing>`).
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger.getChild("frontend")

        cf = bot.config.irc["frontend"]
        base = super(Frontend, self)
        base.__init__(cf["host"], cf["port"], cf["nick"], cf["ident"],
                      cf["realname"])
        self._connect()

    def _process_message(self, line):
        """Process a single message from IRC."""
        if line[1] == "JOIN":
            data = Data(self.bot, self.nick, line, msgtype="JOIN")
            self.bot.commands.call("join", data)

        elif line[1] == "PRIVMSG":
            data = Data(self.bot, self.nick, line, msgtype="PRIVMSG")
            if data.is_private:
                self.bot.commands.call("msg_private", data)
            else:
                self.bot.commands.call("msg_public", data)
            self.bot.commands.call("msg", data)

        elif line[1] == "376":  # On successful connection to the server
            # If we're supposed to auth to NickServ, do that:
            try:
                username = self.bot.config.irc["frontend"]["nickservUsername"]
                password = self.bot.config.irc["frontend"]["nickservPassword"]
            except KeyError:
                pass
            else:
                msg = "IDENTIFY {0} {1}".format(username, password)
                self.say("NickServ", msg, hidelog=True)

            # Join all of our startup channels:
            for chan in self.bot.config.irc["frontend"]["channels"]:
                self.join(chan)
