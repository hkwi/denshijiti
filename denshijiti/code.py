
# coding: utf-8

# 「標準地域コード」の助けを借りつつ、「全国地方公共団体コード」の RDF を生成する。

# In[1]:

import pandas as pd
import numpy as np
import rdflib
import datetime
import re
import lxml.html
import rdflib
import math
import os.path
import urllib.parse
import jaconv


# In[2]:

from rdflib.namespace import RDF, RDFS, DCTERMS
SACS = rdflib.Namespace("http://data.e-stat.go.jp/lod/terms/sacs#")
JITI = rdflib.Namespace("http://hkwi.github.com/denshijiti/#")
JITIS = rdflib.Namespace("http://hkwi.github.com/denshijiti/terms#")
IC = rdflib.Namespace("http://imi.ipa.go.jp/ns/core/rdf#")


# e-stat「標準地域コード」を取り込む。http://data.e-stat.go.jp/lodw/rdfschema/downloadfile/

# In[3]:

estat = rdflib.Graph()
estat.load("http://data.e-stat.go.jp/lodw/download/rdfschema/StandardAreaCode.ttl", format="turtle")


# 現在の excel を収集する。

# In[4]:

p = lxml.html.parse("http://www.soumu.go.jp/denshijiti/code.html")
r = p.getroot()
r.make_links_absolute()
for h in r.xpath("//h3"):
    if h.text.find("都道府県コード") >= 0:
        for l in h.xpath("following-sibling::node()//li"):
            if l.text.find("改正一覧") >= 0:
                for a in l.xpath("self::node()//a/@href"):
                    if a.lower().endswith(".xls"):
                        clist_hist = a
                        break
            else:
                for a in l.xpath("self::node()//a/@href"):
                    if a.lower().endswith(".xls"):
                        clist = a
                        break


# まず過去履歴を集める

# In[5]:

x = pd.read_excel(clist_hist, skiprows=1, header=[0,1,2])
x.columns=[
    "a","b","c","都道府県名",
    "改正前コード","改正前市区町村名","改正前市区町村名ふりがな",
    "改正区分","改正年月日",
    "改正後コード","改正後市区町村名","改正後市区町村名ふりがな",
    "事由等"
]
x.index = range(len(x.index))


# In[6]:

asub = x["改正前市区町村名"].str.extract(r"^[\(（](.*)[\)）]$", expand=False)
bsub = x["改正後市区町村名"].str.extract(r"^[\(（](.*)[\)）]$", expand=False)
ks = ["都道府県名", "改正前コード", "改正区分", "改正年月日", "改正後コード"]
x2 = x[asub.isnull() & bsub.isnull() & x[ks].notnull().any(axis=1)].assign(asub=None, bsub=None)
for i,d in asub[asub.notnull()].iteritems():
    x2.loc[i-1, "asub"] = d
for i,d in asub[bsub.notnull()].iteritems():
    x2.loc[i-1, "bsub"] = d

x2.index = range(len(x2.index))


# In[7]:

for ri,r in x2.iterrows():
    for ci,c in r.iteritems():
        if c=="〃":
            x2.loc[ri, ci] = x2.loc[ri-1, ci]


# In[8]:

cids = []
cid = 0
t = x2.assign(u=lambda o: o["都道府県名"].notnull())
for ri, r in x2.iterrows():
    if not isinstance(r["都道府県名"], float):
        cid += 1
    cids.append(cid)


# In[9]:

dts = []
t = pd.concat([x2, pd.Series(cids, name="cid"), pd.Series(None, name="date")], axis=1)
for i in range(cid):
    u = t[(t["cid"]==i+1) & t["改正年月日"].notnull()]
    assert len(set(u["改正年月日"]))==1, u.to_csv()
    for d in set(u["改正年月日"]):
        if isinstance(d, datetime.datetime):
            dt = d.date()
        elif isinstance(d, datetime.date):
            dt = d
        else:
            m = re.match(r"H(\d{2})\.(\d+)\.(\d+)", d)
            dt = datetime.date(2000+int(m.group(1))-12, int(m.group(2)), int(m.group(3)))
    for ri,r in t[(t["cid"]==i+1)].iterrows():
        t.loc[ri,"date"] = dt


# In[10]:

g = rdflib.Graph()
g.bind("ic", IC)
g.bind("jiti", JITI)
g.bind("jitis", JITIS)
g.bind("dcterms", DCTERMS)

for cls in ("StandardAreaCode", "CodeSet", "CodeChangeEvent"):
    g.add((JITIS[cls], RDF.type, RDFS["Class"]))

g.add((JITIS["StandardAreaCode"], RDFS.subClassOf, IC["住所"]))

def get_code(code_like):
    code = "%06d" % int(code_like)
    assert code_checksum(code) == code[5:], "code %s checksum error" % code
    return code

def code_checksum(code):
    s = np.array([int(s) for s in code[:5]]) * np.array([6,5,4,3,2])
    return str(11 - s.sum() % 11)[-1]

def get_code_id(url_like):
    m = re.search(r"C(?P<code>\d{5})-(?P<ymd>\d{8})$", url_like)
    assert m, "code_id %s format error" % url_like
    return m.group(0)

class Code(object):
    def __init__(self, code_id):
        m = re.match(r"C(?P<code>\d{5})-(?P<ymd>\d{8})$", code_id)
        assert m, "code %s format error" % code_id
        self.code = m.group("code")
        self.csum = code_checksum(self.code)
        
        # e-Stat LOD 準拠
        self.sac = JITI[code_id]
        g.add((self.sac, RDF["type"], JITIS["StandardAreaCode"]))
        g.add((self.sac, DCTERMS["identifier"], rdflib.Literal(self.code)))
        g.add((self.sac, JITIS["checkDigit"], rdflib.Literal(self.csum)))
        
        # 共通語彙基盤 住所IEP
        self.ic = JITI["LG-%s" % code_id]
        g.add((self.ic, RDF.type, IC["コード型"]))
        if self.code[2:] == "000":
            g.add((self.ic, IC["識別値"], rdflib.Literal(self.code[:2], datatype=rdflib.XSD.string)))
            g.add((self.sac, IC["都道府県コード"], self.ic))
        else:
            g.add((self.ic, IC["識別値"], rdflib.Literal(self.code[2:]+self.csum, datatype=rdflib.XSD.string)))
            g.add((self.sac, IC["市区町村コード"], self.ic))
            
            q = '''
            PREFIX dcterms: <http://purl.org/dc/terms/>
            SELECT ?s WHERE {
                ?s a sacs:StandardAreaCode ;
                   dcterms:identifier "%s000" ;
                   dcterms:issued ?d .
            }
            ORDER BY DESC(?d) LIMIT 1
            ''' % self.code[:2]
            for s, in estat.query(q):
                pid = get_code_id(s)
                g.add((self.sac, IC["都道府県コード"], JITI["LG-%s" % pid]))

    def set_name(self, name, kana):
        assert name != "同左"
        assert kana != "同左"
        g.add((self.ic, IC["表記"], rdflib.Literal(name, datatype=rdflib.XSD.string)))
        # e-Stat LOD 準拠
        g.add((self.sac, RDFS["label"], rdflib.Literal(name, lang="ja")))
        g.add((self.sac, RDFS["label"], rdflib.Literal(kana, lang="ja-Hira")))

q = '''
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX sacs: <http://data.e-stat.go.jp/lod/terms/sacs#>
SELECT ?s ?d WHERE {
  ?s a sacs:StandardAreaCode ;
     dcterms:identifier "%s" ;
     dcterms:issued ?d .
}
ORDER BY DESC(?d)
'''
code_ids = []

last_date = None

ev = None
cid = -1
for ri, r in t.sort_values(["date","cid"]).iterrows():
    last_date = r["date"]
    
    if cid != r["cid"]:
        dtstr = r["date"].strftime("%Y-%m-%d")
        ev = rdflib.BNode("_:ev%s-%02d" % (dtstr,cid))
        g.add((ev, RDF["type"], JITIS["CodeChangeEvent"]))
        g.add((ev, DCTERMS["issue"], rdflib.Literal(dtstr, datatype=rdflib.XSD.date)))
        cid = r["cid"]
    
    if not math.isnan(r["改正前コード"]):
        tc = get_code(r["改正前コード"])
        cids = [cid for c,cid in code_ids if c==tc]
        code_id = None
        if cids:
            code_id = cids[0]
        else:
            for s,d in estat.query(q % tc[:5]):
                if d.value < r["date"]:
                    code_id = get_code_id(s)
                    break
        assert code_id
        g.add((ev, JITIS["old"], JITI[code_id]))
        Code(code_id).set_name(r["改正前市区町村名"], r["改正前市区町村名ふりがな"])
    
    code = None
    code_id = None
    if r["改正後コード"]=="削除" or r["改正区分"] == "欠番":
        pass
    elif r["改正後コード"] == "同左":
        if math.isnan(r["改正前コード"]):
            raise Exception(r.to_csv())
        code = get_code(r["改正前コード"])
        code_id = "C%s-%s" % (code[:5], r["date"].strftime("%Y%m%d"))
    else:
        try:
            code = get_code(r["改正後コード"])
            code_id = "C%s-%s" % (code[:5], r["date"].strftime("%Y%m%d"))
        except:
            raise Exception(r.to_csv())
    
    if code and code_id:
        tq = "SELECT ?n WHERE { <%s> <%s> ?n . }"
        for n, in g.query(tq % (JITI[code_id], RDFS["label"])):
            g.remove((JITI[code_id], RDFS["label"], n))
        tq = "SELECT ?n WHERE { <%s> <%s> ?n . }"
        for n, in g.query(tq % (JITI["LG-"+code_id], IC["表記"])):
            g.remove((JITI["LG-"+code_id], IC["表記"], n))
        
        code_ids.append((code, code_id))
        g.add((ev, JITIS["new"], JITI[code_id]))
        
        name = r["改正後市区町村名"]
        if name.strip()=="同左":
            name = r["改正前市区町村名"]
        
        kana = r["改正後市区町村名ふりがな"]
        if isinstance(kana, float) or kana.strip()=="同左":
            kana = r["改正前市区町村名ふりがな"]
        
        Code(code_id).set_name(name, kana)


# コードセットの登録。

# In[11]:

dtstr = last_date.strftime("%Y-%m-%d")
cs = rdflib.BNode("_:cs%s" % dtstr)
g.add((cs, rdflib.RDF["type"], JITIS["CodeSet"]))
g.add((cs, DCTERMS["issue"], rdflib.Literal(dtstr, datatype=rdflib.XSD.date)))


# In[12]:

q = '''
PREFIX sacs: <%s>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?s WHERE {
  ?s a sacs:StandardAreaCode ;
     dcterms:identifier "%s" .
}
ORDER BY DESC(?s)
'''

x = pd.read_excel(clist)
for ri,r in x.iterrows():
    code = get_code(r["団体コード"])
    code_id = None
    for s, in g.query(q % (JITIS, code[:5])):
        code_id = get_code_id(s)
        break
    
    if code_id is None:
        for s, in estat.query(q % (SACS, code[:5])):
            code_id = get_code_id(s)
            break
        
        name = r["市区町村名\n（漢字）"]
        if isinstance(name, float) or not name.strip():
            name = r["都道府県名\n（漢字）"]

        kana = r["市区町村名\n（カナ）"]
        if isinstance(kana, float) or not kana.strip():
            kana = r["都道府県名\n（カナ）"]
        
        Code(code_id).set_name(name, jaconv.kata2hira(jaconv.h2z(kana)))
    
    assert code_id, code
    g.add((cs, DCTERMS["hasPart"], JITI[code_id]))


# In[13]:

list(g.query(q% (JITIS, "01206")))


# 過去履歴を逆向きに遡ってコードセットを登録してもよい。

# In[14]:

with open("code.ttl", "wb") as f:
    g.serialize(destination=f, format="turtle")

