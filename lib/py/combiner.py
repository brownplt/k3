import os
import settings
from pyPdf import PdfFileWriter, PdfFileReader
from lib.py.tex import texEscape
import subprocess
import shutil
import tempfile

from resume.views import get_letter_filename, get_statement_filename, get_file_type

def append_files(out, filenames):
  for filename in filenames:
    path = os.path.join(settings.SAVEDFILES_DIR, filename)
    f = open(path, 'r')
    contents = f.read()
    if get_file_type(contents) == 'pdf':
      try:
        pdf = file(path, 'rb')
        reader = PdfFileReader(pdf)
        for pagenum in range(reader.getNumPages()):
          out.addPage(reader.getPage(pagenum))
      except Exception as e:
        raise Exception("Error (%s) when processing file %s" % (e, filename))

def get_rev_tex(rev):
  scores = rev.get_scores()
  def getAdv():
    if rev.advocate == 'comment':
      return ' (comment)'
    elif rev.advocate == 'advocate':
      return ' (advocate)'
    elif rev.advocate == 'detract':
      return ' (detract)'
    else:
      return ''
  def getRscores():
    if rev.advocate == 'comment' or len(scores) == 0:
      return ''
    else:
      return ', '.join(['%s: %d' % (texEscape(sc.value.category.shortform),sc.value.number) for sc in scores])
  return '{\\bf %s} %s %s\n\n%s\n\n' % (texEscape(rev.reviewer.auth.email), getRscores(), getAdv(), texEscape(rev.comments))

def get_combined_data(applicant):
  out = PdfFileWriter()

  cover_file = open(settings.COVER_TEMPLATE, 'r')
  coverTemplate = cover_file.read()
  tdir = tempfile.mkdtemp()
  cover_file.close()

  tfile = open(os.path.join(tdir,'o.tex'),'w')
  tfile.write(coverTemplate % (
    texEscape(applicant.fullname()), 
    texEscape(applicant.auth.email), 
    '\n\n'.join(['{\\bf %s:} %s' % (texEscape(c.type.name), texEscape(c.value)) 
      for c in applicant.get_component_objects() if c.type.type != 'statement']), 
    '\n\n'.join(texEscape(a['name']) for a in applicant.getAreas()), 
    '\n\\medskip\n'.join([get_rev_tex(rev) for rev in applicant.myReviews()])))
  tfile.close()

  os.system('pdflatex -output-directory %s %s' % (tdir, os.path.join(tdir,'o.tex')))
  review_pdf = PdfFileReader(file(os.path.join(tdir, 'o.pdf'), 'rb'))
  pagerange = range(1, review_pdf.getNumPages() + 1)
  for pagenum in range(review_pdf.getNumPages()):
    out.addPage(review_pdf.getPage(pagenum))

  submitted_refs = applicant.get_submitted_refs()
  ref_filenames = [get_letter_filename(r) for r in submitted_refs]
  append_files(out, ref_filenames)

  submissions = applicant.get_submitted_objects()
  stmt_filenames = [get_statement_filename(applicant, o.type) for o in submissions]
  append_files(out, stmt_filenames)

  # save combined PDF, open and read data, return data
  combined_path = os.path.join(settings.SAVEDFILES_DIR,\
    '%s-combined' % applicant.id)
  out_stream = file(combined_path, 'wb')
  out.write(out_stream)
  out_stream.close()

  combined = open(combined_path, 'r')
  contents = combined.read()
  return contents
