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
  content = ""
  p = file(path, "rb")
  pdf = pyPdf.PdfFileReader(p)
  num_pages = pdf.getNumPages()
  for i in range(0, num_pages):
    pagecontent = pdf.getPage(i).extractText()
    content = content + pagecontent + " "
  return content

def seperatePDFContent(content):
  spaces = "\s+"
  seperatedContent = []
  subclasspat = "(Subclass\s+[A-Z]+)"
  subclassespat = "(Subclasses\s+[A-Z]+-[A-Z]+)"
  # subcontentpat takes care of classpat and all subcontentpat
  subcontentpat = "([A-Z]+\(?[0-9.A-Z]*\)?-?\(?[0-9.A-Z]*\)?\s)"
  # combine all patterns together
  combinedpat = "%s|%s|%s" %( subclasspat, subclassespat, subcontentpat)
  pattern = re.compile(combinedpat)
  contentsplit = pattern.split(content)
  k = 0
  foundclass = False
  while k < len(contentsplit):
    if not contentsplit[k]:
      contentsplit.pop(k)
    else:
      if not foundclass :
        if(re.match("CLASS\s",contentsplit[k])):
          seperatedContent.append("CLASS")
          k = k + 2
          theclass = getClass(contentsplit, k)
          seperatedContent.append(theclass[0])
          k = theclass[1]
          foundclass = True
        else :
          k = k + 1
      else :
        if re.match(subclasspat, contentsplit[k]) or re.match(subclassespat, contentsplit[k]):
          seperatedContent.append("Subclass")
          subclasscategory = getSubclassCat(contentsplit[k])
          seperatedContent.append(subclasscategory)
        elif re.match(subcontentpat, contentsplit[k]):
          getSubContent(contentsplit[k], seperatedContent)
        else :
          seperatedContent.append(re.sub(spaces," ",contentsplit[k]))
        k = k + 1
  return seperatedContent

def getClass(content, index):
  spaces= "\s+"
  classname = ""
  subclasspat = "Subclass\s+([A-Z]+)"
  subclassespat = "Subclasses\s+([A-Z]+)-[A-Z]+"
  while index < len(content):
    if not content[index] or re.sub(spaces, "" , content[index]):
      content.pop(index)
    else :
      if re.match(  subclasspat , content[index]) or re.match(subclassespat, content[index]):
        break
      classname = classname + content[index] + " "
      index = index  + 1
  return (classname, index)

def getSubclassCat(Subclass):
  cat = ""
  spaces = "\s+"
  subclasspat = "Subclass\s+([A-Z]+)"
  subclassespat = "Subclasses\s+([A-Z]+)-[A-Z]+"
  subclasscontent = re.split(subclasspat,Subclass)
  if len(subclasscontent)>1:
    cat = re.sub(spaces, " " ,subclasscontent[1])
  else :
    subclasscontent = re.split(subclassespat, Subclass)
    cat = re.sub(spaces, " " ,subclasscontent[1])
  return cat

def getSubContent(subcontent, incontent):
  spaces = "\s+"
  subcontentpat = "([A-Z]+)"
  subcontentnumpat = "\(?([0-9.]+)\)?\s"
  subcontentwdletrangepat = "([0-9.]+)."
  subcontentdivide = re.split(subcontentpat, subcontent)
  subcontentid = re.sub(spaces, " " , subcontent[1])
  incontent.append(subcontentid)
  indexofvalue = 2
  valuecontained = subcontentdivide[2]
  valueofsubcontent=re.split(subcontentnumpat, valuecontained)
  if(len(valueofsubcontent)<=1):
    valueofsubcontent = re.split(subcontentwdletrangepat, valuecontained)
  if(len(valueofsubcontent)>1):
    actualvalue = re.sub(spaces, " ",valueofsubcontent[1])
    incontent.append(actualvalue)
  return

def convert_pdf(path):
  pdfContent = getPDFContent(path)
  pdfdivided = seperatePDFContent(pdfContent)
  line = 0
  while line < len(pdfdivided) and pdfdivided[line]!="CLASS":
    line = line + 1
  # set to name of class
  line = line + 1
  topfoldername = ""
  if(line < len(pdfdivided)):
    topfoldername = pdfdivided[line]
    line = line + 1
    while line < len(pdfdivided) and (pdfdivided[line]!="Subclass" and pdfdivided[line]!="Subclasses"):
      topfoldername = topfoldername + " " + unicode(pdfdivided[line])
      print topfoldername
      line = line + 1
    topfolder = OrderedBTreeFolder(unicode(topfoldername))
  else :
    print "CLASS NOT FOUND IN PDF"
    sys.exit(1)
  # get the subclass section id
  while line < len(pdfdivided):
    line = findSubclass(topfolder, pdfdivided, line + 1)
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
    idofsubsection = unicode(content[line])
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
      if(leveloffolder + 1 < len(maxnum)):
        maxnum[leveloffolder + 1] = number
      else :
        maxnum.append(number)
    nameofsubsection = unicode(content[line])
    print "  " + unicode( " " * leveloffolder) + nameofsubsection
    line = line + 1
    subsection = OrderedBTreeFolder(nameofsubsection)
    leveloffolder = leveloffolder + 1
    if(leveloffolder == 1):
      # set the folder underneath the subclass
      subroot._setOb(subsection.id, subsection)
      while(leveloffolder >= len(folders)):
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
      while(leveloffolder >= len(folders)):
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
