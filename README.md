総務省「全国地方公共団体コード」を RDF 化します。

自動ビルドしていて、[最新版](https://hkwi.github.io/denshijiti/code.ttl)がダウンロードできます。

[![Build Status](https://travis-ci.org/hkwi/denshijiti.svg?branch=master)](https://travis-ci.org/hkwi/denshijiti)


注：「全国地方公共団体コード」だけでは一般的に使われる住所を組み立てることはできません。例えば `473481` 沖縄県与那原町は一般的には「沖縄県島尻郡与那原町」ですが、`jitis:group` である `473405` 島尻郡は「全国地方公共団体コード」には登録されていません。代わりに「統計に用いる地域標準コード」などが使えます。

# 例

```
import rdflib
g = rdflib.Graph()
g.load("https://hkwi.github.io/denshijiti/code.ttl", format="turtle")
for c,n in g.query('''
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX jitis: <http://hkwi.github.com/denshijiti/terms#>

SELECT ?c ?n WHERE {
	?s a jitis:StandardAreaCode ;
		rdfs:label ?n ;
		jitis:code ?c .
	?cs a jitis:CodeSet ;
		dcterms:issued "2016-10-10"^^xsd:date ;
		dcterms:hasPart ?s .
	FILTER (LANG(?n) = "ja")
}
ORDER BY ASC(?c)
'''):
	print(c,n)
```
