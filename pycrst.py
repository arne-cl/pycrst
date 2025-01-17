## pycrst 1.0
## An Algorithm for Pythonizing Rhetorical Structures
## Andrew Potter
## 6/8/2023
## 8/14/2023 bug fixes, integration of convergence into main function
'''
Current reference if citing this work:
Potter, A. (Accepted). An algorithm for pythonizing rhetorical structures. In DiSLiDaS 2023. 

Some assumptions, limitations, caveats
Hyphenated relation names are converted to snake format.
It is assumed that every text will contain at least one relation.
Some discontinuitites and span anomalies are detected.
Input files must be on local drive in rstfiles subfolder.
'''

from inspect import currentframe
import xml.etree.ElementTree as ET
import re
import sys
from pcpp import pcpp
debugging = False

# Uncomment input file of interest
# selected classics and miscellaneous
rstFile = './rstFiles/ccletter.rs3'
#rstFile = './rstFiles/australianmining.rs3'
#rstFile = './rstFiles/dioxin.rs3'
#rstFile = './rstFiles/emeritiCommittee.rs3'
#rstFile = './rstFiles/musicdayannouncement.rs3'
#rstFile = './rstFiles/syncom.rs3'
#rstFile = './rstFiles/taxprogram.rs3'
#rstFile = './rstFiles/truebrit.rs3'
#rstFile = './rstFiles/unlazy.rs3'
#rstFile = './rstFiles/zpg.rs3' # discontinuity OK, see unconnected segs 1-4
#rstFile = './rstFiles/Gettysburg Address.rs3'

# STS Corpus
#rstFile = './rstFiles/sts corpus/STS-Nov-M133-Fuller.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M148-Lynch.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M134-Herkert.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M149-Hakken.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M134a-Hakken.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M150-Fuller.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M135-Traweek.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M151-Holmes.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M136-Lynch.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M152-Shapiro.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M137-Lynch.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M153-Hess.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M138-Hess.rs3'
#rstFile = './rstFiles/sts corpus/STS-Oct-M1-Hamlett.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M139-Weinstein.rs3'
#rstFile = './rstFiles/sts corpus/STS-Oct-M2-Fuller.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M140-Fuller.rs3'
#rstFile = './rstFiles/sts corpus/STS-Oct-M3-Busch.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M141-Durbin.rs3'
#rstFile = './rstFiles/sts corpus/STS-Oct-M4-Morman.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M143-Bailar.rs3'
#rstFile = './rstFiles/sts corpus/STS-Oct-M5-Bouzid.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M144-Hess.rs3'
#rstFile = './rstFiles/sts corpus/STS-Oct-M6-Lieberman.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M145-Edwards.rs3'
#rstFile = './rstFiles/sts corpus/STS-Oct-M7-Eglash.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M146-La Porte.rs3'
#rstFile = './rstFiles/sts corpus/STS-Oct-M8-Miller.rs3'
#rstFile = './rstFiles/sts corpus/STS-Nov-M147-Schmaus.rs3'
#rstFile = './rstFiles/sts corpus/STS-Oct-M9-Baxter.rs3'

# selected GUM
#rstFile = './rstFiles/GUM/GUM_news_worship.rs3'
#rstFile = './rstFiles/GUM/GUM_news_worship_2.rs3'
#rstFile = './rstFiles/GUM/GUM_academic_census.rs3'
          
##################################################################
## relational proposition, generally known as rp
class RelProp:
    def __init__(self, rel, sat, nuc, type, text):
        self.rel = rel
        self.sat = sat
        self.nuc = nuc
        self.type = type
        self.text = text.strip() if text else ""

########################################
## load RST file, initialize rplist
def initialize(rstFile):

    global top
    global rplist

    print(rstFile)
    
    xmlroot = ET.parse(rstFile).getroot()

    header = xmlroot.find('header')
    relations = header.find('relations')
    relList = relations.findall('rel')

    for rel in relList:             # make list of all multinuc predicates
        type = rel.get('type')
        if type == 'multinuc':
            name = snakify(rel.get('name'))
            multinucs.append(name)

    body = xmlroot.find('body')
    spanList = body.findall('segment') + body.findall("group")
    
    for rp in spanList:
        rel = snakify(rp.get('relname'))
        sat = rp.get('id')
        nuc = rp.get('parent')
        type = rp.get('type')
        if not type: type = 'segment'
        text = rp.text
        rplist.append(RelProp(rel,sat,nuc,type,text))

    for rp in rplist:
        if rp.nuc == None:
            top = rp
            rp.rel = "top"
            rp.nuc = ""
    
    rplist = renumber(rplist)
    return top


########################################
# Transform RST to RP 

def gen_exp(rp):
    
    if rp.rel == 'top' and rp.type == 'span':    
        exp = gen_exp(get_nuc(rp.sat))
        
    elif rp.type == 'span':
        nuc_exp = gen_exp(get_span_nuc(rp))
        if get_sat_count(rp) > 1:   # converge
            exp_list = []
            children = get_children(rp)
            for child in children:
                if child.rel != 'span':
                    if child.type == 'span':
                        child.nuc = nuc_exp
                        exp_list.append(gen_exp(child))
                    elif child.type == 'multinuc':
                        child.nuc = nuc_exp
                        exp_list.append(format_rp(child.rel, gen_exp(child), child.nuc))
                    elif child.type == 'segment':
                        child.nuc = nuc_exp
                        exp_list.append(format_rp(child)) 
                
            exp = 'convergence(' + ','.join(exp_list) + ')'

        else:
            sat = get_sat(rp)
            if sat:
                if sat.type == 'multinuc':
                    sat.nuc = nuc_exp
                    exp = format_rp(sat.rel,gen_exp(sat),nuc_exp)
                else:
                    sat_rp = get_span_nuc(sat)
                    if sat_rp:
                        sat.sat = gen_exp(sat_rp)
                    exp = format_rp(sat.rel, sat.sat, nuc_exp)
            else:
                exp = format_rp(rp.rel, nuc_exp, rp.nuc)

    elif rp.type == 'segment':
        if get_sat_count(rp) > 1:   # converge
            exp_list = []
            children = get_children(rp)
            for child in children:
                if child.type == 'multinuc':
                    exp = format_rp(child.rel, gen_exp(child), child.nuc)
                elif child.type == 'span':
                    exp = gen_exp(child)
                else:
                    exp = format_rp(child)
                exp_list.append(exp)
            exp = 'convergence(' + ','.join(exp_list) + ')'
        else:
            sat = get_sat(rp)
            if not sat:
                exp = format_rp(rp)
            elif sat.type == 'multinuc':
                exp = format_rp(sat.rel, gen_exp(sat), rp.sat)
            else:
                exp = gen_exp(sat)

    elif rp.type == 'multinuc':
        nucs = get_mn_nucs(rp)       
        nuc_exp_lst = []            # create list of nuclei rps
        for n in nucs:
            if n.type == 'span':
                nuc_exp_lst.append(gen_exp(get_children(n)[0]))
            elif n.type == 'multinuc':  # multinuc within multinuc
                nuc_exp_lst.append(gen_exp(n))
            else:
                nuc_exp_lst.append(n.sat)

        nuc_exp_lst = sort_nucs(nuc_exp_lst)
        exp = '{}({})'.format(nucs[0].rel, ','.join(nuc_exp_lst))
        
        mn_sats = get_mn_sats(rp)   # get sats for mn, if any
        
        if len(mn_sats) == 1:
            mn_sats[0].nuc = exp
            if mn_sats[0].type == 'segment':
                exp = format_rp(mn_sats[0])
            else:
                exp = gen_exp(mn_sats[0])
                if not mn_sats[0].type == 'span':
                    mn_sats[0].sat = exp
                    exp = format_rp(mn_sats[0])

        elif len(mn_sats) > 1:  # converge
            sat_exp_lst = []
            for r in mn_sats:
                r.nuc = exp
                if r.type == 'multinuc':
                    sat_exp_lst.append(format_rp(r.rel, gen_exp(r), r.nuc))
                else: 
                    sat_exp_lst.append(gen_exp(r))
            exp = 'convergence(' + ','.join(sat_exp_lst) + ')'

    debug(exp)
    return exp

###############################################################
# print debug when turned on
def debug(*arg):
    if debugging:
        frameinfo = currentframe()
        print(frameinfo.f_back.f_lineno,":",*arg)
        input()

## miscellaneous
def is_span_type(rp): return rp.type == 'span'
def is_multi_type(rp): return rp.type == 'multinuc'
def is_segment(rp): return rp.type == 'segment'
def is_multi_rel(rp): return rp.rel in multinucs
def is_top(rp): return rp.rel == 'top'
def snakify(s): return s.replace('-','_') if s else s
rplist = []
top = None
multinucs = []

########################################
## sequentialize segment numbering
def renumber(rplist):
    old_nums = []
    for rp in rplist:
        old_nums.append(int(rp.sat))
        
    new_nums = [item for item in range(1, len(rplist) + 1)]
    for rp in rplist:
        if rp.rel == 'top':
            rp.sat = str(new_nums[old_nums.index(int(rp.sat))])
        else:
            rp.sat = str(new_nums[old_nums.index(int(rp.sat))])
            rp.nuc = str(new_nums[old_nums.index(int(rp.nuc))])
    return rplist

########################################
# format rp as pythonic expression
def format_rp(*rp):

    rpexp = "{}({},{})"
    
    if len(rp) == 1:
        return rpexp.format(rp[0].rel,rp[0].sat,rp[0].nuc)
    elif len(rp) == 3:
        return rpexp.format(rp[0],rp[1],rp[2])
    
########################################
# get the nucs for a multiuclear type rp  
def get_mn_nucs(rp):
    mn_nucs = []
    children = get_children(rp)
    for child in children:
        if is_multi_rel(child):
            mn_nucs.append(child)
    return mn_nucs

########################################
#get the sats for a multiuclear type rp
def get_mn_sats(rp):
    mn_sats = []
    children = get_children(rp)
    for child in children:
        if not is_multi_rel(child): 
            mn_sats.append(child)
    return mn_sats

########################################
# Sort the nucs in multinuclear expression
def sort_nucs(nuc_exp_lst):

    mn_dict = {}
    for exp in nuc_exp_lst:
        temp = re.findall(r'\d+', exp)
        mn_dict[int(temp[0])] = exp

    myKeys = sorted(list(mn_dict.keys()))
    mn_dict = {i: mn_dict[i] for i in myKeys}

    nuc_exp_lst = []
    for key in myKeys:
        nuc_exp_lst.append(mn_dict.get(key))

    return nuc_exp_lst

########################################
# get the nucleus associated with an rp
def get_nuc(nucid):
    for rp in rplist:
        if nucid == rp.nuc:
            return rp
    debug("get_nuc not found", nucid)
    return None

########################################
# get all rps linking to an rp 
def get_children(rp):
    children = []
    for r in rplist:
        if r.nuc == rp.sat:
            children.append(r)
    return children

########################################
# get the span relation linking to an rp, if any
def get_span_nuc(rp):
    children = get_children(rp)
    for child in children:
        if child.rel == 'span':
            return child
    return False

########################################
# get the number of satellites linking to an rp
def get_sat_count(rp):
    satcount = 0
    children = get_children(rp)
    for child in children:
        if child.rel != 'span':
            satcount += 1
    return satcount

########################################
# get the (solitary) sat linking to an rp
def get_sat(rp):
    children = get_children(rp)    
    for child in children:
        if child.rel != 'span': 
            return child
    return False

########################################
#look for dropped units or unprocessed spans
def check_continuity(exp):
    segnums = list(set(sorted(map(int, re.findall('\d+', exp)))))
    count = 1
    continuity = True
    for i in segnums:
        if i != count:
            continuity = False
            print('discontinuity at segment', i, 'count',count)
        count += 1
    return continuity
########################################
# check for presence of span relations in expression
def span_check(exp):
    return 'span' in exp

########################################    
# run it
top = initialize(rstFile)
exp = gen_exp(top)
print(exp)
print()
print(__file__)
print(rstFile)
print(pcpp(exp))
print()
if check_continuity(exp): print('Continuity complete')
if span_check(exp):
    print("Span check error")
else:
    print("Span check OK")
