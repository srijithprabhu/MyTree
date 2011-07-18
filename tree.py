import sys
import pyPdf
import re
from Products.orderedbtreefolder.orderedbtreefolder \
     import OrderedBTreeFolder
from Products.BTreeFolder2.BTreeFolder2 \
     import ExhaustedUniqueIdsError

def main(argv):
  convert_pdf(argv[1])

def getPDFContent(path):
  pdfpartition = []
  # patterns to look for
  subclasspat = "(Subclass)\s+([A-Z]+)"
  subclassespat = "(Subclasses)\s+[A-Z]+-([A-Z]+)"
  classpat = "\s+(CLASS)\s+[A-Z]+(-)\s*([A-Z\s]+)\s+"
  #section pattern without range (no dash) (number optional)
  sectworangepat = "\s+([A-Z]+)\(?(\d+)?\.?\d*?\)?\s+"
  #section pattern with range (with dash) (number not optional)
  sectwnumrangepat = "\s+([A-Z]+)\(?\d+\.?\d*\)?-\(?(\d+\.?\d*)\)?\s+"
  sectwnumletrangepat = "\s+([A-Z]+)(\d+)\.[A-Z]+-[A-Z]+\s+"
  sectwletrangepat = "\s+([A-Z]+)-[A-Z]+\s+"
  # pattern used to partition
  combinedpat= "%s|%s|%s|%s|%s|%s|%s" % ( sectworangepat, sectwletrangepat, sectwnumrangepat, sectwnumletrangepat, subclasspat, subclassespat, classpat)
  patpart = re.compile(unicode(combinedpat))
  p = file(path, "rb")
  pdf = pyPdf.PdfFileReader(p)
  num_pages = pdf.getNumPages()
  for i in range(0, num_pages):
    pagecontent = pdf.getPage(i).extractText()
    pagepartition = patpart.split(pagecontent)
    k = 0
    while k < len(pagepartition):
      #remove None and empty strings
      if not pagepartition[k]:
        pagepartition.pop(k)
      else :
        #replace multiple whitespaces with one whitespace
        pagepartition[k] = re.sub("\s+"," ", pagepartition[k])
        pdfpartition.append(pagepartition[k])
        k = k + 1
  return pdfpartition

def convert_pdf(path):
  pdfContent = getPDFContent(path)
  line = 0
  while line < len(pdfContent) and pdfContent[line]!="CLASS":
    line = line + 1
  # set to name of class
  while line < len(pdfContent) and pdfContent[line].find("-") == -1:
    line = line + 1
  line = line + 1
  topfoldername = ""
  if(line < len(pdfContent)):
    topfoldername = pdfContent[line]
    line = line + 1
    while line < len(pdfContent) and (pdfContent[line]!="Subclass" and pdfContent[line]!="Subclasses"):
      topfoldername = topfoldername + " " + unicode(pdfContent[line])
      print topfoldername
      line = line + 1
    topfolder = OrderedBTreeFolder(unicode(topfoldername))
  else :
    print "CLASS NOT FOUND IN PDF"
    sys.exit(1)
  # get the subclass section id
  while line < len(pdfContent):
    line = findSubclass(topfolder, pdfContent, line + 1)
  return

def findSubclass(root, content, line):
  # get id of subclass
  subclassid = unicode(content[line])
  line = line + 1
  # get id of line following subclass
  if(unicode(content[line]).startswith(subclassid)):
    line = line + 1
    idnumorstring = unicode(content[line])
    if(idnumorstring.replace(".","").isdigit()):
      line = line + 1
  subclassname = unicode(content[line])
  print " " + subclassname
  subclassfolder = OrderedBTreeFolder(subclassname)
  try:
    root._setOb(subclassfolder.id, subclassfolder)
  except KeyError:
    subclassfolder = root._getOb(subclassfolder.id)
  line = getContentsofSubclass(subclassfolder, content, line + 1)
  return line

def getContentsofSubclass(subroot, content, line):
  # keep track of how far in the subsection we are
  leveloffolder = 0
  # keep track of what the currentid and maxnum is at each subsection
  ids = [unicode(content[line])]
  maxnum = [0]
  folders = []
  while line + 1 < len(content) and (content[line]!="Subclass" and content[line]!="Subclasses"):
    # get id, number(optional), and name of subsection
    idofsubsection = content[line]
    line = line + 1
    idnumorstring = unicode(content[line])
    if(idnumorstring.replace(".","").isdigit()):
      line = line + 1
      number = float(idnumorstring)
      # go until the subsection starts with the id of the parent
      while leveloffolder > 0 and not idofsubsection.startswith(ids[leveloffolder]):
        leveloffolder = leveloffolder - 1
      while leveloffolder > 0 and maxnum[leveloffolder]<number and idofsubsection.startswith(ids[leveloffolder]):
        leveloffolder = leveloffolder - 1
      if(leveloffolder + 1 >= len(maxnum)):
        maxnum.append(number)
      else :
        maxnum[leveloffolder + 1] = number
    nameofsubsection = unicode(content[line])
    print "  " + unicode( " " * leveloffolder) + nameofsubsection
    line = line + 1
    subsection = OrderedBTreeFolder(nameofsubsection)
    leveloffolder = leveloffolder + 1
    if(leveloffolder == 1):
      # set the folder underneath the subclass
      subroot._setOb(subsection.id, subsection)
      if(leveloffolder >= len(folders)):
        folders.append(subsection)
        ids.append(idofsubsection)
      else :
        folders[leveloffolder]= subsection
        ids[leveloffolder]=idofsubsection
      while leveloffolder>=len(maxnum):
        maxnum.append(0)
      
    else :
      # set folder underneath subsection
      parent = folders[leveloffolder-1]
      if(leveloffolder >= len(folders)):
        folders.append(subsection)
        ids.append(idofsubsection)
      else :
        folders[leveloffolder]= subsection
        ids[leveloffolder] = idofsubsection
      parent._setOb(subsection.id, subsection)
      while leveloffolder>=len(maxnum):
        maxnum.append(0)
    

  return line

if __name__ == '__main__': sys.exit(main(sys.argv))
