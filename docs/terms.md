RDF で使われる語彙は次のようになっている。

```
PREFIX jitis: <http://hkwi.github.com/denshijiti/terms#>
```

# CodeSet

ある時点でのコード一覧を示す `rdfs:Class` です。

次のプロパティを持ちます。

- `dcterms:issued` : 改定日
- `dcterms:hasPart` : `jitis:StandardAreaCode`

`dcterms:issued` で最新のものを取得すると、
現在の一覧が得られます。

# StandardAreaCode

e-stat「標準地域コード」での定義と同様の、コードを示す `rdfs:Class` です。
`ic:住所` のサブクラスになっています。

次のプロパティを持ちます。

- `rdfs:label`
- `jitis:code`
- `ic:市区町村` optional
- `ic:市区町村コード` optional
- `ic:都道府県`
- `ic:都道府県コード`
- `dcterms:identifier`
- `dcterms:issued`
- `skos:closeMatch`
- `jitis:type` optional コードによって与えられる意味を示します。
- `jitis:group` optional 統計などで所属するグループを示します。

# CodeChangeEvent

変更履歴の変更単位一つを示す `rdfs:Class` です。

次のプロパティを持ちます。

- `jitis:new` 改正後の `jitis:StandardAreaCode`
- `jitis:old` 改正前の `jitis:StandardAreaCode`
- `dcterms:issued` 改正日

# 都道府県

- `jitis:type` で指示される、コードの意味です。

# 指定都市

- `jitis:type` で指示される、コードの意味です。

# 特別区

- `jitis:type` で指示される、コードの意味です。

# 指定都市の区

- `jitis:type` で指示される、コードの意味です。

# 市

- `jitis:type` で指示される、コードの意味です。

# code

6 桁数字のコードを指すプロパティ名。

## new

改正後の `StandardAreaCode` を指すプロパティ名

## old

改正前の `StandardAreaCode` を指すプロパティ名
