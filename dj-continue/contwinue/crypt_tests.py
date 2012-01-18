from belaylibs.cryptcaps import Crypt
from contwinue.tests_common import Generator
import belaylibs.dj_belay as bcap

class TestEnDecrypt(Generator):
  def setUp(self):
    self.crypt = Crypt()
    super(TestEnDecrypt, self).setUp()

  def roundtrip(self, data):
    encrypted = self.crypt.prepare(bcap.dbPreProcess(data))
    decrypted = bcap.dbPostProcess(self.crypt.unprepare(encrypted))
    self.assertEqual(decrypted, data)

  def test_structure_with_db(self):
    self.roundtrip({
      'conference': self.conference.grantable_ptr,
      'otherstuff': 22,
      'moredata': 'an even longer string'
    })

  def test_just_db(self):
    self.roundtrip(self.conference.grantable_ptr)

  def test_number(self): self.roundtrip(4)

  def test_string(self): self.roundtrip('foo')

  def test_unicode(self): self.roundtrip(u"\u03BB")

  def test_list(self): self.roundtrip([u'\u03BB', 45, 3.111111])

  def test_empty_list(self): self.roundtrip([])

  def test_empty(self): self.roundtrip("")

  def test_longish(self):
    self.roundtrip({
      'this                       ': 'object          ',
      'is                       ': 'a                     ',
      'long           ': ['s','t','r','i','n','g']
    })


