import cStringIO, Texml.texmlwr

# From http://uucode.com/blog/2008/10/17/escape-a-tex-string-in-python/
class TexEscape:
  def __init__(self):
    self.stream = cStringIO.StringIO()
    self.texmlwr = Texml.texmlwr.texmlwr(self.stream, 'utf-8', '72')
  def escape(self, s):
    self.texmlwr.write("x\n")
    self.stream.truncate(0)
    self.texmlwr.write(s)
    return self.stream.getvalue()
  def free(self):
    self.stream.close()

def texEscape(str):
  e = TexEscape()
  result = e.escape(str)
  e.free() # garbage collection?
  return result
