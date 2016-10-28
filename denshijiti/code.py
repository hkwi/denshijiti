
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


# e-stat「標準地域コード」を取り込む。http://data.e-stat.go.jp/lodw/rdfschema/downloadfile/

# In[2]:

estat = rdflib.Graph()
estat.load("http://data.e-stat.go.jp/lodw/download/rdfschema/StandardAreaCode.ttl", format="turtle")


# 現在の excel を収集する。

# In[3]:

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

# In[4]:

x = pd.read_excel(clist_hist, skiprows=1, header=[0,1,2])
x.columns=[
    "a","b","c","都道府県名",
    "改正前コード","改正前市区町村名","改正前市区町村名ふりがな",
    "改正区分","改正年月日",
    "改正後コード","改正後市区町村名","改正後市区町村名ふりがな",
    "事由等"
]
x.index = range(len(x.index))


# In[5]:

asub = x["改正前市区町村名"].str.extract(r"^[\(（](.*)[\)）]$", expand=False)
bsub = x["改正後市区町村名"].str.extract(r"^[\(（](.*)[\)）]$", expand=False)
ks = ["都道府県名", "改正前コード", "改正区分", "改正年月日", "改正後コード"]
x2 = x[asub.isnull() & bsub.isnull() & x[ks].notnull().any(axis=1)].assign(asub=None, bsub=None)
for i,d in asub[asub.notnull()].iteritems():
    x2.loc[i-1, "asub"] = d
for i,d in asub[bsub.notnull()].iteritems():
    x2.loc[i-1, "bsub"] = d

x2.index = range(len(x2.index))


# In[6]:

for ri,r in x2.iterrows():
    for ci,c in r.iteritems():
        if c=="〃":
            x2.loc[ri, ci] = x2.loc[ri-1, ci]


# In[7]:

cids = []
cid = 0
t = x2.assign(u=lambda o: o["都道府県名"].notnull())
for ri, r in x2.iterrows():
    if r["都道府県名"] is not np.nan:
        cid += 1
    cids.append(cid)


# In[8]:

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


# In[9]:

g = rdflib.Graph()
SACS = rdflib.Namespace("http://data.e-stat.go.jp/lod/terms/sacs#")
JITI = rdflib.Namespace("http://hkwi.github.com/denshijiti/#")
JITIS = rdflib.Namespace("http://hkwi.github.com/denshijiti/terms#")
g.bind("jiti", JITI)
g.bind("jitis", JITIS)
g.bind("dcterms", rdflib.namespace.DCTERMS)

def get_code(code_like):
    return "%06d" % int(code_like)

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
        g.add((ev, rdflib.RDF["type"], JITIS["CodeChangeEvent"]))
        g.add((ev, rdflib.namespace.DCTERMS["issue"], rdflib.Literal(dtstr, datatype=rdflib.XSD.date)))
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
                    code_id = os.path.basename(urllib.parse.urlparse(s).path)
                    break
        assert code_id
        g.add((ev, JITIS["old"], JITI[code_id]))
        g.add((JITI[code_id], rdflib.RDF["type"], JITIS["StandardAreaCode"]))
        g.add((JITI[code_id], rdflib.namespace.DCTERMS["identifier"], rdflib.Literal(tc[:5])))
        g.add((JITI[code_id], rdflib.namespace.RDFS["label"], rdflib.Literal(r["改正前市区町村名"])))
        g.add((JITI[code_id], JITIS["kana"], rdflib.Literal(r["改正前市区町村名ふりがな"])))
    
    code = None
    code_id = None
    if r["改正後コード"]=="削除" or r["改正区分"] == "欠番":
        pass
    elif r["改正後コード"] == "同左":
        if r["改正前コード"] is np.nan:
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
        code_ids.append((code, code_id))
        g.add((ev, JITIS["new"], JITI[code_id]))
        g.add((JITI[code_id], rdflib.RDF["type"], JITIS["StandardAreaCode"]))
        g.add((JITI[code_id], rdflib.namespace.DCTERMS["identifier"], rdflib.Literal(code[:5])))
        if r["改正後市区町村名"]=="同左":
            g.add((JITI[code_id], rdflib.namespace.RDFS["label"], rdflib.Literal(r["改正前市区町村名"])))
        else:
            g.add((JITI[code_id], rdflib.namespace.RDFS["label"], rdflib.Literal(r["改正後市区町村名"])))
        
        if r["改正後市区町村名ふりがな"]=="同左":
            g.add((JITI[code_id], JITIS["kana"], rdflib.Literal(r["改正前市区町村名ふりがな"])))
        else:
            g.add((JITI[code_id], JITIS["kana"], rdflib.Literal(r["改正後市区町村名ふりがな"])))


# コードセットの登録。

# In[10]:

dtstr = last_date.strftime("%Y-%m-%d")
cs = rdflib.BNode("_:cs%s" % dtstr)
g.add((cs, rdflib.RDF["type"], JITIS["CodeSet"]))
g.add((cs, rdflib.namespace.DCTERMS["issue"], rdflib.Literal(dtstr, datatype=rdflib.XSD.date)))


# In[11]:

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
for c in x["団体コード"].apply(get_code):
    code_id = None
    for s, in g.query(q % (JITIS, c[:5])):
        code_id = s
        break
    if code_id is None:
        for s, in estat.query(q % (SACS, c[:5])):
            code_id = JITI[os.path.basename(urllib.parse.urlparse(s).path)]
            break
    g.add((cs, rdflib.namespace.DCTERMS["hasPart"], code_id))


# 過去履歴を逆向きに遡ってコードセットを登録してもよい。

# In[12]:

with open("code.ttl", "wb") as f:
    g.serialize(destination=f, format="turtle")


# In[ ]:



