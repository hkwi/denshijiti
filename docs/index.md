---
# You don't need to edit this file, it's empty on purpose.
# Edit theme's home layout instead if you wanna make some changes
# See: https://jekyllrb.com/docs/themes/#overriding-theme-defaults
layout: home
---

コード一覧はTurtleフォーマットで[ダウンロード](code.ttl)できます。

自治体コードは組織改編などで意味が変わるため、それぞれ別のエンティティが割り当てられています。
実際のコードは[スキーマ](terms)の`code`から取得します。

Codes:
<ul id="codes"></ul>

Code sets:
<ul id="cs"></ul>

<script src="https://cdnjs.cloudflare.com/ajax/libs/axios/0.16.1/axios.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/4.8.0/d3.min.js"></script>
<script src="n3-browser.min.js"></script>
<script>
function jiti(ns){
	var prefix="http://hkwi.github.com/denshijiti/#";
	if(ns.substring(0, prefix.length) == prefix){
		return ns.substr(prefix.length);
	}
}
axios({url:"code.ttl",responseType:"text"}).then(function(resp){
	var cs = {};
	var codes = {};
	o = N3.Parser().parse(resp.data);
	o.forEach(function(tp){
		var name = jiti(tp.subject);
		if(name){
			if(name.substr(0,3)=="CS-"){
				cs[name] = 1;
			} else {
				codes[name] = 1;
			}
		}
	});
	var lgs1 = d3.select("#codes");
	Object.keys(codes).forEach(function(c){
		lgs1.append("li").attr("id", c).text(c);
	});
	var lgs2 = d3.select("#cs");
	Object.keys(cs).forEach(function(c){
		lgs2.append("li").attr("id", c).text(c);
	});
});
</script>
