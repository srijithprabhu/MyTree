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
  subclasspat = ur"(Subclass\s+[A-Z]+)"
  subclassespat = ur"(Subclasses\s+[A-Z]+-[A-Z]+)"
  # subcontentpat takes care of classpat and all subcontentpat lookbehind for special cases
  subcontentpat = ur"(?<!\ssee\s|....[A-Z\-(]|...,\s)([A-Z]+\(?[0-9.A-Z]*\)?-?\(?[0-9.A-Z]*\)?\s)"
  # combine all patterns together
  combinedpat = ur"%s|%s|%s" %( subclasspat, subclassespat, subcontentpat)
  pattern = re.compile(combinedpat)
  contentsplit = pattern.split(content)
  k = 0
  foundclass = False
  while k < len(contentsplit):
    if not contentsplit[k] or not re.sub(spaces, "" , contentsplit[k]):
      contentsplit.pop(k)
    else:
      if not foundclass :
        if(re.match("CLASS\s",contentsplit[k])):
          seperatedContent.append("CLASS")
          while k<len(contentsplit) :
            if contentsplit[k] and re.match("\s*-\s*",contentsplit[k]):
              break
            k = k + 1
          theclass = getClass(contentsplit, k + 1)
          seperatedContent.append(re.sub(spaces, " " ,theclass[0]))
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
          seperatedContent.append(re.sub(spaces," ",contentsplit[k]).strip())
        k = k + 1
  return seperatedContent

def getClass(content, index):
  spaces= "\s+"
  classname = ""
  subclasspat = "Subclass\s+([A-Z]+)"
  subclassespat = "Subclasses\s+([A-Z]+)-[A-Z]+"
  while index < len(content):
    if not content[index] or not re.sub(spaces, "" , content[index]):
      content.pop(index)
    else :
      if re.match(subclasspat , content[index]) or re.match(subclassespat, content[index]):
        break
      classname = classname + content[index] + " "
      index = index  + 1
  return (classname, index)

def getSubclassCat(Subclass):
  cat = ""
  spaces = "\s+"
  subclasspat = "Subclass\s+([A-Z]+)"
  subclassespat = "Subclasses\s+[A-Z]+-([A-Z]+)"
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
  subcontentnumpat = "\(?([0-9.]+)\)?\s+"
  subcontentwdletrangepat = "([0-9.]+)."
  subcontentdivide = re.split(subcontentpat, subcontent)
  subcontentid = re.sub(spaces, " " , subcontentdivide[1])
  incontent.append(subcontentid)
  indexofvalue = 2
  valuecontained = subcontentdivide[2]
  if(valuecontained=="-"):
    incontent.append(subcontentdivide[3])
    return
  valueofsubcontent=re.split(subcontentnumpat, valuecontained)
  if(len(valueofsubcontent)<=1):
    valueofsubcontent = re.split(subcontentwdletrangepat, valuecontained)
  if(len(valueofsubcontent)>1):
    actualvalue = re.sub(spaces, "",valueofsubcontent[1])
    incontent.append(actualvalue)
  else :
    incontent.append(subcontentdivide[1])
  return

def convert_pdf(path):
  pdfContent = getPDFContent(path)
  pdfdivided = seperatePDFContent(pdfContent)
  index = 1
  if(len(pdfdivided)>1):
    classname = pdfdivided[index]
    rootfolder = OrderedBTreeFolder(classname)
    index = index + 2
    while index<len(pdfdivided):
      index = findSubclass(rootfolder, pdfdivided, index)
  return

def findSubclass(root, content, line):
  lowercase = "[a-z]"
  # get id of subclass
  subclassid = unicode(content[line])
  line = line + 1
  # get id of line following subclass
  if not re.search(lowercase, content[line]):
    line = line + 2
  subclassname = unicode(content[line])
  print "  " + subclassname
  subclassfolder = OrderedBTreeFolder(subclassname)
  try:
    root._setOb(subclassfolder.id, subclassfolder)
  except KeyError:
    subclassfolder = root._getOb(subclassfolder.id)
  line = getContentsofSubclass(subclassfolder, content, line + 1)
  return line

def getContentsofSubclass(subroot, content, line):
  # keep track of ids and folders and maxnum at each level of folder
  numpat = "[0-9.]+"
  maxnums = [999999]
  ids = [subroot.id]
  folders = [subroot]
  line = line + 1
  if((re.sub("\.", "",content[line])).isnumeric()):
    maxnums.append(float(content[line]))
    ids.append(content[line-1])
  else:
    ids.append(content[line])
    maxnums.append(999999)
  line = line + 1
  tempfolder = OrderedBTreeFolder(content[line])
  subroot._setOb(tempfolder.id, tempfolder)
  folders.append(tempfolder)
  line = line + 1
  leveloffolder = 1
  while line < len(content) and content[line]!="Subclass":
    currentid = content[line]
    while leveloffolder>0 and ( not currentid.startswith(ids[leveloffolder]) and currentid > ids[leveloffolder]):
      leveloffolder = leveloffolder - 1
    line = line + 1
    number = 999999
    if re.match(numpat,content[line]):
      number = float(content[line])
      while leveloffolder>0 and currentid.startswith(ids[leveloffolder]) and maxnums[leveloffolder] < number:
        leveloffolder = leveloffolder - 1
    else:
      currentid = content[line]
    line = line + 1
    nameoffolder = content[line]
    print "  " + unicode("  " * leveloffolder) + nameoffolder
    tempfolder = OrderedBTreeFolder(nameoffolder)
    parentfolder = folders[leveloffolder]
    parentfolder._setOb(tempfolder.id, tempfolder)
    leveloffolder = leveloffolder + 1
    if(leveloffolder >= len(folders)):
      folders.append(tempfolder)
      ids.append(currentid)
      maxnums.append(number)
    else:
      folders[leveloffolder] = tempfolder
      ids[leveloffolder] = currentid
      maxnums[leveloffolder] = number
    line = line + 1
    
  return line + 1

if __name__ == '__main__': sys.exit(main(sys.argv))
