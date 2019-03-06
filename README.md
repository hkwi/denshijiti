総務省「全国地方公共団体コード」を RDF 化します。[ウェブサイト](http://www.soumu.go.jp/denshijiti/code.html)と[カタログサイト](http://www.data.go.jp/data/dataset/soumu_20140909_0395)に掲載のあるデータを使っています。

自動ビルドしていて、[最新版](https://hkwi.github.io/denshijiti/code.ttl)がダウンロードできます。

またビルドにあたっては、[e-stat 統計 LOD](http://data.e-stat.go.jp/lodw/data/) のデータを活用しています。

[![Build Status](https://travis-ci.org/hkwi/denshijiti.svg?branch=master)](https://travis-ci.org/hkwi/denshijiti)


注：「全国地方公共団体コード」だけでは一般的に使われる住所を組み立てることはできません。例えば `473481` 沖縄県与那原町は一般的には「沖縄県島尻郡与那原町」ですが、`jitis:group` である `473405` 島尻郡は「全国地方公共団体コード」には登録されていません。代わりに「[統計に用いる地域標準コード](http://data.e-stat.go.jp/lodw/provdata/lodRegion)」などが使えます。

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

# Code Snippet

コードの検査数字（チェックサム）は次のコードで計算できる（JIS X 0401）。

```
lambda code: str(11-sum([int(a)*b for a,b in zip(code, range(6,1,-1))])%11)[-1]
```

# 5桁？ 6桁？
次のような背景があるそうだ。
- 歴史ある業務システムでは 5 桁で運用されているものが多く、自治体職員のかたもこの数字に目が慣れているという実態がある。
- check digit は長い桁数に対して効果を発揮するので、5 桁程度では効果が薄いという見解もある。もちろんデータの重要度による。
- もともとパンチ入力ミスを検出するために導入されたらしい。
- 現在でもデータ入力の業務は存在するので、できれば 6 桁が良いという意見もある。

このプロジェクトでは 6 桁を使用している。

# License
プログラムは Apache 2.0 ライセンス、データは CC-BY ライセンスにします。
