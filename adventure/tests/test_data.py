import unittest

class FooTest(unittest.TestCase):

    def setUp(self):
        from adventure.data import Data
        from adventure.interpret import read_data_from_nearby_file
        self.data = Data()
        read_data_from_nearby_file(self.data)

    def test_long_description(self):
        self.assertEqual(self.data.rooms[4].long_description, u"""\
YOU ARE IN A VALLEY IN THE FOREST BESIDE A STREAM TUMBLING ALONG A
ROCKY BED.
""")

    def test_long_description_expands_tabs(self):
        self.assertIn(u"ALMOST AS IF ALIVE.  A COLD WIND BLOWS",
                      self.data.rooms[15].long_description)

    def test_short_description(self):
        self.assertEqual(self.data.rooms[4].short_description,
                         u"YOU'RE IN VALLEY.\n")

    def test_object_message_expands_tabs(self):
        self.assertEqual(self.data.objects[24].messages[5], u"""\
YOU'VE OVER-WATERED THE PLANT!  IT'S SHRIVELING UP!  IT'S, IT'S...
""")

    def test_hint(self):
        hint = self.data.hints[4]
        self.assertEqual(hint.turns, 4)
        self.assertEqual(hint.penalty, 2)
        self.assertEqual(hint.question.text,
                         u"ARE YOU TRYING TO GET INTO THE CAVE?\n")
        self.assertEqual(hint.message.text, u"""\
THE GRATE IS VERY SOLID AND HAS A HARDENED STEEL LOCK.  YOU CANNOT
ENTER WITHOUT A KEY, AND THERE ARE NO KEYS NEARBY.  I WOULD RECOMMEND
LOOKING ELSEWHERE FOR THE KEYS.
""")
