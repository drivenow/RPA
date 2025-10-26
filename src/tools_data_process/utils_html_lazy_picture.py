test_lazy_html = """'\n\n\n\n\n\n\n\n\n\n<div>\n<div>\n<div>\n<div>\n<img alt="cover_image"
class="wx_follow_avatar_pic"
src="https://mmbiz.qpic.cn/sz_mmbiz_jpg/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoB2hykr6Wf
12yaIWmN4xZrMIpzYDRib97TJsV3JngbALouQbn92ibdiad0A/0?wx_fmt=jpeg"/>\n</div>\n</di
v>\n<div>\n<div>\n<div>\n<h1>\n买卖压力度量，复权调整成交量之后，效果居然能有提升！</h1>\n<div>\n<span>原创<
/span>\n<span>\n                   量化拯救散户\n                 </span>\n<span>\n<a
href="javascript:void(0);">\n        量化拯救散户
</a>\n</span>\n<span>\n<em>2025年10月25日
14:25</em>\n<em><span>上海</span></em>\n</span>\n</div>\n<div><section><section><s
ection><section><section><img _width="100%" class="rich_pages wxw-img
js_img_placeholder wx_img_placeholder" data-imgfileid="100007369" data-index="1"
data-original-style="vertical-align: middle;max-width: 100%;width: 100%;box-
sizing: border-box;height: auto !important;" data-ratio="0.8034188034188035"
data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_gif/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBBBDFMLxA
eg23Lh8Gs2kd42CxrUutIL75E5oZk8icfvs122OJ8g4wickQ/640?wx_fmt=png&amp;from=appmsg"
data-type="gif" data-w="351" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="vertical-align:
middle; max-width: 100%; box-sizing: border-box; width: 110px !important;
height: 88.3761px !important; visibility: visible;"
width="1"/></section></section></section></section><section><p><span><img
_width="677px" class="rich_pages wxw-img js_img_placeholder wx_img_placeholder"
data-imgfileid="100007391" data-index="2" data-original-style="height: auto
!important;" data-ratio="0.562962962962963" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_jpg/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBdVk3zYp1
xXibYTM01vuI5MicMurLDXFY93l7kSSxEwuZz1vYboiaK6HgQ/640?wx_fmt=jpeg&amp;from=appms
g" data-type="jpeg" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 637px
!important; height: 358.607px !important; visibility: visible;"
width="1"/></span><span>本文，笔者将复现东方证券朱剑涛老师2019年10月29日发布的研报《</span><span>因子选股系列研究之
六十：基于量价关系度量股票的买卖压力</span><span>》。</span></p><p><span>2019年的时候，因子选股系列已经发布了60篇了，这含
金量无需多言。</span></p><p><span>研报中，认为市场上存在两类投资者，A类着眼于中长期，B类看中短期。所以，B类投资者的交易是噪声交易。</s
pan></p><p><span>通过对A类投资者的分析，这类投资者买入的时候，标的在价格低位的成交量大于价格高位；卖出的时候，标的在价格高位的成交量大于价格低
位。</span></p><p><span>基于这样的一个思路，就有了这个叫做<span>买卖压力度量</span>的因子。</span></p></secti
on><section><section><section><section><section><section><p><strong><span>计算步骤及代
码</span></strong></p></section></section></section></section></section></section
><section><section><section><p><span>这个因子的计算步骤不是很复杂，用一个公式就能表达。</span></p></secti
on><section><section><section><section><section><p><strong><span>1</span></stron
g></p></section></section><section><section><p><strong><span>计算公式</span></strong
></p></section></section></section></section></section><section><section><sectio
n><section><section><section><img _width="677px" class="rich_pages wxw-img
js_img_placeholder wx_img_placeholder" data-imgfileid="100007379" data-index="3"
data-original-style="height: auto !important;" data-ratio="0.24615384615384617"
data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoB8YvwH9pO
pLiaIvo7Mvakok6Qv3cwQLBe7twR2lr4bCfswk9r5RV79ag/640?wx_fmt=png&amp;from=appmsg"
data-type="png" data-w="780" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 524px
!important; height: 128.985px !important;" type="block"
width="1"/></section><p><span>vwap很好理解，就是成交量加权平均价格。</span></p><p><span>volu就是vol
ume，成交量。</span></p><p><span>此外，在研报中还隐藏了一个细节，那就是vwap和volu都是经过复权调整的。</span></p><p>
<span>说实话，笔者不是很理解这一句话，主要是成交量是如何经过复权调整的。</span></p><p><span>实在想不明白，笔者就简单粗暴，直接将成交量
乘上了复权因子。</span></p></section></section></section></section></section><section><s
ection><section><section><section><p><b><span>2</span></b></p></section></sectio
n><section><section><p><strong><span>计算代码</span></strong></p></section></section
></section></section></section><section><section><section><section><section><sec
tion><pre><code><span>def __call__(self):</span></code><code><span>\xa0 \xa0
data =
BaseDataLoader.<span>load_data</span>(<span>\'../../data/stock_bar_1day.parquet\
'</span>,</span></code><code><span>\xa0 \xa0 \xa0 \xa0 \xa0 \xa0 \xa0 \xa0 \xa0
\xa0 \xa0 \xa0 \xa0 \xa0 \xa0 \xa0 \xa0 \xa0 \xa0 \xa0
\xa0fields=[<span>\'vwap\'</span>,\xa0<span>\'volume\'</span>,\xa0<span>\'factor
\'</span>]).<span>to_dataframes</span>()</span></code><code><span>\xa0 \xa0
self.vwap = data[<span>\'vwap\'</span>] *
data[<span>\'factor\'</span>]</span></code><code><span>\xa0 \xa0 self.vol =
data[<span>\'volume\'</span>] *
data[<span>\'factor\'</span>]</span></code><code><span>\xa0 \xa0 res =
[]</span></code><code><span>\xa0 \xa0 for i
in\xa0<span>tqdm</span>(<span>range</span>(<span>21</span>,\xa0<span>len</span>(
self.vwap)+<span>1</span>)):</span></code><code><span>\xa0 \xa0 \xa0 \xa0
res.<span>append</span>(self.<span>cal_factor</span>(i))</span></code><code><spa
n>\xa0 \xa0 res = pd.<span>concat</span>(res,
axis=<span>1</span>).T</span></code><code><span>\xa0 \xa0 res.index.name
=\xa0<span>\'datetime\'</span></span></code><code><span>\xa0 \xa0
res.<span>reset_index</span>(inplace=True)</span></code><code><span>\xa0 \xa0
res = pd.<span>melt</span>(res, id_vars=<span>\'datetime\'</span>,
var_name=<span>\'code\'</span>,
value_name=<span>\'reverse_prob\'</span>)</span></code><code><span>\xa0 \xa0
res.<span>to_parquet</span>(<span>\'./reverse_prob.parquet\'</span>)</span></cod
e></pre></section><p><span>第一段代码，主要就是读取数据。主要是第4行和第5行，需要说明一下，这两行的作用就是对vwap和volu进行
复权调整。</span></p><section><pre><code><span><span>def</span>\xa0<span>cal_factor</
span>(<span><span>self</span></span><span>,
idx</span>):</span></code><code><span>\xa0 \xa0 vwap
=\xa0<span>self</span>.vwap.iloc[idx-
<span>21</span><span>:idx</span>]</span></code><code><span>\xa0 \xa0 day =
vwap.iloc[[-
<span>1</span>]].index.tolist()[<span>0</span>]</span></code><code><span>\xa0
\xa0 vol =\xa0<span>self</span>.vol.iloc[idx-
<span>21</span><span>:idx</span>]</span></code><code><span>\xa0 \xa0 vol =
vol.div(vol.mean(), axis=<span>1</span>)</span></code><code><span>\xa0 \xa0 res
= np.log(vwap.mean() / (vwap * vol).sum())</span></code><code><span>\xa0 \xa0
res.name = day</span></code><code><span>\xa0
\xa0\xa0<span>return</span>\xa0res</span></code></pre></section><p><span>第二段代码，就
是按照公式计算每21个交易日的因子值。</span></p></section></section></section></section></section>
<section><section><section><img _width="100%" class="rich_pages wxw-img
js_img_placeholder wx_img_placeholder" data-imgfileid="100007371" data-index="4"
data-original-style="vertical-align: middle;max-width: 100%;width: 100%;box-
sizing: border-box;height: auto !important;" data-ratio="0.9203703703703704"
data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBzxKibSos
aw9MmOH3F8aOfySIs1llHN9KgTlq1ERVPHaDqW9xjHWz31g/640?wx_fmt=png&amp;from=appmsg"
data-type="png" data-w="1080" src="data:image/svg+xml,%3C%3Fxml version=\'1.0\'
encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\' viewBox=\'0 0 1 1\'
version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="vertical-align:
middle; max-width: 100%; box-sizing: border-box; width: 53px !important; height:
48.7796px
!important;"/></section></section></section></section></section><section><sectio
n><section><section><section><section><p><strong><span>因子评价</span></strong></p><
/section></section></section></section></section></section><section><section><se
ction><p><span>由于这个因子在计算的时候已经使用了过去21个交易日的量价数据了，所以它本身就可以看作是一个月度因子了，无需在对过去21个交易日的因
子值取均值或者标准差了。</span></p><p><span>值得一提的是，笔者在复现的时候也尝试过，对vwap进行复权，而不对volu进行复权，得到的因子表
现不如都复权处理的。所以，下面的因子评价结果展示的是对vwap和volu都复权处理计算的因子。</span></p></section><section><se
ction><section><section><section><section><section><section><section><section><p
><strong><span>01</span></strong></p></section></section></section></section></s
ection></section></section><section><section><p><strong><span>IC分析</span></stron
g></p></section></section></section></section></section><section><section><secti
on><section><section><section><section><section><img _width="677px"
class="rich_pages wxw-img js_insertlocalimg js_img_placeholder
wx_img_placeholder" data-imgfileid="100007380" data-index="5" data-original-
style="height: auto !important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBPQKqN9x2
PYjeDN3Jicj9oOnayGHOgPnByg0gfCP2nHxUjz8r9cqpPKg/640?wx_fmt=png&amp;from=appmsg"
data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section><section><img _width="677px" class="rich_pages wxw-img
js_insertlocalimg js_img_placeholder wx_img_placeholder" data-
imgfileid="100007383" data-index="6" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoB63qwR6wP
XIUbTSpAKGibjfl8uJpLVT2YTTrkwYtWW7Ltl3AwkqKKtxA/640?wx_fmt=png&amp;from=appmsg"
data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section><section><img _width="677px" class="rich_pages wxw-img
js_insertlocalimg js_img_placeholder wx_img_placeholder" data-
imgfileid="100007384" data-index="7" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBHqo7MMCD
icByhxIf66loRCh3WyPDuepK3RkJeJChoTiaveRUCElWaic3A/640?wx_fmt=png&amp;from=appmsg
" data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section><section><img _width="677px" class="rich_pages wxw-img
js_insertlocalimg js_img_placeholder wx_img_placeholder" data-
imgfileid="100007382" data-index="8" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBibOYXMJd
vHselZmTLibRjENwpZicKKvA69PdPpdGNTmmD9FCRrCuQIJqQ/640?wx_fmt=png&amp;from=appmsg
" data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section><section><img _width="677px" class="rich_pages wxw-img
js_insertlocalimg js_img_placeholder wx_img_placeholder" data-
imgfileid="100007381" data-index="9" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBdDnfoGyZ
o5sWq8r4HbPx68PveewIT75TwrtLPsbj1fdE64n2drBzEg/640?wx_fmt=png&amp;from=appmsg"
data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section><section><img _width="677px" class="rich_pages wxw-img
js_insertlocalimg js_img_placeholder wx_img_placeholder" data-
imgfileid="100007385" data-index="10" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBdJ1NCzTr
xyaX5nocLaMRialye305FrI0NKZmKib1wwpXBqVZeA5QIxKQ/640?wx_fmt=png&amp;from=appmsg"
data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section><p><span>从IC上来看，这个因子的表现中规中矩，IC绝对值不算高也不能说低。</span></p></sect
ion></section></section></section></section></section></section><section><sectio
n><section><section><section><section><section><section><section><section><p><st
rong><span>02</span></strong></p></section></section></section></section></secti
on></section></section><section><section><p><strong><span>回归分析</span></strong></
p></section></section></section></section></section><section><section><section><
section><section><section><section><section><img _width="677px"
class="rich_pages wxw-img js_insertlocalimg js_img_placeholder
wx_img_placeholder" data-imgfileid="100007386" data-index="11" data-original-
style="height: auto !important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBbjd2SaJ9
iaerl4x6ntFHcj7gXxicqGeQBD25RiaXUD7qaljVEFu2AOCug/640?wx_fmt=png&amp;from=appmsg
" data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section><section><img _width="677px" class="rich_pages wxw-img
js_insertlocalimg js_img_placeholder wx_img_placeholder" data-
imgfileid="100007387" data-index="12" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBK5icbYEc
2vZdqpkDIL2GSBGzBcsfHQ37y6omiaAOgIpCGyIAxCYx2LiaQ/640?wx_fmt=png&amp;from=appmsg
" data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section></section></section></section></section></section></section
></section><section><section><section><section><section><section><section><secti
on><section><section><p><strong><span>03</span></strong></p></section></section>
</section></section></section></section></section><section><section><p><strong><
span>换手率分析</span></strong></p></section></section></section></section></section>
<section><section><section><section><section><section><section><section><img
_width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder
wx_img_placeholder" data-imgfileid="100007389" data-index="13" data-original-
style="height: auto !important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBhfPLicjT
zq7E4B65cZlxTADE5NuTNN5Am9o08odt06dSkZB2VUsvLbw/640?wx_fmt=png&amp;from=appmsg"
data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section><section><img _width="677px" class="rich_pages wxw-img
js_insertlocalimg js_img_placeholder wx_img_placeholder" data-
imgfileid="100007390" data-index="14" data-original-style="height: auto
!important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBib3CU6ql
dWxS1zBw6RBmeQX1TiaJSEyqKiajAKe66cPR97PPa7zqfuu7Q/640?wx_fmt=png&amp;from=appmsg
" data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section></section></section></section></section></section></section
></section><section><section><section><section><section><section><section><secti
on><section><section><p><strong><span>04</span></strong></p></section></section>
</section></section></section></section></section><section><section><p><strong><
span>鼓励创新原则</span></strong></p></section></section></section></section></section
><section><section><section><section><section><section><section><section><img
_width="677px" class="rich_pages wxw-img js_insertlocalimg js_img_placeholder
wx_img_placeholder" data-imgfileid="100007388" data-index="15" data-original-
style="height: auto !important;" data-ratio="0.75" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBKyezUlia
libBzOktNEJCktc3H48taumX0OibjVZOm0lOsjjzia0vrcMJCQ/640?wx_fmt=png&amp;from=appms
g" data-type="png" data-w="1080" height="1" src="data:image/svg+xml,%3C%3Fxml
version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\'
viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="width: 531px
!important; height: 398.25px !important;" type="block"
width="1"/></section><p><span>但是，分层回测上的表现注定了这个因子恐怕很难被使用。</span></p><p><span>因为，其
分层回测的单调性可以说是一塌糊涂，因子值最小的一组和因子值最大的一组的收益率小于其他三组。</span></p><p><span>如果在考虑交易成本的话，无论是
因子值最大的一组还是因子值最小的一组，其在2018年到2024年间的收益率都将是小于0的。</span></p></section></section></se
ction></section></section></section></section><section><section><section><img
_width="100%" class="rich_pages wxw-img js_img_placeholder wx_img_placeholder"
data-imgfileid="100007372" data-index="16" data-original-style="vertical-align:
middle;max-width: 100%;width: 100%;box-sizing: border-box;height: auto
!important;" data-ratio="0.9203703703703704" data-s="300,640" data-
src="https://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBzxKibSos
aw9MmOH3F8aOfySIs1llHN9KgTlq1ERVPHaDqW9xjHWz31g/640?wx_fmt=png&amp;from=appmsg"
data-type="png" data-w="1080" src="data:image/svg+xml,%3C%3Fxml version=\'1.0\'
encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\' viewBox=\'0 0 1 1\'
version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\'
xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg
stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-
opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\'
fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\'
height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="vertical-align:
middle; max-width: 100%; box-sizing: border-box; width: 53px !important; height:
48.7796px
!important;"/></section></section></section></section></section><section><p><str
ong><span><span>-\xa0</span><span><em><span>END</span></em></span><span>\xa0-
</span></span></strong></p></section><section><section><section><img
_width="100%" class="rich_pages wxw-img js_img_placeholder wx_img_placeholder"
data-imgfileid="100007376" data-index="17" data-original-style="vertical-align: middle;max-width: 100%;width: 100%;box-sizing: border-box;height: auto !important;" data-ratio="0.8034188034188035" data-s="300,640" data-src="https://mmbiz.qpic.cn/sz_mmbiz_gif/MA6hRUd7yGtVTYQ2MJAr02hvUvQOdGoBBBDFMLxAeg23Lh8Gs2kd42CxrUutIL75E5oZk8icfvs122OJ8g4wickQ/640?wx_fmt=png&amp;from=appmsg" data-type="gif" data-w="351" height="1" src="data:image/svg+xml,%3C%3Fxml version=\'1.0\' encoding=\'UTF-8\'%3F%3E%3Csvg width=\'1px\' height=\'1px\' viewBox=\'0 0 1 1\' version=\'1.1\' xmlns=\'http://www.w3.org/2000/svg\' xmlns:xlink=\'http://www.w3.org/1999/xlink\'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke=\'none\' stroke-width=\'1\' fill=\'none\' fill-rule=\'evenodd\' fill-opacity=\'0\'%3E%3Cg transform=\'translate(-249.000000, -126.000000)\' fill=\'%23FFFFFF\'%3E%3Crect x=\'249\' y=\'126\' width=\'1\' height=\'1\'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E" style="vertical-align: middle; max-width: 100%; box-sizing: border-box; width: 110px !important; height: 88.3761px !important;" width="1"/></section></section></section></section></div>\n</div>\n<div>预览时标签不可点</div>\n\n</div>\n</div>\n\n<div>\n<div>\n<div>\n<p>微信扫一扫关注该公众号</p>\n</div>\n</div>\n</div>\n</div>\n<div>\n<div>\n<span>继续滑动看下一个</span>\n</div>\n</div>\n</div>\n<div>\n<div>\n<div>\n<button>轻触阅读原文</button>\n</div>\n<div>\n<div>\n<div>\n<div>\n<div>\n<div>\n<div>\n<div>\n<span>\n<img alt="" class="wx_follow_avatar_pic" src="http://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGsObOvNt30RgVh2Tsxrx3jqaba7mP6jPoo0ASk2qXCCE8Zb7pqaDM1kO2utfN19R9jrquiavyETaAw/0?wx_fmt=png"/>\n</span>\n</div>\n<div>\n<div>\n<div>\n            量化拯救散户           </div>\n</div>\n</div>\n</div>\n</div>\n</div>\n</div>\n</div>\n</div>\n</div>\n</div>\n<div>\n<div>\n<div>\n<span>向上滑动看下一个</span>\n</div>\n</div>\n</div>\n</div>\n\n\n<div>\n<div>\n<div>\n<a href="javascript:;">知道了</a>\n</div>\n</div>\n</div>\n\n<div>\n<div>\n<div>\n     微信扫一扫使用小程序\n</div>\n</div>\n</div>\n<div>\n<div>\n\n<div>\n<a href="javascript:void(0);">取消</a>\n<a href="javascript:void(0);">允许</a>\n</div>\n</div>\n</div>\n<div>\n<div>\n\n<div>\n<a href="javascript:void(0);">取消</a>\n<a href="javascript:void(0);">允许</a>\n</div>\n</div>\n</div>\n<div>\n<div>\n\n<div>\n<a href="javascript:void(0);">取消</a>\n<a href="javascript:void(0);">允许</a>\n</div>\n</div>\n</div>\n<div>\n<button>×</button>\n<button>分析</button>\n</div>\n<div>\n<div>\n<div>\n<div>\n<div>\n<img alt="作者头像" class="jump_author_avatar" src="http://mmbiz.qpic.cn/sz_mmbiz_png/MA6hRUd7yGsObOvNt30RgVh2Tsxrx3jqaba7mP6jPoo0ASk2qXCCE8Zb7pqaDM1kO2utfN19R9jrquiavyETaAw/0?wx_fmt=png"/>\n</div>\n</div>\n</div>\n<div>\n<p>微信扫一扫可打开此内容，使用完整服务</p>\n</div>\n</div>\n</div>\n\n<span>：</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>，</span>\n<span>。</span>\n<span>视频</span>\n<span>小程序</span>\n<span>赞</span>\n<span>，轻点两下取消赞</span>\n<span>在看</span>\n<span>，轻点两下取消在看</span>\n<span>分享</span>\n<span>留言</span>\n<span>收藏</span>\n<span>听过</span>\n\n\n\n\n\n\n\n'
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

LAZY_ATTRS = [
    "data-src", "data-original", "data-lazy-src",
    "data-actualsrc", "data-url", "data-origin", "data-ks-lazyload",
]
LAZY_SRCSETS = ["data-srcset", "data-lazy-srcset"]

def is_placeholder(u: str) -> bool:
    if not u:
        return True
    u = u.strip().lower()
    # 微信/懒加载常见占位：data:、1x1 svg、about:blank 等
    return (
        u.startswith("data:") or
        u.startswith("about:") or
        "svg+xml" in u or               # 你截图里的就是这个
        "placeholder" in u or
        "pixel" in u
    )

def norm_url(u: str) -> str:
    if not u:
        return u
    if u.startswith("//"):  # 协议相对
        u = "https:" + u
    # 去掉常见懒加载/转码参数（可按需增减）
    try:
        p = urlparse(u)
        q = [(k, v) for k, v in parse_qsl(p.query) if k not in {"wx_lazy", "tp", "wxfrom"}]
        return urlunparse(p._replace(query="&".join([f"{k}={v}" for k,v in q])))
    except Exception:
        return u

def pick_from_srcset(srcset: str) -> str:
    items = [x.strip() for x in (srcset or "").split(",") if x.strip()]
    if not items: return ""
    # 取最后一项（通常是最大宽度）
    return items[-1].split()[0]

def normalize_lazy_images(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")  # 用 lxml 更稳

    for img in soup.find_all("img"):
        cur_src = (img.get("src") or "").strip()

        # 1) 先把 data-srcset / data-lazy-srcset 迁移到 srcset
        for a in LAZY_SRCSETS:
            if img.has_attr(a) and img.get(a):
                img["srcset"] = img[a]
                del img[a]

        # 2) 如果当前 src 是占位，尝试从 data-* 属性取真实地址
        new_src = ""
        if is_placeholder(cur_src):
            # 2.1 data-* 候选
            for a in LAZY_ATTRS:
                if img.has_attr(a) and img.get(a):
                    new_src = img.get(a).strip()
                    break
            # 2.2 如果还没有，且有 srcset，从 srcset 里挑一条
            if not new_src and img.get("srcset"):
                new_src = pick_from_srcset(img["srcset"])

        # 3) 如果拿到了新地址就写回；否则保留原 src
        if new_src:
            img["src"] = norm_url(new_src)
        elif cur_src:  # 也做一下规范化
            img["src"] = norm_url(cur_src)

        # 可选：去掉微信特有占位属性，避免后续再被脚本复原
        # for a in LAZY_ATTRS: 
        #     if img.has_attr(a): del img[a]

    # <source> 里也可能有 data-srcset
    for s in soup.find_all("source"):
        for a in LAZY_SRCSETS:
            if s.has_attr(a) and s.get(a):
                s["srcset"] = s[a]; del s[a]
        if s.get("srcset"):
            # 规范化 srcset 的各个 URL
            items = []
            for item in s["srcset"].split(","):
                bits = item.strip().split()
                if not bits: continue
                bits[0] = norm_url(bits[0])
                items.append(" ".join(bits))
            s["srcset"] = ", ".join(items)

    return str(soup)

def fix_strikethrough_html(html: str) -> str:
    # 可选的正则预清理：把 “<s ection” 还原成 "<section"
    html = re.sub(r"<\s*s\s+ection", "<section", html, flags=re.I)
    html = re.sub(r"</\s*s\s*>", "", html, flags=re.I)  # 清掉误关闭的 </s>

    # 用 html5lib 增强容错，自动补全闭合
    soup = BeautifulSoup(html, "lxml")

    # 1) 去掉会导致删除线的标签（只保留其文本/子节点）
    for tag in soup.find_all(["s", "strike", "del"]):
        tag.unwrap()

    # 2) 去掉内联样式里的 line-through
    for el in soup.select('[style*="line-through"]'):
        style = el.get("style", "")
        style = re.sub(r"text-decoration\s*:\s*line-through;?\s*", "", style, flags=re.I)
        # 清理多余分号/空白
        style = re.sub(r";\s*;", ";", style).strip().strip(";")
        if style:
            el["style"] = style
        else:
            el.attrs.pop("style", None)

    # 3) 兜底：在 <head> 注入覆盖样式（防止遗漏）
    override = soup.new_tag("style")
    override.string = """
    s, strike, del { text-decoration: none !important; }
    [style*="line-through"] { text-decoration: none !important; }
    """
    if soup.head:
        soup.head.append(override)
    else:
        soup.insert(0, override)

    return str(soup)

if __name__=="__main__":
   norm_html = normalize_lazy_images(html=test_lazy_html)
   norm_html = fix_strikethrough_html(html = norm_html)
   with open("C:/Users/fullmetal/Desktop/1.html", "w", encoding="utf-8") as f:
       f.writelines(norm_html)